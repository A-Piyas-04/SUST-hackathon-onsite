"""Generate and write the OpenAPI baseline artifact."""

from __future__ import annotations

import json
import os
from pathlib import Path

from app.db.dsn import load_dotenv
from app.main import create_app

OUTPUT = Path(__file__).resolve().parents[3] / "docs" / "openapi" / "openapi.v1.json"


def main() -> None:
    load_dotenv()
    os.environ.setdefault(
        "DIRECT_DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5433/liquidity_platform",
    )
    app = create_app()
    schema = app.openapi()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    print(f"Wrote OpenAPI spec to {OUTPUT}")


if __name__ == "__main__":
    main()
