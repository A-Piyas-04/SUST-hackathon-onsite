"""Offline training for learned confidence calibration (Feature 1).

Pulls labeled examples from PostgreSQL (or CSV exports), optionally augments with
synthetic ground-truth rows, fits logistic regression, and writes the artifact
used at runtime by ``app.services.quality.calibration``.

Human review labels and synthetic ground-truth labels are reported separately.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from app.contracts.v1.enums import FeedHealthStatus
from app.services.analytics import config as cfg
from app.services.quality.calibration import (
    FEATURE_NAMES,
    ConfidenceCalibrationModel,
    build_feature_vector,
    utc_now_iso,
)

HUMAN_REVIEW_SQL = """
SELECT DISTINCT ON (cr.case_review_id)
    cr.was_false_positive,
    dqa.status,
    dqa.sample_count,
    dqa.latest_source_at,
    dqa.assessed_at,
    COALESCE(
        (
            SELECT (dqi.evidence->>'rejected_event_count')::float
            FROM data_quality_issues dqi
            WHERE dqi.data_quality_assessment_id = dqa.data_quality_assessment_id
              AND dqi.issue_type = 'malformed_payload'
            LIMIT 1
        ),
        0.0
    ) AS rejected_event_count
FROM case_reviews cr
JOIN cases c ON c.case_id = cr.case_id
LEFT JOIN alert_quality_assessments aqa ON aqa.alert_id = c.alert_id
LEFT JOIN alert_liquidity_projections alp ON alp.alert_id = c.alert_id
LEFT JOIN liquidity_projections lp ON lp.liquidity_projection_id = alp.liquidity_projection_id
LEFT JOIN alert_anomaly_flags aaf ON aaf.alert_id = c.alert_id
LEFT JOIN anomaly_flags af ON af.anomaly_flag_id = aaf.anomaly_flag_id
JOIN data_quality_assessments dqa ON dqa.data_quality_assessment_id = COALESCE(
    aqa.data_quality_assessment_id,
    lp.primary_data_quality_assessment_id,
    af.data_quality_assessment_id
)
WHERE cr.was_false_positive IS NOT NULL
ORDER BY cr.case_review_id, dqa.assessed_at DESC
"""

GROUND_TRUTH_SQL = """
SELECT
    gtl.label_type,
    gtl.expected_value,
    gtl.outlet_id,
    gtl.provider_id,
    gtl.window_start,
    gtl.window_end,
    dqa.status,
    dqa.sample_count,
    dqa.latest_source_at,
    dqa.assessed_at,
    COALESCE(
        (
            SELECT (dqi.evidence->>'rejected_event_count')::float
            FROM data_quality_issues dqi
            WHERE dqi.data_quality_assessment_id = dqa.data_quality_assessment_id
              AND dqi.issue_type = 'malformed_payload'
            LIMIT 1
        ),
        0.0
    ) AS rejected_event_count
FROM ground_truth_labels gtl
LEFT JOIN LATERAL (
    SELECT dqa.*
    FROM data_quality_assessments dqa
    WHERE dqa.outlet_id = gtl.outlet_id
      AND (gtl.provider_id IS NULL OR dqa.provider_id = gtl.provider_id)
      AND dqa.assessed_at >= gtl.window_start
      AND dqa.assessed_at <= gtl.window_end
    ORDER BY dqa.assessed_at
    LIMIT 1
    ) dqa ON TRUE
