"""Local diagnostic bundle generator for TraceAI Control.

The diagnostic bundle is intended for support and architecture observability. It
collects non-destructive JSON snapshots that explain what the installed app saw
locally: build metadata, source inventory, preflight status and audit UI payload.
"""

from __future__ import annotations

import argparse
import json
import zipfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.core.build_info import build_info_to_dict, get_build_info
from src.core.preflight_report import build_preflight_report, preflight_report_to_dict
from src.core.source_inventory import build_inventory_report, report_to_dict
from src.ui.audit_checklist_json import build_audit_checklist_ui_payload

DIAGNOSTIC_SCHEMA_VERSION = "traceai-diagnostic-bundle.v1"


@dataclass(frozen=True)
class DiagnosticBundleManifest:
    """Manifest written inside every diagnostic ZIP."""

    schema_version: str
    generated_at: str
    source_directory: str
    code: str
    lot: str
    files: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def build_diagnostic_bundle(
    source_directory: str | Path,
    code: str,
    lot: str,
    output_zip_path: str | Path,
    generated_report_path: str | Path | None = None,
) -> Path:
    """Generate a local diagnostic ZIP.

    The function is best-effort: build/source/preflight errors are captured in
    the manifest and individual `*_error.json` files, so support still receives a
    useful artifact even when a later layer fails.
    """

    output_zip = Path(output_zip_path).expanduser().resolve()
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    files: dict[str, str | bytes] = {}
    warnings: list[str] = []
    errors: list[str] = []

    def add_json(name: str, payload: Any) -> None:
        files[name] = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"

    def add_error(name: str, exc: Exception) -> None:
        message = f"{type(exc).__name__}: {exc}"
        errors.append(f"{name}: {message}")
        add_json(name, {"error": message})

    try:
        add_json("build_info.json", build_info_to_dict(get_build_info()))
    except Exception as exc:  # pragma: no cover - defensive support artifact
        add_error("build_info_error.json", exc)

    try:
        inventory = build_inventory_report(source_directory)
        add_json("source_inventory.json", report_to_dict(inventory))
    except Exception as exc:  # pragma: no cover - defensive support artifact
        add_error("source_inventory_error.json", exc)

    try:
        preflight = build_preflight_report(source_directory, code, lot)
        add_json("preflight.json", preflight_report_to_dict(preflight))
        if preflight.warnings:
            warnings.extend(f"preflight: {warning}" for warning in preflight.warnings)
        if preflight.blockers:
            errors.extend(f"preflight blocker: {blocker}" for blocker in preflight.blockers)
    except Exception as exc:  # pragma: no cover - defensive support artifact
        add_error("preflight_error.json", exc)

    try:
        audit_payload = build_audit_checklist_ui_payload(source_directory, code, lot)
        add_json("audit_checklist_ui.json", audit_payload)
    except Exception as exc:  # pragma: no cover - audit can fail while inventory remains useful
        add_error("audit_checklist_ui_error.json", exc)

    if generated_report_path:
        report_path = Path(generated_report_path).expanduser()
        if report_path.is_file():
            try:
                files[f"reports/{report_path.name}"] = report_path.read_bytes()
            except OSError as exc:
                add_error("generated_report_copy_error.json", exc)
        else:
            warnings.append(f"generated_report_path not found: {report_path}")

    manifest = DiagnosticBundleManifest(
        schema_version=DIAGNOSTIC_SCHEMA_VERSION,
        generated_at=generated_at,
        source_directory=str(Path(source_directory).expanduser().resolve()),
        code=code,
        lot=lot,
        files=sorted(files),
        warnings=deduplicate(warnings),
        errors=deduplicate(errors),
    )
    files["manifest.json"] = json.dumps(asdict(manifest), ensure_ascii=False, indent=2) + "\n"
    files["README.txt"] = build_readme(manifest)

    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, payload in files.items():
            archive.writestr(name, payload)

    return output_zip


def build_readme(manifest: DiagnosticBundleManifest) -> str:
    lines = [
        "TraceAI Control diagnostic bundle",
        "=================================",
        "",
        f"Schema: {manifest.schema_version}",
        f"Generated at: {manifest.generated_at}",
        f"Source directory: {manifest.source_directory}",
        f"Code/Lot: {manifest.code} / {manifest.lot}",
        "",
        "Files:",
    ]
    lines.extend(f"- {name}" for name in manifest.files)
    if manifest.warnings:
        lines.extend(["", "Warnings:"])
        lines.extend(f"- {warning}" for warning in manifest.warnings)
    if manifest.errors:
        lines.extend(["", "Errors/blockers:"])
        lines.extend(f"- {error}" for error in manifest.errors)
    return "\n".join(lines).rstrip() + "\n"


def deduplicate(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if text and text not in seen:
            result.append(text)
            seen.add(text)
    return result


def default_diagnostic_zip_path(output_directory: str | Path, code: str, lot: str) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_code = sanitize_filename_part(code)
    safe_lot = sanitize_filename_part(lot)
    return Path(output_directory).expanduser().resolve() / f"TraceAI-Diagnostic-{safe_code}-{safe_lot}-{timestamp}.zip"


def sanitize_filename_part(value: str) -> str:
    text = "".join(character if character.isalnum() or character in {"-", "_", "."} else "_" for character in str(value).strip())
    return text.strip("._") or "UNKNOWN"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generează ZIP diagnostic local TraceAI Control.")
    parser.add_argument("source_directory", help="Folderul cu sursele oficiale.")
    parser.add_argument("--code", required=True, help="Cod articol/produs căutat.")
    parser.add_argument("--lot", required=True, help="Lot căutat.")
    parser.add_argument("--output", "-o", required=True, help="Cale output ZIP diagnostic.")
    parser.add_argument("--report", help="Raport DOCX generat, copiat opțional în ZIP.")
    args = parser.parse_args(argv)

    output = build_diagnostic_bundle(args.source_directory, args.code, args.lot, args.output, args.report)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
