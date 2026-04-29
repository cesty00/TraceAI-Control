from src.core.normalized_dataset import NormalizedColumn, NormalizedDataSet, NormalizedRow, NormalizedTable
from src.core.record_selection import select_records_by_code_lot
from src.core.run_pipeline import CorePipelineResult
from src.core.source_inventory import InventoryReport
from src.core.dataset_validation import ValidationReport
from src.rules.case_type_detection import CASE_FINISHED_PRODUCT, detect_case_type
from src.rules.run_rules_pipeline import RulesPipelineResult
from src.rules.traceability_case import build_traceability_case, traceability_case_to_dict


def test_build_traceability_case_maps_rules_pipeline_metadata() -> None:
    table = NormalizedTable(
        source_key="production",
        source_name="rapoarte productie.csv",
        sheet_name=None,
        columns=[NormalizedColumn("cod", "cod"), NormalizedColumn("lot", "lot")],
        rows=[
            NormalizedRow(
                row_number=2,
                values={"cod": "DS0001", "lot": "L001"},
                original_values={"cod": "DS0001", "lot": "L001"},
                code_lot_hints={"code": "DS0001", "lot": "L001"},
            )
        ],
        row_count=1,
    )
    dataset = NormalizedDataSet(source_directory="/tmp/data", tables=[table])
    selection = select_records_by_code_lot(dataset, "DS0001", "L001")
    detection = detect_case_type(dataset, selection, "DS0001", "L001")
    core = CorePipelineResult(
        inventory=InventoryReport(source_directory="/tmp/data", expected_sources=[], sources=[]),
        normalized_dataset=dataset,
        validation=ValidationReport(status="VALID"),
        selection=selection,
    )
    rules = RulesPipelineResult(core=core, case_type_detection=detection)

    traceability_case = traceability_case_to_dict(build_traceability_case(rules, "DS0001", "L001"))

    assert traceability_case["subject"] == {
        "code": "DS0001",
        "lot": "L001",
        "case_type": CASE_FINISHED_PRODUCT,
    }
    assert traceability_case["evidence"]
    assert traceability_case["sections"]["core_validation_status"] == "VALID"
    assert traceability_case["sections"]["selected_record_count"] == 1
