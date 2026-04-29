import zipfile
from pathlib import Path

from samples.demo_docx_runner import main


def read_docx_document_xml(path: Path) -> str:
    with zipfile.ZipFile(path) as package:
        return package.read("word/document.xml").decode("utf-8")


def test_demo_docx_runner_generates_valid_demo_report(tmp_path: Path) -> None:
    output = tmp_path / "demo_traceability_report.docx"

    exit_code = main(["--output", str(output)])
    document_xml = read_docx_document_xml(output)

    assert exit_code == 0
    assert output.exists()
    assert "RAPORT DE TRASABILITATE" in document_xml
    assert "DS0001" in document_xml
    assert "L001" in document_xml
    assert "Tabele operaționale din TraceabilityCase" in document_xml
    assert "Bilanț preliminar" in document_xml
    assert "Linii bilanț preliminar" in document_xml
    assert "Client demo" in document_xml
    assert "CMD-OUT-1" in document_xml
    assert "Total preliminar pe UM" in document_xml
