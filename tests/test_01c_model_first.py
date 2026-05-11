import zipfile
from pathlib import Path

from src.audit.audit_checklist_report import build_audit_checklist_report
from src.audit.audit_traceability_report import build_audit_traceability_report
from src.report.audit_checklist_docx import (
    AuditReportPolicy,
    build_document_register_section,
    build_document_xml,
    generate_audit_checklist_docx_report,
)
from src.ui.audit_checklist_json import audit_checklist_ui_payload_from_report
from tests.test_audit_traceability_report import make_case


def build_reports():
    traceability = build_audit_traceability_report(make_case())
    checklist = build_audit_checklist_report(traceability)
    return traceability, checklist


def test_mapper_upstream_receipt_populates_optional_fields() -> None:
    report, _ = build_reports()

    upstream_doc = next(doc for doc in report.physical_documents if doc.document_area == "NIR")

    assert upstream_doc.document_number == "300005747"
    assert upstream_doc.document_date == "2026-04-09"
    assert upstream_doc.receipt_date == "2026-04-09"
    assert upstream_doc.supplier == "Fish Invest LTD"


def test_mapper_downstream_delivery_populates_optional_fields() -> None:
    report, _ = build_reports()

    delivery_doc = next(doc for doc in report.physical_documents if doc.document_area == "WMS")

    assert delivery_doc.document_number == "38569"
    assert delivery_doc.client == "LIDL ROMAN - DEPOZIT NORD"
    assert delivery_doc.delivery_date == "2026-04-11"
    assert delivery_doc.document_date == "FARA DATE IDENTIFICATE"


def test_production_document_does_not_invent_disallowed_fields() -> None:
    report, _ = build_reports()

    prd_doc = next(doc for doc in report.physical_documents if doc.document_area == "PRD")

    assert prd_doc.document_number == "0030412_DC"
    assert prd_doc.document_date == "2026-04-10"
    assert prd_doc.supplier == "FARA DATE IDENTIFICATE"
    assert prd_doc.client == "FARA DATE IDENTIFICATE"
    assert prd_doc.receipt_date == "FARA DATE IDENTIFICATE"
    assert prd_doc.delivery_date == "FARA DATE IDENTIFICATE"


def test_checklist_model_serializes_optional_fields_with_missing_defaults() -> None:
    _, checklist = build_reports()

    delivery_doc = next(doc for doc in checklist.document_register if doc.area == "WMS")
    prd_doc = next(doc for doc in checklist.document_register if doc.area == "PRD")

    assert delivery_doc.document_number == "38569"
    assert delivery_doc.client == "LIDL ROMAN - DEPOZIT NORD"
    assert delivery_doc.delivery_date == "2026-04-11"
    assert prd_doc.supplier == "FARA DATE IDENTIFICATE"
    assert prd_doc.client == "FARA DATE IDENTIFICATE"
    assert prd_doc.receipt_date == "FARA DATE IDENTIFICATE"
    assert prd_doc.delivery_date == "FARA DATE IDENTIFICATE"


def test_ui_json_remains_v1_and_additive() -> None:
    _, checklist = build_reports()

    payload = audit_checklist_ui_payload_from_report(checklist, data_quality={})
    row = payload["report"]["document_register"][0]

    assert payload["schema_version"] == "audit-checklist-ui.v1"
    assert "area" in row
    assert "document_reference" in row
    assert "document_number" in row
    assert "document_date" in row
    assert "receipt_date" in row
    assert "supplier" in row
    assert "client" in row
    assert "delivery_date" in row


def test_docx_still_generates_without_layout_change(tmp_path: Path) -> None:
    _, checklist = build_reports()

    xml = build_document_xml(checklist)
    register_xml = "".join(build_document_register_section(checklist, AuditReportPolicy()))

    assert "Registru documente fizice" in xml
    for banned_header in ["Număr document", "Dată document", "Dată recepție", "Furnizor", "Client"]:
        assert banned_header not in register_xml

    output = generate_audit_checklist_docx_report(checklist, tmp_path / "audit_checklist.docx")
    with zipfile.ZipFile(output) as package:
        assert "word/document.xml" in set(package.namelist())
