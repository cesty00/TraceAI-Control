"""Discover multiple traceability cases from normalized source files.

The script is diagnostic-only. It helps avoid overfitting tests to one product by
listing representative code+lot cases from WMS and PRD sources.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Discover representative TraceAI test cases.")
    parser.add_argument("source_directory")
    parser.add_argument("--output", required=True)
    parser.add_argument("--json-output")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args(argv)

    source_dir = Path(args.source_directory)
    result = discover_cases(source_dir, args.limit)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(to_markdown(result), encoding="utf-8")
    if args.json_output:
        Path(args.json_output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated multi-case discovery report: {output}")
    return 0


def discover_cases(source_dir: Path, limit: int) -> dict[str, object]:
    wms_rows = read_csv_dicts(source_dir / "trasabilitate_wms.csv")
    prd_rows = read_csv_dicts(source_dir / "rapoarte productie.csv")

    prd_finished = Counter(
        (clean(row.get("PRE_Cod Articol")), clean(row.get("PRE_LOT")), clean(row.get("PRE_Denumire Articol")))
        for row in prd_rows
        if clean(row.get("PRE_Cod Articol")) and clean(row.get("PRE_LOT"))
    )
    prd_components = Counter(
        (clean(row.get("CON_Cod Articol")), clean(row.get("CON_LOT")), clean(row.get("CON_Denumire Articol")))
        for row in prd_rows
        if clean(row.get("CON_Cod Articol")) and clean(row.get("CON_LOT"))
    )
    wms_cases = Counter(
        (clean(row.get("Cod articol")), clean(row.get("Lot")), clean(row.get("Denumire articol")))
        for row in wms_rows
        if clean(row.get("Cod articol")) and clean(row.get("Lot"))
    )
    prd_finished_keys = {(code, lot) for code, lot, _name in prd_finished}
    wms_only = Counter({key: count for key, count in wms_cases.items() if (key[0], key[1]) not in prd_finished_keys})

    return {
        "source_directory": str(source_dir),
        "wms_row_count": len(wms_rows),
        "prd_row_count": len(prd_rows),
        "finished_product_candidates": rows_from_counter(prd_finished, limit),
        "component_candidates": rows_from_counter(prd_components, limit),
        "wms_only_candidates": rows_from_counter(wms_only, limit),
    }


def rows_from_counter(counter: Counter[tuple[str, str, str]], limit: int) -> list[dict[str, object]]:
    return [
        {"code": code, "lot": lot, "name": name, "rows": rows}
        for (code, lot, name), rows in counter.most_common(limit)
    ]


def read_csv_dicts(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    try:
        dialect = csv.Sniffer().sniff(text[:8192], delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    return list(csv.DictReader(text.splitlines(), dialect=dialect))


def clean(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.casefold() == "nan" else text


def to_markdown(result: dict[str, object]) -> str:
    lines = ["# TraceAI multi-case discovery", ""]
    lines.append(f"Source directory: `{result['source_directory']}`")
    lines.append(f"WMS rows: {result['wms_row_count']}")
    lines.append(f"PRD rows: {result['prd_row_count']}")
    append_section(lines, "Finished product candidates from PRD PRE_*", result["finished_product_candidates"])
    append_section(lines, "Component candidates from PRD CON_*", result["component_candidates"])
    append_section(lines, "WMS-only candidates", result["wms_only_candidates"])
    return "\n".join(lines) + "\n"


def append_section(lines: list[str], title: str, rows: object) -> None:
    lines.extend(["", f"## {title}", "", "| code | lot | name | rows |", "| --- | --- | --- | --- |"])
    for row in rows:
        lines.append(f"| {row['code']} | {row['lot']} | {row['name']} | {row['rows']} |")


if __name__ == "__main__":
    raise SystemExit(main())
