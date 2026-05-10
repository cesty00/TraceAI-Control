import zipfile
from pathlib import Path

from src.audit.audit_checklist_report import build_audit_checklist_report
from src.audit.audit_traceability_report import build_audit_traceability_report
from src.core.build_info import BuildInfo, format_build_info_line
from src.report.audit_checklist_docx import (
    AuditReportPolicy,
    DOCUMENT_REGISTER_CHECKBOX,
    DOCUMENT_REGISTER_COLUMN_WIDTHS,
    QUICK_AUDITOR_GUIDE_ITEMS,
    build_document_register_section,
    build_document_xml,
    build_title_block,
    generate_audit_checklist_docx_report,
)
from tests.test_audit_traceability_report import make_case


def test_audit_checklist_docx_contains_required_sections_and_title() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    xml = build_document_xml(report)

    assert "TEST DE TRASABILITATE PENTRU AUDIT" in xml
    assert "Card verdict auditor" in xml
    assert "Ghid rapid PP-03" in xml
    assert "Sumar Data Quality" in xml
    assert "Rezumat conformare checklist" in xml
    assert "00_DATA_QUALITY — verificare surse înainte de raport" in xml
    assert "Status=WARNING; surse=4/4; erori=0; warning=2; issues=2" in xml
    assert "AMONTE — Produs finit, producție și livrări" in xml
    assert "AVAL — Materii prime, ambalaje, auxiliare și loturi sursă" in xml
    assert "Comenzi producție și consumuri" in xml
    assert "Fluxuri loturi și documente" in xml
    assert "Registru documente fizice" in xml
    assert "Informații build" in xml


def test_audit_checklist_docx_pp03_section_order_is_stable() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    xml = build_document_xml(report)

    card_index = xml.index("Card verdict auditor")
    data_quality_index = xml.index("Sumar Data Quality", card_index + 1)
    conformity_index = xml.index("Rezumat conformare checklist", data_quality_index + 1)
    amonte_index = xml.index("AMONTE — Produs finit, producție și livrări", conformity_index + 1)
    aval_index = xml.index("AVAL — Materii prime, ambalaje, auxiliare și loturi sursă", amonte_index + 1)
    production_index = xml.index("Comenzi producție și consumuri", aval_index + 1)
    flow_index = xml.index("Fluxuri loturi și documente", production_index + 1)
    register_index = xml.index("Registru documente fizice", flow_index + 1)
    build_index = xml.index("Informații build", register_index + 1)

    assert card_index < data_quality_index
    assert data_quality_index < conformity_index
    assert conformity_index < amonte_index
    assert amonte_index < aval_index
    assert aval_index < production_index
    assert production_index < flow_index
    assert flow_index < register_index
    assert register_index < build_index


def test_audit_checklist_docx_pp03_conclusion_section_is_between_register_and_build() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    xml = build_document_xml(report)

    assert "Concluzie audit intern" in xml
    conclusion_index = xml.index("Concluzie audit intern")
    register_index = xml.index("Registru documente fizice")
    build_index = xml.index("Informații build", register_index + 1)

    assert conclusion_index > register_index
    assert conclusion_index < build_index
    assert "Raportul sintetizează informațiile identificate" in xml
    assert "nu înlocuiește verificarea documentelor fizice" in xml



def test_audit_checklist_docx_contains_auditor_verdict_card_before_data_quality() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    xml = build_document_xml(report)

    assert xml.index("Card verdict auditor") < xml.index("Sumar Data Quality")
    for expected_text in [
        "Verdict audit",
        "Bilanț PRD vs WMS",
        "AMONTE / produs finit și livrări",
        "AVAL / loturi sursă",
        "Documente fizice",
    ]:
        assert expected_text in xml


def test_audit_checklist_docx_auditor_verdict_card_uses_approved_01e_text() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    xml = build_document_xml(report)

    assert "Cardul verdict sintetizează cazul de audit și indică zonele principale care trebuie citite înaintea verificării documentelor fizice." in xml



def test_audit_checklist_docx_quick_guide_uses_pp03_order_text() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    xml = build_document_xml(report)

    assert "Ghid rapid PP-03: Card verdict, Sumar Data Quality, Rezumat conformare, AMONTE, AVAL, Comenzi producție și consumuri, Fluxuri loturi și documente, Registru documente fizice și Informații build." in xml



def test_audit_checklist_docx_conformity_summary_uses_approved_01e_3_text() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    xml = build_document_xml(report)

    assert "Rezumatul de conformare arată dacă raportul conține informațiile necesare pentru verificarea trasabilității. Observațiile explică limitele datelor sau verificările care trebuie completate manual." in xml



def test_audit_checklist_docx_contains_quick_auditor_guide_points() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    xml = build_document_xml(report)

    assert "Ghid rapid PP-03" in xml
    for guide_item in QUICK_AUDITOR_GUIDE_ITEMS:
        assert guide_item in xml



def test_audit_checklist_docx_document_register_is_printable_checklist() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    xml = build_document_xml(report)

    assert "Coloana Bifat permite folosirea tabelului ca listă de verificare tipărită" in xml
    assert "Bifat" in xml
    assert DOCUMENT_REGISTER_CHECKBOX in xml
    assert "required" in xml



