#!/usr/bin/env python3
"""Exports the live FastAPI OpenAPI schema to openapi/openapi.yaml.

Owner: Member 1. Run this after any router/schema change to keep the frozen
v1 contract file in sync with the real, importable app (rather than a
hand-maintained YAML file that can silently drift). "Frozen v1" means the
overall shape/version is stable for this phase, not that this export script
is a one-time throwaway.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402


def main() -> int:
    schema = app.openapi()
    out_path = BACKEND_DIR / "openapi" / "openapi.yaml"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(schema, f, sort_keys=False, allow_unicode=True)
    print(f"Wrote {out_path} ({len(schema.get('paths', {}))} paths)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
