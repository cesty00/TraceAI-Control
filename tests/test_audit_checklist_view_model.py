import pytest

from src.audit.audit_checklist_report import build_audit_checklist_report
from src.audit.audit_traceability_report import build_audit_traceability_report
from src.ui.audit_checklist_json import UI_SCHEMA_VERSION, audit_checklist_ui_payload_from_report
from src.ui.audit_checklist_view_model import (
    AuditChecklistUiSection,
    build_audit_checklist_ui_view_model,
)
from tests.test_audit_checklist_ui_json import EXPECTED_SECTION_KEYS
from tests.test_audit_traceability_report import make_case


def build_payload() -> dict:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    return audit_checklist_ui_payload_from_report(report)


def payload_section_by_key(payload: dict, key: str) -> dict:
    return next(section for section in payload["sections"] if section["key"] == key)


def test_audit_checklist_view_model_uses_payload_sections_in_display_order() -> None:
    payload = build_payload()

    view_model = build_audit_checklist_ui_view_model(payload)

    assert view_model.schema_version == UI_SCHEMA_VERSION
    assert view_model.subject == payload["subject"]
    assert [section.key for section in view_model.sections] == EXPECTED_SECTION_KEYS
    assert [section.title for section in view_model.sections] == [
        section["title"] for section in payload["sections"]
    ]


def test_audit_checklist_view_model_maps_rows_and_details_without_rebuilding_report() -> None:
    payload = build_payload()
    view_model = build_audit_checklist_ui_view_model(payload)
    sections = {section.key: section for section in view_model.sections}

    assert sections["downstream"].kind == "table"
    assert sections["downstream"].rows == payload_section_by_key(payload, "downstream")["rows"]
    assert "delivery_document_number" in sections["downstream"].column_keys
    assert sections["balance"].kind == "details"
    assert sections["balance"].data == payload_section_by_key(payload, "balance")["data"]
    assert "prd_produced" in sections["balance"].field_keys
    assert sections["data_quality"].kind == "details"
    assert sections["data_quality"].data == payload_section_by_key(payload, "data_quality")["data"]
    assert sections["conclusion"].data["observations"] == payload["report"]["observations"]


def test_audit_checklist_view_model_preserves_sparse_table_columns_in_discovery_order() -> None:
    payload = {
        "schema_version": UI_SCHEMA_VERSION,
        "subject": {"code": "DS", "lot": "L"},
        "sections": [
            {
                "key": "custom",
                "title": "Custom",
                "description": "Sparse table",
                "rows": [
                    {"first": "1", "second": "2"},
                    {"second": "3", "third": "4"},
                ],
            }
        ],
        "report": {},
    }

    view_model = build_audit_checklist_ui_view_model(payload)

    assert view_model.sections == [
        AuditChecklistUiSection(
            key="custom",
            title="Custom",
            description="Sparse table",
            kind="table",
            rows=[{"first": "1", "second": "2"}, {"second": "3", "third": "4"}],
            column_keys=["first", "second", "third"],
        )
    ]


def test_audit_checklist_view_model_rejects_unsupported_schema() -> None:
    payload = build_payload()
    payload["schema_version"] = "audit-checklist-ui.v0"

    with pytest.raises(ValueError, match="Schema UI nesuportată"):
        build_audit_checklist_ui_view_model(payload)


def test_audit_checklist_view_model_rejects_invalid_rows_shape() -> None:
    payload = {
        "schema_version": UI_SCHEMA_VERSION,
        "subject": {"code": "DS", "lot": "L"},
        "sections": [
            {
                "key": "bad",
                "title": "Bad",
                "description": "Invalid rows",
                "rows": {"not": "a list"},
            }
        ],
    }

    with pytest.raises(ValueError, match="rows trebuie să fie listă"):
        build_audit_checklist_ui_view_model(payload)
