import zipfile
from pathlib import Path

from src.report.docx_minimal import generate_minimal_docx_report
from src.rules.case_type_detection import CASE_FINISHED_PRODUCT, CASE_WMS_ONLY_PRODUCT
from src.rules.traceability_case import (
    TraceabilityCase,
    TraceabilityCaseEvidence,
    TraceabilityCaseSubject,
)


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
        document_xml = package.read("word/document.xml").decode("utf-8")

    assert "RAPORT DE TRASABILITATE" in document_xml
    assert "Rezumat executiv" in document_xml
    assert "Identificarea cazului" in document_xml
    assert "Surse utilizate" in document_xml
    assert "Interpretarea tipului de caz" in document_xml
    assert "Concluzie preliminară" in document_xml
    assert "Recomandare operațională" in document_xml
    assert "Documente de pregătit pentru audit" in document_xml
    assert "Semnături" in document_xml
    assert "DS0001" in document_xml
    assert "L001" in document_xml
    assert CASE_FINISHED_PRODUCT in document_xml
    assert "FARA DATE IDENTIFICATE" in document_xml


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

    with zipfile.ZipFile(output) as package:
        document_xml = package.read("word/document.xml").decode("utf-8")

    assert "WMS-only" in document_xml
    assert "Flux PRD" in document_xml
    assert "Nu au fost identificate înregistrări PRD" in document_xml