"""

# Deterministic demo features when no joinable quality assessment exists.
SYNTHETIC_FEATURE_PROFILES: dict[str, dict[str, Any]] = {
    "normal": {
        "status": FeedHealthStatus.FRESH,
        "sample_count": 27,
        "rejected_event_count": 0,
        "age_minutes": 10.0,
        "reliable": True,
    },
    "shortage": {
        "status": FeedHealthStatus.FRESH,
        "sample_count": 22,
        "rejected_event_count": 1,
        "age_minutes": 45.0,
        "reliable": True,
    },
    "anomaly": {
        "status": FeedHealthStatus.STALE,
        "sample_count": 18,
        "rejected_event_count": 2,
        "age_minutes": 280.0,
        "reliable": True,
    },
    "data_quality_incident": {
        "status": FeedHealthStatus.CONFLICTING,
        "sample_count": 8,
        "rejected_event_count": 3,
        "age_minutes": 360.0,
        "reliable": False,
    },
}


@dataclass(frozen=True)
class TrainingExample:
    label_source: str
    reliable: bool
    status: FeedHealthStatus
    sample_count: int
    rejected_event_count: int
    age_minutes: float


def _parse_status(raw: str | None) -> FeedHealthStatus:
    if not raw:
        return FeedHealthStatus.FRESH
    return FeedHealthStatus(raw)


def _age_minutes(*, latest_source_at: datetime | None, assessed_at: datetime | None) -> float:
    if latest_source_at is None or assessed_at is None:
        return 0.0
    delta = assessed_at - latest_source_at
    return max(0.0, delta.total_seconds() / 60.0)


def _rejection_rate(*, sample_count: int, rejected_event_count: float | int) -> float:
    rejected = int(rejected_event_count or 0)
    total = sample_count + rejected
    if rejected <= 0 or total <= 0:
        return 0.0
    return rejected / total


def _human_example_from_row(row: dict[str, Any]) -> TrainingExample:
    status = _parse_status(row.get("status"))
    sample_count = int(row["sample_count"])
    rejected = int(float(row.get("rejected_event_count") or 0))
    latest = row.get("latest_source_at")
    assessed = row.get("assessed_at")
    if isinstance(latest, str):
        latest = datetime.fromisoformat(latest.replace("Z", "+00:00"))
    if isinstance(assessed, str):
        assessed = datetime.fromisoformat(assessed.replace("Z", "+00:00"))
    return TrainingExample(
        label_source="human_review",
        reliable=not bool(row["was_false_positive"]),
        status=status,
        sample_count=sample_count,
        rejected_event_count=rejected,
        age_minutes=_age_minutes(latest_source_at=latest, assessed_at=assessed),
    )


def _synthetic_reliable(label_type: str, expected_value: dict[str, Any]) -> bool:
    if label_type == "data_quality_incident":
        return False
    if label_type == "normal":
        return True
    # shortage / anomaly: real incident windows — alerts grounded in adequate feeds.
    return bool(expected_value.get("positive", True))


def _synthetic_example_from_row(row: dict[str, Any]) -> TrainingExample:
    label_type = row["label_type"]
    expected_raw = row.get("expected_value") or "{}"
    expected = expected_raw if isinstance(expected_raw, dict) else json.loads(expected_raw)
    profile = SYNTHETIC_FEATURE_PROFILES.get(label_type, SYNTHETIC_FEATURE_PROFILES["normal"])

    if row.get("status"):
        status = _parse_status(row["status"])
        sample_count = int(row["sample_count"])
        rejected = int(float(row.get("rejected_event_count") or 0))
        latest = row.get("latest_source_at")
        assessed = row.get("assessed_at")
        if isinstance(latest, str):
            latest = datetime.fromisoformat(latest.replace("Z", "+00:00"))
        if isinstance(assessed, str):
            assessed = datetime.fromisoformat(assessed.replace("Z", "+00:00"))
        age = _age_minutes(latest_source_at=latest, assessed_at=assessed)
    else:
        status = profile["status"]
        sample_count = int(profile["sample_count"])
        rejected = int(profile["rejected_event_count"])
        age = float(profile["age_minutes"])

    reliable = _synthetic_reliable(label_type, expected)
    return TrainingExample(
        label_source="synthetic_ground_truth",
        reliable=reliable,
        status=status,
        sample_count=sample_count,
        rejected_event_count=rejected,
        age_minutes=age,
    )


def _load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def fetch_human_examples_from_db(conn) -> list[TrainingExample]:
    with conn.cursor() as cur:
        cur.execute(HUMAN_REVIEW_SQL)
        columns = [desc.name for desc in cur.description]
        rows = [dict(zip(columns, row)) for row in cur.fetchall()]
    return [_human_example_from_row(row) for row in rows]


def fetch_synthetic_examples_from_db(conn) -> list[TrainingExample]:
    with conn.cursor() as cur:
        cur.execute(GROUND_TRUTH_SQL)
        columns = [desc.name for desc in cur.description]
        rows = [dict(zip(columns, row)) for row in cur.fetchall()]
    return [_synthetic_example_from_row(row) for row in rows]


def fetch_human_examples_from_csv(dataset_dir: Path) -> list[TrainingExample]:
    reviews = {row["case_id"]: row for row in _load_csv_rows(dataset_dir / "case_reviews.csv")}
    cases = {row["case_id"]: row for row in _load_csv_rows(dataset_dir / "cases.csv")}
    quality_links = {
        row["alert_id"]: row["data_quality_assessment_id"]
        for row in _load_csv_rows(dataset_dir / "alert_quality_assessments.csv")
    }
    projections = {
        row["liquidity_projection_id"]: row
        for row in _load_csv_rows(dataset_dir / "liquidity_projections.csv")
    }
    for row in _load_csv_rows(dataset_dir / "alert_liquidity_projections.csv"):
        projection = projections.get(row["liquidity_projection_id"])
        if projection and projection.get("primary_data_quality_assessment_id"):
            quality_links.setdefault(
                row["alert_id"], projection["primary_data_quality_assessment_id"]
            )
    anomaly_flags = {
        row["anomaly_flag_id"]: row for row in _load_csv_rows(dataset_dir / "anomaly_flags.csv")
    }
    for row in _load_csv_rows(dataset_dir / "alert_anomaly_flags.csv"):
        flag = anomaly_flags.get(row["anomaly_flag_id"])
        if flag and flag.get("data_quality_assessment_id"):
            quality_links.setdefault(row["alert_id"], flag["data_quality_assessment_id"])

    assessments = {
        row["data_quality_assessment_id"]: row
        for row in _load_csv_rows(dataset_dir / "data_quality_assessments.csv")
    }
    issues_by_assessment: dict[str, list[dict[str, str]]] = {}
    for issue in _load_csv_rows(dataset_dir / "data_quality_issues.csv"):
        issues_by_assessment.setdefault(issue["data_quality_assessment_id"], []).append(issue)

    examples: list[TrainingExample] = []
    for case_id, review in reviews.items():
        case = cases.get(case_id)
        if not case:
            continue
        alert_id = case["alert_id"]
        assessment_id = quality_links.get(alert_id)
        if not assessment_id:
            continue
        assessment = assessments.get(assessment_id)
        if not assessment:
            continue
        rejected = 0.0
        for issue in issues_by_assessment.get(assessment_id, []):
            if issue["issue_type"] == "malformed_payload":
                evidence = json.loads(issue["evidence"].replace('""', '"'))
                rejected = float(evidence.get("rejected_event_count", 1))
        row = {
            "was_false_positive": review["was_false_positive"].lower() == "true",
            "status": assessment["status"],
            "sample_count": assessment["sample_count"],
            "latest_source_at": assessment["latest_source_at"] or None,
            "assessed_at": assessment["assessed_at"],
            "rejected_event_count": rejected,
        }
        examples.append(_human_example_from_row(row))
    return examples


def fetch_synthetic_examples_from_csv(dataset_dir: Path) -> list[TrainingExample]:
    labels = _load_csv_rows(dataset_dir / "ground_truth_labels.csv")
    assessments = _load_csv_rows(dataset_dir / "data_quality_assessments.csv")
    examples: list[TrainingExample] = []
    for label in labels:
        matched = None
        for assessment in assessments:
            if assessment["outlet_id"] != label["outlet_id"]:
                continue
            provider_id = label.get("provider_id") or ""
            if provider_id and assessment["provider_id"] != provider_id:
                continue
            assessed_at = assessment["assessed_at"]
            if label["window_start"] <= assessed_at <= label["window_end"]:
                matched = assessment
                break
        row = dict(label)
        if matched:
            row.update(
                {
                    "status": matched["status"],
                    "sample_count": matched["sample_count"],
                    "latest_source_at": matched.get("latest_source_at") or None,
                    "assessed_at": matched["assessed_at"],
                    "rejected_event_count": 0,
                }
            )
        examples.append(_synthetic_example_from_row(row))
    return examples


def examples_to_xy(examples: list[TrainingExample]) -> tuple[list[list[float]], list[int]]:
    x_rows: list[list[float]] = []
    y_rows: list[int] = []
    for example in examples:
        features = build_feature_vector(
            status=example.status,
            sample_count=example.sample_count,
            rejected_event_count=example.rejected_event_count,
            age_minutes=example.age_minutes,
        )
        x_rows.append(features)
        y_rows.append(1 if example.reliable else 0)
    return x_rows, y_rows


def train_and_save(
    examples: list[TrainingExample],
    *,
    output_path: Path,
) -> ConfidenceCalibrationModel:
    try:
        import sklearn
        from sklearn.linear_model import LogisticRegression
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "scikit-learn is required for training (pip install -r backend/requirements.txt)"
        ) from exc

    n_human = sum(1 for e in examples if e.label_source == "human_review")
    n_synthetic = sum(1 for e in examples if e.label_source == "synthetic_ground_truth")
    total = len(examples)
    if total < cfg.CALIBRATION_MIN_LABELED_EXAMPLES:
        raise SystemExit(
            f"Insufficient labeled examples: {total} "
            f"(human_review={n_human}, synthetic_ground_truth={n_synthetic}); "
            f"need >= {cfg.CALIBRATION_MIN_LABELED_EXAMPLES}"
        )

    x_rows, y_rows = examples_to_xy(examples)
    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(x_rows, y_rows)

    artifact = ConfidenceCalibrationModel(
        coefficients=tuple(float(c) for c in model.coef_[0]),
        intercept=float(model.intercept_[0]),
        feature_names=FEATURE_NAMES,
        trained_at=utc_now_iso(),
        n_human_examples=n_human,
        n_synthetic_examples=n_synthetic,
        sklearn_version=sklearn.__version__,
    )
    saved = artifact.save(output_path)
    print(f"Wrote calibration artifact: {saved}")
    print(
        f"Training report: human_review={n_human}, "
        f"synthetic_ground_truth={n_synthetic}, total={total}"
    )
    return artifact


def build_parser() -> argparse.ArgumentParser:
    repo_root = Path(__file__).resolve().parents[3]
    default_dataset = repo_root / "data" / "generated" / "moderate_demo"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--from-csv",
        type=Path,
        default=None,
        help="Load labels from generated CSV exports instead of PostgreSQL",
    )
    parser.add_argument(
        "--include-synthetic",
        action="store_true",
        help="Include synthetic ground_truth_labels rows",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=cfg.CONFIDENCE_CALIBRATION_ARTIFACT_PATH,
        help="Path for the serialized calibration artifact",
    )
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=default_dataset,
        help="CSV dataset directory when --from-csv is used",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    human_examples: list[TrainingExample]
    synthetic_examples: list[TrainingExample] = []

    if args.from_csv is not None or not _db_available():
        dataset_dir = args.from_csv or args.dataset_dir
        if not dataset_dir.is_dir():
            print(f"Dataset directory not found: {dataset_dir}", file=sys.stderr)
            return 2
        human_examples = fetch_human_examples_from_csv(dataset_dir)
        if args.include_synthetic:
            synthetic_examples = fetch_synthetic_examples_from_csv(dataset_dir)
    else:
        from migrations.run_migrations import _load_dotenv, open_connection

        _load_dotenv()
        _, _, conn = open_connection()
        with conn:
            human_examples = fetch_human_examples_from_db(conn)
            if args.include_synthetic:
                synthetic_examples = fetch_synthetic_examples_from_db(conn)

    examples = human_examples + synthetic_examples
    print(
        f"Loaded examples: human_review={len(human_examples)}, "
        f"synthetic_ground_truth={len(synthetic_examples)}, total={len(examples)}"
    )

    try:
        train_and_save(examples, output_path=args.output)
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


def _db_available() -> bool:
    import os

    return bool(os.environ.get("DIRECT_DATABASE_URL") or os.environ.get("DATABASE_URL"))


if __name__ == "__main__":
    raise SystemExit(main())
