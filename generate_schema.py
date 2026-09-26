"""Regenerate schema.json from the pydantic models in models.py.

Run this any time models.py changes, so schema.json (used as external
documentation / for validation in other tools) stays in sync automatically
instead of being hand-edited and drifting out of date.

Usage:
    python generate_schema.py
"""

import json
from pathlib import Path

from models import MonitoringFormDocumentData


def main() -> None:
    schema = MonitoringFormDocumentData.model_json_schema()
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "MonitoringFormDocumentData",
        **schema,
    }
    out_path = Path("schema.json")
    out_path.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
