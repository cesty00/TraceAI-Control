import zipfile
from pathlib import Path

from src.audit.audit_checklist_report import build_audit_checklist_report
from src.audit.audit_traceability_report import build_audit_traceability_report
from src.report.audit_checklist_docx import (
    build_document_xml,
    generate_audit_checklist_docx_report,
)
from tests.test_audit_traceability_report import make_case


def test_audit_checklist_docx_contains_required_sections_and_title() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    xml = build_document_xml(report)

    assert "TEST DE TRASABILITATE PENTRU AUDIT" in xml
    assert "Rezumat de conformare checklist" in xml
    assert "01_EXERCITIU — Fișa principală a exercițiului" in xml
    assert "02_TABEL_I_AMONTE — Materii prime, ambalaje și materiale auxiliare" in xml
    assert "03_TABEL_II_AVAL — Livrări produs finit" in xml
    assert "04_PRODUCTIE_CONSUM — Detaliere pe comenzi de producție" in xml
    assert "05_FLUX_LOTURI_SI_DOCUMENTE — Fluxuri loturi și documente" in xml
    assert "Registru documente fizice de pregătit pentru auditor" in xml
    assert "Concluzie audit intern" in xml


def test_audit_checklist_docx_uses_explicit_checklist_columns() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    xml = build_document_xml(report)

    for upstream_header in [
        "Dată recepție",
        "Furnizor",
        "Tip document",
        "Număr document",
        "Dată document",
        "Stoc la moment",
        "Livrări terți",
    ]:
        assert upstream_header in xml

    for downstream_header in [
        "Client",
        "Adresă",
        "Dată livrare",
        "Cantitate livrată",
        "Număr document",
        "Comandă WMS",
    ]:
        assert downstream_header in xml


def test_audit_checklist_docx_renders_split_receipt_fields_when_available() -> None:
    traceability_case = make_case()
    raw_row = traceability_case.report_tables.order_traceability.rows[0]
    raw_row.values["Recepții WMS consum"] = "total 5000 Kilogram; 300005747/Fish Invest LTD: 5000 Kilogram"
    raw_row.values["Stoc consum la moment"] = "125 Kilogram; locații: Depozit Principal"

    report = build_audit_checklist_report(build_audit_traceability_report(traceability_case))
    xml = build_document_xml(report)

    assert "WMS recepție" in xml
    assert "300005747" in xml
    assert "Fish Invest LTD" in xml
    assert "125 Kilogram; locații: Depozit Principal" in xml


def test_generate_audit_checklist_docx_report_writes_valid_docx(tmp_path: Path) -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    output = tmp_path / "audit_checklist.docx"

    result = generate_audit_checklist_docx_report(report, output)

    assert result == output
    assert output.exists()
    with zipfile.ZipFile(output) as package:
        names = set(package.namelist())
        assert "word/document.xml" in names
        document_xml = package.read("word/document.xml").decode("utf-8")
    assert "TEST DE TRASABILITATE PENTRU AUDIT" in document_xml
    assert "Rezumat de conformare checklist" in document_xml
