import zipfile
from pathlib import Path

from src.audit.audit_checklist_report import build_audit_checklist_report
from src.audit.audit_traceability_report import build_audit_traceability_report
from src.core.build_info import BuildInfo, format_build_info_line
from src.report.audit_checklist_docx import (
    AuditReportPolicy,
    DOCUMENT_REGISTER_CHECKBOX,
    QUICK_AUDITOR_GUIDE_ITEMS,
    build_document_xml,
    generate_audit_checklist_docx_report,
)
from tests.test_audit_traceability_report import make_case


def test_audit_checklist_docx_contains_required_sections_and_title() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    xml = build_document_xml(report)

    assert "TEST DE TRASABILITATE PENTRU AUDIT" in xml
    assert "Card verdict auditor" in xml
    assert "Ghid rapid pentru auditor" in xml
    assert "Rezumat de conformare checklist" in xml
    assert "00_DATA_QUALITY — verificare surse înainte de raport" in xml
    assert "Status=WARNING; surse=4/4; erori=0; warning=2; issues=2" in xml
    assert "01_EXERCITIU — Fișa principală a exercițiului" in xml
    assert "02_TABEL_I_AMONTE — Materii prime, ambalaje și materiale auxiliare" in xml
    assert "03_TABEL_II_AVAL — Livrări produs finit" in xml
    assert "04_PRODUCTIE_CONSUM — Detaliere pe comenzi de producție" in xml
    assert "05_FLUX_LOTURI_SI_DOCUMENTE — Fluxuri loturi și documente" in xml
    assert "Registru documente fizice de pregătit pentru auditor" in xml
    assert "Concluzie audit intern" in xml
    assert "Informații build raport" in xml


def test_audit_checklist_docx_contains_auditor_verdict_card_before_quick_guide() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    xml = build_document_xml(report)

    assert xml.index("Card verdict auditor") < xml.index("Ghid rapid pentru auditor")
    for expected_text in [
        "Verdict audit",
        "Bilanț PRD vs WMS",
        "Aval / livrări",
        "Amonte / loturi sursă",
        "Documente fizice",
    ]:
        assert expected_text in xml


def test_audit_checklist_docx_contains_quick_auditor_guide_points() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    xml = build_document_xml(report)

    assert "Ghid rapid pentru auditor" in xml
    for guide_item in QUICK_AUDITOR_GUIDE_ITEMS:
        assert guide_item in xml


def test_audit_checklist_docx_document_register_is_printable_checklist() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    xml = build_document_xml(report)

    assert "Coloana Bifat permite folosirea tabelului ca listă de verificare tipărită" in xml
    assert "Bifat" in xml
    assert DOCUMENT_REGISTER_CHECKBOX in xml
    assert "required" in xml


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


def test_audit_checklist_docx_renders_build_information() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    build_info = BuildInfo(
        app_name="TraceAI Control",
        app_version="1.0.0",
        build_commit="abcdef1234567890",
        build_date="build-date",
        build_channel="local",
        generated_at="generated-at",
    )

    xml = build_document_xml(report, build_info=build_info)

    assert "Build raport: 1.0.0 / commit abcdef123456 / generat generated-at" in xml
    assert "Commit build" in xml
    assert "abcdef1234567890" in xml
    assert format_build_info_line(build_info) == "TraceAI Control 1.0.0 | commit abcdef123456 | channel local | generated generated-at"


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
    assert "125 Kilogram; loc. Depozit Principal" in xml


def test_audit_report_policy_compacts_stock_location_label() -> None:
    policy = AuditReportPolicy()

    assert policy.stock("125 Kilogram; locații: Depozit Principal") == "125 Kilogram; loc. Depozit Principal"
    assert policy.stock("FARA DATE IDENTIFICATE") == "FARA DATE IDENTIFICATE"


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
    assert "Card verdict auditor" in document_xml
    assert "Ghid rapid pentru auditor" in document_xml
    assert "Rezumat de conformare checklist" in document_xml
    assert "00_DATA_QUALITY — verificare surse înainte de raport" in document_xml
    assert "Informații build raport" in document_xml


def test_generate_audit_checklist_docx_report_writes_case_metadata_header_footer(tmp_path: Path) -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    output = tmp_path / "audit_checklist.docx"
    build_info = BuildInfo(
        app_name="TraceAI Control",
        app_version="1.2.3",
        build_commit="abcdef1234567890",
        build_date="build-date",
        build_channel="test-channel",
        generated_at="2026-05-04T11:00:00+00:00",
    )

    generate_audit_checklist_docx_report(report, output, build_info=build_info)

    with zipfile.ZipFile(output) as package:
        document_xml = package.read("word/document.xml").decode("utf-8")
        header_xml = package.read("word/header1.xml").decode("utf-8")
        footer_xml = package.read("word/footer1.xml").decode("utf-8")

    assert '<w:pgSz w:w="16838" w:h="11906" w:orient="landscape"/>' in document_xml
    assert "TraceAI Control — Test de trasabilitate pentru audit" in header_xml
    assert report.exercise.code in header_xml
    assert report.exercise.lot in header_xml
    assert report.exercise.product_name in header_xml
    assert "TraceAI Control 1.2.3" in footer_xml
    assert "commit abcdef123456" in footer_xml
    assert "canal test-channel" in footer_xml
    assert "generat 2026-05-04T11:00:00+00:00" in footer_xml
    assert 'w:instr="PAGE"' in footer_xml


def test_audit_checklist_docx_conclusion_mentions_physical_documents_remain_required() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    xml = build_document_xml(report)

    assert "Ea nu înlocuiește verificarea documentelor fizice" in xml
    assert "ce trebuie atașat dosarului de audit" in xml


def test_audit_checklist_docx_downstream_section_mentions_physical_delivery_documents() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    xml = build_document_xml(report)

    assert "Auditorul trebuie să compare aceste rânduri cu documentele fizice de livrare" in xml
    assert "documentele WMS indicate" in xml
