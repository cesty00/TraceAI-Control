"""JSON contract for the TraceAI audit checklist interface.

The UI should consume this module instead of rebuilding traceability logic from
raw TraceabilityCase tables. This keeps one source of truth:

source files -> TraceabilityCase -> AuditTraceabilityReport -> AuditChecklistReport

The same AuditChecklistReport feeds both the DOCX renderer and the UI JSON.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.audit.audit_checklist_report import (
    AuditChecklistReport,
    audit_checklist_report_to_dict,
    build_audit_checklist_report,
)
from src.audit.audit_traceability_report import build_audit_traceability_report
from src.rules.run_traceability_case import run_traceability_case

UI_SCHEMA_VERSION = "audit-checklist-ui.v1"


def build_audit_checklist_ui_payload(source_directory: str | Path, code: str, lot: str) -> dict[str, Any]:
    """Build the JSON payload consumed by the UI for one traceability case."""

    traceability_case = run_traceability_case(str(source_directory), code, lot)
    audit_report = build_audit_traceability_report(traceability_case)
    checklist_report = build_audit_checklist_report(audit_report)
    return audit_checklist_ui_payload_from_report(checklist_report)


def audit_checklist_ui_payload_from_report(report: AuditChecklistReport) -> dict[str, Any]:
    """Convert AuditChecklistReport into a UI-friendly stable payload.

    The raw report dictionary is preserved under ``report`` so the UI can access
    every field. The ``sections`` list gives the frontend a deterministic display
    order and human-readable labels without duplicating business rules.
    """

    report_dict = audit_checklist_report_to_dict(report)
    return {
        "schema_version": UI_SCHEMA_VERSION,
        "subject": {
            "code": report.exercise.code,
            "lot": report.exercise.lot,
            "product_name": report.exercise.product_name,
            "case_type": report.exercise.case_type,
            "result": report.exercise.result,
        },
        "sections": build_ui_sections(report_dict),
        "report": report_dict,
    }


def build_ui_sections(report_dict: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the display order expected by the application interface."""

    return [
        {
            "key": "conformity",
            "title": "Rezumat de conformare checklist",
            "description": "Arată dacă cerințele principale ale exercițiului de trasabilitate sunt acoperite de datele identificate.",
            "rows": report_dict["conformity"],
        },
        {
            "key": "exercise",
            "title": "01_EXERCITIU — Fișa principală",
            "description": "Identifică produsul, lotul, sursele utilizate și rezultatul verificării.",
            "data": report_dict["exercise"],
        },
        {
            "key": "balance",
            "title": "Bilanț produs finit",
            "description": "Compară cantitatea produsă în PRD cu intrările și ieșirile lotului în WMS.",
            "data": report_dict["balance"],
        },
        {
            "key": "downstream",
            "title": "03_TABEL_II_AVAL — Livrări produs finit",
            "description": "Prezintă traseul lotului de produs finit către clienți, cu documente WMS și cantități livrate.",
            "rows": report_dict["downstream"],
        },
        {
            "key": "upstream",
            "title": "02_TABEL_I_AMONTE — Materii prime, ambalaje și auxiliare",
            "description": "Prezintă loturile care au intrat în produsul finit: consum, recepție, furnizor, document, stoc și observații.",
            "rows": report_dict["upstream"],
        },
        {
            "key": "production_consumption",
            "title": "04_PRODUCTIE_CONSUM — Detaliere pe comenzi",
            "description": "Leagă fiecare comandă de producție de cantitatea de produs finit și de consumurile aferente.",
            "rows": report_dict["production_consumption"],
        },
        {
            "key": "lot_flows",
            "title": "05_FLUX_LOTURI_SI_DOCUMENTE — Fluxuri loturi",
            "description": "Reunește recepțiile, consumul în lotul auditat, livrările către terți și stocul rămas pentru loturile sursă.",
            "rows": report_dict["lot_flows"],
        },
        {
            "key": "document_register",
            "title": "Registru documente fizice",
            "description": "Listează documentele care trebuie pregătite pentru auditor.",
            "rows": report_dict["document_register"],
        },
        {
            "key": "conclusion",
            "title": "Concluzie audit intern",
            "description": "Sintetizează rezultatul verificării și observațiile importante.",
            "data": {
                "status": report_dict["conclusion_status"],
                "text": report_dict["conclusion_text"],
                "observations": report_dict["observations"],
            },
        },
    ]


def write_audit_checklist_ui_json(payload: dict[str, Any], output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generează JSON UI pentru raportul audit checklist.")
    parser.add_argument("source_directory", help="Folderul cu sursele oficiale.")
    parser.add_argument("--code", required=True, help="Cod articol/produs căutat.")
    parser.add_argument("--lot", required=True, help="Lot căutat.")
    parser.add_argument("--output", "-o", required=True, help="Cale output JSON.")
    args = parser.parse_args(argv)

    payload = build_audit_checklist_ui_payload(args.source_directory, args.code, args.lot)
    write_audit_checklist_ui_json(payload, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
