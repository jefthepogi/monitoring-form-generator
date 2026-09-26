"""
Maintain the `monitoring_items` list of input_data.json as a CSV file.

Typing dozens of chapter/section rows directly into JSON is error-prone.
This script lets you edit the monitoring items in a spreadsheet (CSV) instead,
then regenerates the `monitoring_items` array inside input_data.json from it.
All other sections of input_data.json (header_info, project_info,
table_columns, notes, signatures) are left untouched.

CSV columns (header row required), matching models.MonitoringItem 1:1:

    section_id, title, is_header, corrections, page_no, client_name, complied, remarks

- `is_header` and `complied` accept: true/false, yes/no, y/n, 1/0 (case-insensitive).
  Leave `complied` blank on header rows.
- Leave `section_id`, `corrections`, `page_no`, `client_name`, `remarks` blank if not applicable.

Usage:
    # Create a starter CSV from the monitoring_items already in input_data.json
    python manage_monitoring_csv.py export input_data.json monitoring_items.csv

    # After editing the CSV, write the items back into input_data.json
    python manage_monitoring_csv.py import monitoring_items.csv input_data.json

    # Import into a new file instead of overwriting the source
    python manage_monitoring_csv.py import monitoring_items.csv input_data.json --output updated_input_data.json
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import List

from models import MonitoringFormDocumentData, MonitoringItem

FIELDNAMES = ["section_id", "title", "is_header", "corrections", "page_no", "client_name", "complied", "remarks"]

TRUE_STRINGS = {"true", "yes", "y", "1"}
FALSE_STRINGS = {"false", "no", "n", "0", ""}


def _parse_bool(value: str, *, default: bool) -> bool:
    normalized = (value or "").strip().lower()
    if normalized in TRUE_STRINGS:
        return True
    if normalized in FALSE_STRINGS:
        return default if normalized == "" else False
    raise ValueError(f"Cannot interpret {value!r} as a boolean (use true/false, yes/no, or 1/0)")


def export_items_to_csv(json_path: str, csv_path: str) -> None:
    """Write the monitoring_items currently in a full input_data.json out to CSV."""
    data = MonitoringFormDocumentData.model_validate_json(Path(json_path).read_text(encoding="utf-8"))

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for item in data.monitoring_items:
            writer.writerow(
                {
                    "section_id": item.section_id,
                    "title": item.title,
                    "is_header": str(item.is_header).lower(),
                    "corrections": item.corrections or "",
                    "page_no": item.page_no or "",
                    "client_name": item.client_name or "",
                    "complied": "" if item.is_header else str(bool(item.complied)).lower(),
                    "remarks": item.remarks or "",
                }
            )

    print(f"Exported {len(data.monitoring_items)} monitoring items to {csv_path}")


def read_items_from_csv(csv_path: str) -> List[MonitoringItem]:
    items: List[MonitoringItem] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = [c for c in ("title",) if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"CSV is missing required column(s): {', '.join(missing)}")

        for row_num, row in enumerate(reader, start=2):  # header is row 1
            title = (row.get("title") or "").strip()
            if not title:
                continue  # skip blank rows
            try:
                is_header = _parse_bool(row.get("is_header", ""), default=False)
                complied = _parse_bool(row.get("complied", ""), default=True)
                items.append(
                    MonitoringItem(
                        section_id=(row.get("section_id") or "").strip(),
                        title=title,
                        is_header=is_header,
                        corrections=(row.get("corrections") or "").strip(),
                        page_no=(row.get("page_no") or "").strip(),
                        client_name=(row.get("client_name") or "").strip(),
                        complied=complied,
                        remarks=(row.get("remarks") or "").strip(),
                    )
                )
            except ValueError as exc:
                raise ValueError(f"CSV row {row_num}: {exc}") from exc
    return items


def import_items_from_csv(csv_path: str, json_path: str, output_path: str | None = None) -> None:
    """Regenerate monitoring_items in input_data.json from a CSV, keeping everything else intact."""
    items = read_items_from_csv(csv_path)

    raw = json.loads(Path(json_path).read_text(encoding="utf-8"))
    raw["monitoring_items"] = [item.model_dump() for item in items]

    # Validate the merged result end-to-end before writing anything out.
    validated = MonitoringFormDocumentData.model_validate(raw)

    dest = Path(output_path or json_path)
    dest.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Imported {len(validated.monitoring_items)} monitoring items into {dest}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_export = sub.add_parser("export", help="Write monitoring_items from a JSON file out to CSV")
    p_export.add_argument("json_path", help="Path to input_data.json (or similar)")
    p_export.add_argument("csv_path", help="Path to write the CSV to")

    p_import = sub.add_parser("import", help="Write monitoring_items from a CSV back into a JSON file")
    p_import.add_argument("csv_path", help="Path to the edited CSV")
    p_import.add_argument("json_path", help="Path to the input_data.json to update")
    p_import.add_argument("--output", help="Write to a different file instead of overwriting json_path")

    args = parser.parse_args()

    try:
        if args.command == "export":
            export_items_to_csv(args.json_path, args.csv_path)
        elif args.command == "import":
            import_items_from_csv(args.csv_path, args.json_path, args.output)
    except (ValueError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
