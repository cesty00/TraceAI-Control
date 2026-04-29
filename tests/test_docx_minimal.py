import zipfile
from pathlib import Path

from src.report.docx_minimal import generate_minimal_docx_report
from src.rules.case_type_detection import CASE_FINISHED_PRODUCT, CASE_WMS_ONLY_PRODUCT
from src.rules.traceability_case import (
    TraceabilityBalanceLine,
    TraceabilityCase,
    TraceabilityCaseEvidence,
    TraceabilityCaseSubject,
    TraceabilityPreliminaryBalance,
    TraceabilityReportTable,
    TraceabilityReportTables,
    TraceabilityTableRow,
    build_empty_report_tables,
)


def read_document_xml(path: Path) -> str:
    with zipfile.ZipFile(path) as package:
        return package.read("word/document.xml").decode("utf-8")


def test_generate_minimal_docx_report_creates_valid_docx_package(tmp_path: Path) -> None:
    traceability_case = TraceabilityCase(
        subject=TraceabilityCaseSubject(
            code="DS0001",
            lot="L001",
            case_type=CASE_FINISHED_PRODUCT,
        ),
        evidence=[
            TraceabilityCaseEvidence(
                source_key="production",
                source_name="rapoarte productie.csv",
                sheet_name=None,
                row_number=2,
                message="Caz detectat din productie.",
            )
        ],
        observations=[],
        sections={"core_validation_status": "VALID"},
    )

    output = generate_minimal_docx_report(traceability_case, tmp_path / "raport.docx")

    assert output.exists()
    assert output.suffix == ".docx"

    with zipfile.ZipFile(output) as package:
        names = set(package.namelist())
        assert "[Content_Types].xml" in names
        assert "_rels/.rels" in names
        assert "word/document.xml" in names
        assert "word/styles.xml" in names
        assert "word/header1.xml" in names
        assert "word/footer1.xml" in names
        assert "word/_rels/document.xml.rels" in names
        document_xml = package.read("word/document.xml").decode("utf-8")
        relationships_xml = package.read("word/_rels/document.xml.rels").decode("utf-8")
        header_xml = package.read("word/header1.xml").decode("utf-8")
        footer_xml = package.read("word/footer1.xml").decode("utf-8")
        styles_xml = package.read("word/styles.xml").decode("utf-8")

    assert "RAPORT DE TRASABILITATE" in document_xml
    assert "Metadate raport" in document_xml
    assert "Rezumat executiv" in document_xml
    assert "Identificarea cazului" in document_xml
    assert "Surse utilizate" in document_xml
    assert "Interpretarea tipului de caz" in document_xml
    assert "Tabele operaționale din TraceabilityCase" in document_xml
    assert "Bilanț preliminar" in document_xml
    assert "Linii bilanț preliminar" in document_xml
    assert "Nu există linii de bilanț preliminar calculate" in document_xml
    assert "Producția lotului" in document_xml
    assert "Nu au fost identificate date detaliate de producție" in document_xml
    assert "Concluzie preliminară" in document_xml
    assert "Recomandare operațională" in document_xml
    assert "Documente de pregătit pentru audit" in document_xml
    assert "Semnături" in document_xml
    assert "DS0001" in document_xml
    assert "L001" in document_xml
    assert CASE_FINISHED_PRODUCT in document_xml
    assert "FARA DATE IDENTIFICATE" in document_xml
    assert "<w:tbl>" in document_xml
    assert "<w:tblStyle w:val=\"TraceAITable\"/>" in document_xml
    assert "<w:gridSpan" in document_xml
    assert "rIdHeader1" in document_xml
    assert "rIdFooter1" in document_xml
    assert "Target=\"styles.xml\"" in relationships_xml
    assert "Target=\"header1.xml\"" in relationships_xml
    assert "Target=\"footer1.xml\"" in relationships_xml
    assert "TraceAI Control — Raport de trasabilitate" in header_xml
    assert "Document generat din TraceabilityCase" in footer_xml
    assert "TraceAITable" in styles_xml