def test_audit_checklist_docx_groups_document_register_by_required_and_recommended() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    policy = AuditReportPolicy()
    selected = policy.select_document_register(report.document_register)
    xml = "".join(build_document_register_section(report, policy))

    expected_rows = [
        [
            DOCUMENT_REGISTER_CHECKBOX,
            line.area,
            line.document_type,
            policy.register_reference(line.document_reference),
            line.related_code,
            line.related_lot,
            policy.delivery(line.related_order),
            policy.register_reason(line.why_needed),
            line.status,
        ]
        for line in selected
    ]
    grouped_rows = [
        [
            DOCUMENT_REGISTER_CHECKBOX,
            line.area,
            line.document_type,
            policy.register_reference(line.document_reference),
            line.related_code,
            line.related_lot,
            policy.delivery(line.related_order),
            policy.register_reason(line.why_needed),
            line.status,
        ]
        for line in selected
        if line.status == "required"
    ] + [
        [
            DOCUMENT_REGISTER_CHECKBOX,
            line.area,
            line.document_type,
            policy.register_reference(line.document_reference),
            line.related_code,
            line.related_lot,
            policy.delivery(line.related_order),
            policy.register_reason(line.why_needed),
            line.status,
        ]
        for line in selected
        if line.status == "recommended"
    ]

    assert "Documente required" in xml
    assert "Documente recommended" in xml
    assert xml.index("Documente required") < xml.index("Documente recommended")
    assert len(grouped_rows) == len(expected_rows)
    assert grouped_rows == expected_rows
    assert xml.count(DOCUMENT_REGISTER_CHECKBOX) == len(selected)
    assert [row[-1] for row in grouped_rows] == [line.status for line in selected]
    assert report.conclusion_status == "PASS"
    assert all(claim not in xml.casefold() for claim in ["done", "release", "production-ready", "daily-use"])



def test_audit_checklist_docx_uses_explicit_checklist_columns() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    xml = build_document_xml(report)

    for upstream_header in [
        "Cantitate recepționată",
        "Dată recepție",
        "Furnizor",
        "Tip document",
        "Număr document",
        "Dată document",
        "Stoc lot sursă",
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
    assert "5000 Kilogram" in xml
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
    assert "Sumar Data Quality" in document_xml
    assert "Rezumat conformare checklist" in document_xml
    assert "00_DATA_QUALITY — verificare surse înainte de raport" in document_xml
    assert "Informații build" in document_xml



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



def test_audit_checklist_docx_downstream_section_mentions_physical_delivery_documents() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    xml = build_document_xml(report)

    assert "Auditorul trebuie să compare aceste rânduri cu documentele fizice de livrare" in xml
    assert "documentele WMS indicate" in xml



def test_audit_checklist_docx_title_block_uses_compact_spacing_after_polish() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    build_info = BuildInfo(
        app_name="TraceAI Control",
        app_version="1.0.0",
        build_commit="abcdef1234567890",
        build_date="build-date",
        build_channel="local",
        generated_at="generated-at",
    )

    xml = "".join(build_title_block(report, build_info))

    assert 'w:spacing w:after="40"' in xml
    assert 'w:spacing w:after="100"' in xml



def test_audit_checklist_docx_document_register_uses_printable_checklist_column_widths() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))

    xml = "".join(build_document_register_section(report, AuditReportPolicy()))

    for width in DOCUMENT_REGISTER_COLUMN_WIDTHS[:3]:
        assert f'w:tcW w:w="{width}" w:type="dxa"' in xml
    assert DOCUMENT_REGISTER_CHECKBOX in xml



def test_audit_checklist_docx_pp03_01a_surfaces_b_fields_more_clearly() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    xml = build_document_xml(report)

    for expected_text in [
        "Cod produs finit",
        "Lot produs finit",
        "Denumire produs finit",
        "Dată producție principală",
        "Cantitate produsă PRD",
        "Stoc produs finit / DSD",
        "Repere rapide produs finit",
        "Tip material",
        "Cod intern",
        "Lot sursă",
        "Materie primă / ambalaj",
        "Cantitate consumată",
        "Stoc lot sursă",
        "Cod intern consum",
    ]:
        assert expected_text in xml



def test_audit_checklist_docx_pp03_01a_does_not_add_banned_pp03_fields() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    xml = build_document_xml(report)

    for banned_text in [
        "Țară",
        "Country",
        "Țara de origine",
        "Country of origin",
        "Received quantity",
    ]:
        assert banned_text not in xml



def test_audit_checklist_docx_pp03_terms_are_not_inverted() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    xml = build_document_xml(report)

    assert "AMONTE — Produs finit, producție și livrări" in xml
    assert "AVAL — Materii prime, ambalaje, auxiliare și loturi sursă" in xml
    assert "03_TABEL_II_AVAL — Livrări produs finit" not in xml
    assert "02_TABEL_I_AMONTE — Materii prime, ambalaje și materiale auxiliare" not in xml
