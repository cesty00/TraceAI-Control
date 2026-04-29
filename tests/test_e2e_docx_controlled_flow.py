import zipfile
from pathlib import Path

from src.core.dataset_validation import ValidationReport
from src.core.normalized_dataset import NormalizedColumn, NormalizedDataSet, NormalizedRow, NormalizedTable
from src.core.record_selection import select_records_by_code_lot
from src.core.run_pipeline import CorePipelineResult
from src.core.source_inventory import InventoryReport
from src.report.docx_minimal import generate_minimal_docx_report
from src.rules.case_type_detection import CASE_FINISHED_PRODUCT, detect_case_type
from src.rules.run_rules_pipeline import RulesPipelineResult
from src.rules.traceability_case import build_traceability_case, traceability_case_to_dict


def make_normalized_table(source_key: str, source_name: str, rows: list[dict[str, str]]) -> NormalizedTable:
    columns = sorted({column for row in rows for column in row.keys()})
    return NormalizedTable(
        source_key=source_key,
        source_name=source_name,
        sheet_name=None,
        columns=[NormalizedColumn(name, name) for name in columns],
        rows=[
            NormalizedRow(
                row_number=index + 2,
                values=row,
                original_values=row,
                code_lot_hints={"code": row.get("cod", ""), "lot": row.get("lot", "")},
            )
            for index, row in enumerate(rows)
        ],
        row_count=len(rows),
    )


def read_docx_document_xml(path: Path) -> str:
    with zipfile.ZipFile(path) as package:
        return package.read("word/document.xml").decode("utf-8")


def test_e2e_controlled_traceability_case_to_docx(tmp_path: Path) -> None:
    dataset = NormalizedDataSet(
        source_directory="/tmp/traceai-controlled-e2e",
        tables=[
            make_normalized_table(
                "production",
                "rapoarte productie.csv",
                [
                    {"cod": "DS0001", "lot": "L001", "comandă": "PRD-1", "cantitate": "10", "um": "kg"},
                    {"cod": "DS0001", "lot": "L001", "denumire": "Materie primă zahăr", "cantitate": "2", "um": "kg"},
                    {"cod": "DS0001", "lot": "L001", "denumire": "Folie ambalaj", "cantitate": "5", "um": "buc"},
                ],
            ),
            make_normalized_table(
                "wms",
                "trasabilitate_wms.csv",
                [
                    {
                        "cod": "DS0001",
                        "lot": "L001",
                        "document comanda": "CMD-OUT-1",
                        "client": "Client test",
                        "cantitate": "4",
                        "um": "kg",
                    }
                ],
            ),
            make_normalized_table(
                "stock",
                "stoc la moment original.xlsx",
                [{"cod": "DS0001", "lot": "L001", "stoc": "6", "um": "kg", "locație": "DEP-1"}],
            ),
        ],
    )
    selection = select_records_by_code_lot(dataset, "DS0001", "L001")
    detection = detect_case_type(dataset, selection, "DS0001", "L001")
    core = CorePipelineResult(
        inventory=InventoryReport(source_directory="/tmp/traceai-controlled-e2e", expected_sources=[], sources=[]),
        normalized_dataset=dataset,
        validation=ValidationReport(status="VALID"),
        selection=selection,
    )
    rules = RulesPipelineResult(core=core, case_type_detection=detection)

    traceability_case = build_traceability_case(rules, "DS0001", "L001")
    traceability_case_dict = traceability_case_to_dict(traceability_case)

    assert traceability_case.subject.case_type == CASE_FINISHED_PRODUCT
    assert traceability_case_dict["report_tables"]["production"]["rows"]
    assert traceability_case_dict["report_tables"]["finished_goods_deliveries"]["rows"]
    assert traceability_case_dict["report_tables"]["raw_materials"]["rows"]
    assert traceability_case_dict["report_tables"]["packaging"]["rows"]
    assert traceability_case_dict["report_tables"]["stock"]["rows"]
    assert traceability_case_dict["preliminary_balance"]["lines"]

    output = generate_minimal_docx_report(traceability_case, tmp_path / "traceai_controlled_e2e.docx")
    document_xml = read_docx_document_xml(output)

    assert output.exists()
    assert "RAPORT DE TRASABILITATE" in document_xml
    assert "DS0001" in document_xml
    assert "L001" in document_xml
    assert "Tabele operaționale din TraceabilityCase" in document_xml
    assert "Producția lotului" in document_xml
    assert "Livrări produs finit" in document_xml
    assert "Materii prime alimentare" in document_xml
    assert "Ambalaje" in document_xml
    assert "Stoc la moment" in document_xml
    assert "Bilanț preliminar" in document_xml
    assert "Linii bilanț preliminar" in document_xml
    assert "CMD-OUT-1" in document_xml
    assert "Client test" in document_xml
    assert "Total preliminar pe UM" in document_xml