def test_generate_minimal_docx_report_contains_wms_only_narrative(tmp_path: Path) -> None:
    traceability_case = TraceabilityCase(
        subject=TraceabilityCaseSubject(
            code="DS0002",
            lot="L002",
            case_type=CASE_WMS_ONLY_PRODUCT,
        ),
        evidence=[],
        observations=["Nu au fost identificate înregistrări PRD pentru acest articol și lot."],
        sections={"core_validation_status": "VALID", "selected_record_count": 0},
    )

    output = generate_minimal_docx_report(traceability_case, tmp_path / "raport_wms.docx")
    document_xml = read_document_xml(output)

    assert "WMS-only" in document_xml
    assert "Flux PRD" in document_xml
    assert "Nu au fost identificate înregistrări PRD" in document_xml


def test_generate_minimal_docx_report_renders_table_rows_from_traceability_case(tmp_path: Path) -> None:
    tables = build_empty_report_tables()
    production_table = TraceabilityReportTable(
        key="production",
        title="Producția lotului",
        columns=["Cod", "Lot", "Comandă", "Cantitate", "UM", "Observații"],
        rows=[
            TraceabilityTableRow(
                values={
                    "Cod": "DS0001",
                    "Lot": "L001",
                    "Comandă": "CMD-1",
                    "Cantitate": "10",
                    "UM": "kg",
                    "Observații": "test",
                },
                source_key="production",
                source_name="rapoarte productie.csv",
                sheet_name=None,
                row_number=2,
            )
        ],
        empty_message="Nu au fost identificate date detaliate de producție în TraceabilityCase.",
    )
    report_tables = TraceabilityReportTables(
        production=production_table,
        finished_goods_deliveries=tables.finished_goods_deliveries,
        raw_materials=tables.raw_materials,
        packaging=tables.packaging,
        auxiliaries_gas=tables.auxiliaries_gas,
        wms_receipts=tables.wms_receipts,
        prd_consumptions=tables.prd_consumptions,
        stock=tables.stock,
    )
    traceability_case = TraceabilityCase(
        subject=TraceabilityCaseSubject("DS0001", "L001", CASE_FINISHED_PRODUCT),
        report_tables=report_tables,
    )

    output = generate_minimal_docx_report(traceability_case, tmp_path / "raport_tabele.docx")
    document_xml = read_document_xml(output)

    assert "<w:tbl>" in document_xml
    assert "<w:tr>" in document_xml
    assert "<w:tc>" in document_xml
    assert "CMD-1" in document_xml
    assert "10" in document_xml
    assert "Sursă: production / rapoarte productie.csv" in document_xml
    assert "Nu au fost identificate livrări produs finit" in document_xml


def test_generate_minimal_docx_report_renders_preliminary_balance_lines(tmp_path: Path) -> None:
    traceability_case = TraceabilityCase(
        subject=TraceabilityCaseSubject("DS0001", "L001", CASE_FINISHED_PRODUCT),
        preliminary_balance=TraceabilityPreliminaryBalance(
            messages=[
                "Bilanț preliminar calculat doar din TraceabilityCase.report_tables.",
                "Unitățile de măsură sunt grupate separat; nu se fac conversii automate.",
            ],
            lines=[
                TraceabilityBalanceLine(
                    table_key="production",
                    table_title="Producția lotului",
                    quantity_column="Cantitate",
                    unit="kg",
                    total="12.5",
                    source_row_count=2,
                    skipped_row_count=1,
                    message="Total preliminar pe UM, fără conversie automată.",
                )
            ],
        ),
    )

    output = generate_minimal_docx_report(traceability_case, tmp_path / "raport_bilant.docx")
    document_xml = read_document_xml(output)

    assert "Bilanț preliminar" in document_xml
    assert "Mesaje bilanț" in document_xml
    assert "Linii bilanț preliminar" in document_xml
    assert "Bilanț preliminar calculat doar din TraceabilityCase.report_tables" in document_xml
    assert "Unitățile de măsură sunt grupate separat" in document_xml
    assert "Producția lotului" in document_xml
    assert "Cantitate" in document_xml
    assert "kg" in document_xml
    assert "12.5" in document_xml
    assert "Total preliminar pe UM" in document_xml
