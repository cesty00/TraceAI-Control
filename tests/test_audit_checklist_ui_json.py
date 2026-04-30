import json
from pathlib import Path

from src.audit.audit_checklist_report import build_audit_checklist_report
from src.audit.audit_traceability_report import build_audit_traceability_report
from src.ui.audit_checklist_json import (
    UI_SCHEMA_VERSION,
    audit_checklist_ui_payload_from_report,
    write_audit_checklist_ui_json,
)
from tests.test_audit_traceability_report import make_case


EXPECTED_SECTION_KEYS = [
    "conformity",
    "exercise",
    "balance",
    "downstream",
    "upstream",
    "production_consumption",
    "lot_flows",
    "document_register",
    "conclusion",
]


def build_payload() -> dict:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    return audit_checklist_ui_payload_from_report(report)


def test_audit_checklist_ui_payload_has_schema_version_subject_and_report() -> None:
    payload = build_payload()

    assert payload["schema_version"] == UI_SCHEMA_VERSION
    assert payload["schema_version"] == "audit-checklist-ui.v1"
    assert payload["subject"] == {
        "code": "DS099904011",
        "lot": "103.26",
        "product_name": "PF-REFRIGERAT-P FILE SOMON 200G ATM PENNY",
        "case_type": "FINISHED_PRODUCT",
        "result": "PASS",
    }
    assert payload["report"]["exercise"]["code"] == "DS099904011"
    assert payload["report"]["balance"]["prd_produced"] == "168 BUCATA"


def test_audit_checklist_ui_sections_keep_expected_display_order() -> None:
    payload = build_payload()

    assert [section["key"] for section in payload["sections"]] == EXPECTED_SECTION_KEYS
    assert [section["title"] for section in payload["sections"]] == [
        "Rezumat de conformare checklist",
        "01_EXERCITIU — Fișa principală",
        "Bilanț produs finit",
        "03_TABEL_II_AVAL — Livrări produs finit",
        "02_TABEL_I_AMONTE — Materii prime, ambalaje și auxiliare",
        "04_PRODUCTIE_CONSUM — Detaliere pe comenzi",
        "05_FLUX_LOTURI_SI_DOCUMENTE — Fluxuri loturi",
        "Registru documente fizice",
        "Concluzie audit intern",
    ]


def test_audit_checklist_ui_sections_expose_downstream_upstream_and_balance() -> None:
    payload = build_payload()
    sections = {section["key"]: section for section in payload["sections"]}

    assert sections["balance"]["data"] == payload["report"]["balance"]
    assert sections["downstream"]["rows"] == payload["report"]["downstream"]
    assert sections["upstream"]["rows"] == payload["report"]["upstream"]
    assert len(sections["downstream"]["rows"]) == 1
    assert len(sections["upstream"]["rows"]) == 3
    assert sections["downstream"]["rows"][0]["delivery_document_number"] == "38569"
    assert {row["code"] for row in sections["upstream"]["rows"]} == {"DS099903930", "10002", "60001"}


def test_audit_checklist_ui_payload_is_json_serializable_and_writable(tmp_path: Path) -> None:
    payload = build_payload()
    output = tmp_path / "audit_ui.json"

    dumped = json.dumps(payload, ensure_ascii=False)
    assert "audit-checklist-ui.v1" in dumped

    result = write_audit_checklist_ui_json(payload, output)

    assert result == output
    loaded = json.loads(output.read_text(encoding="utf-8"))
    assert loaded["schema_version"] == "audit-checklist-ui.v1"
    assert [section["key"] for section in loaded["sections"]] == EXPECTED_SECTION_KEYS
