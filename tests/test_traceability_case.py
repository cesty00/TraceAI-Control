from src.core.dataset_validation import ValidationReport
from src.core.normalized_dataset import NormalizedColumn, NormalizedDataSet, NormalizedRow, NormalizedTable
from src.core.record_selection import select_records_by_code_lot
from src.core.run_pipeline import CorePipelineResult
from src.core.source_inventory import InventoryReport
from src.rules.case_type_detection import CASE_FINISHED_PRODUCT, detect_case_type
from src.rules.run_rules_pipeline import RulesPipelineResult
from src.rules.traceability_case import (
    ALISOL_AUXILIARY_OBSERVATION,
    build_empty_report_tables,
    build_traceability_case,
    report_tables_as_list,
    traceability_case_to_dict,
)


def make_table(source_key: str, source_name: str, values: dict[str, str]) -> NormalizedTable:
    return NormalizedTable(
        source_key=source_key,
        source_name=source_name,
        sheet_name=None,
        columns=[NormalizedColumn(name, name) for name in values.keys()],
        rows=[
            NormalizedRow(
                row_number=2,
                values=values,
                original_values=values,
                code_lot_hints={"code": values.get("cod", ""), "lot": values.get("lot", "")},
            )
        ],
        row_count=1,
    )


def make_rules_result(tables: list[NormalizedTable]) -> RulesPipelineResult:
    dataset = NormalizedDataSet(source_directory="/tmp/data", tables=tables)
    selection = select_records_by_code_lot(dataset, "DS0001", "L001")
    detection = detect_case_type(dataset, selection, "DS0001", "L001")
    core = CorePipelineResult(
        inventory=InventoryReport(source_directory="/tmp/data", expected_sources=[], sources=[]),
        normalized_dataset=dataset,
        validation=ValidationReport(status="VALID"),
        selection=selection,
    )
    return RulesPipelineResult(core=core, case_type_detection=detection)


def test_build_traceability_case_maps_rules_pipeline_metadata() -> None:
    rules = make_rules_result(
        [make_table("production", "rapoarte productie.csv", {"cod": "DS0001", "lot": "L001"})]
    )

    traceability_case = traceability_case_to_dict(build_traceability_case(rules, "DS0001", "L001"))

    assert traceability_case["subject"] == {
        "code": "DS0001",
        "lot": "L001",
        "case_type": CASE_FINISHED_PRODUCT,
    }
    assert traceability_case["evidence"]
    assert traceability_case["sections"]["core_validation_status"] == "VALID"
    assert traceability_case["sections"]["selected_record_count"] == 1
    assert traceability_case["report_tables"]["production"]["title"] == "Producția lotului"
    assert traceability_case["report_tables"]["stock"]["empty_message"]


def test_build_empty_report_tables_contains_expected_sections_in_display_order() -> None:
    tables = report_tables_as_list(build_empty_report_tables())

    assert [table.key for table in tables] == [
        "production",
        "finished_goods_deliveries",
        "raw_materials",
        "packaging",
        "auxiliaries_gas",
        "wms_receipts",
        "prd_consumptions",
        "stock",
    ]
    assert all(table.columns for table in tables)
    assert all(table.empty_message for table in tables)
    assert all(table.rows == [] for table in tables)


def test_build_traceability_case_populates_selected_report_tables() -> None:
    rules = make_rules_result(
        [
            make_table(
                "production",
                "rapoarte productie.csv",
                {"cod": "DS0001", "lot": "L001", "cantitate": "10", "um": "kg"},
            ),
            make_table(
                "wms",
                "trasabilitate_wms.csv",
                {"cod": "DS0001", "lot": "L001", "document intrare": "NIR-1", "cantitate": "10"},
            ),
            make_table(
                "stock",
                "stoc la moment original.xlsx",
                {"cod": "DS0001", "lot": "L001", "stoc": "5", "um": "kg"},
            ),
        ]
    )

    traceability_case = traceability_case_to_dict(build_traceability_case(rules, "DS0001", "L001"))

    production_rows = traceability_case["report_tables"]["production"]["rows"]
    wms_rows = traceability_case["report_tables"]["wms_receipts"]["rows"]
    stock_rows = traceability_case["report_tables"]["stock"]["rows"]

    assert production_rows[0]["values"]["cantitate"] == "10"
    assert production_rows[0]["source_key"] == "production"
    assert wms_rows[0]["values"]["document intrare"] == "NIR-1"
    assert wms_rows[0]["source_key"] == "wms"
    assert stock_rows[0]["values"]["stoc"] == "5"
    assert stock_rows[0]["source_key"] == "stock"
    assert traceability_case["report_tables"]["raw_materials"]["rows"] == []


def test_alisol_is_classified_as_auxiliary_gas_not_raw_material() -> None:
    rules = make_rules_result(
        [
            make_table(
                "production",
                "rapoarte productie.csv",
                {"cod": "DS0001", "lot": "L001", "denumire": "Gaz ALISOL", "cantitate": "2", "um": "kg"},
            )
        ]
    )

    traceability_case = traceability_case_to_dict(build_traceability_case(rules, "DS0001", "L001"))

    auxiliary_rows = traceability_case["report_tables"]["auxiliaries_gas"]["rows"]
    raw_material_rows = traceability_case["report_tables"]["raw_materials"]["rows"]
    production_rows = traceability_case["report_tables"]["production"]["rows"]

    assert auxiliary_rows[0]["values"]["denumire"] == "Gaz ALISOL"
    assert auxiliary_rows[0]["values"]["Observații"] == ALISOL_AUXILIARY_OBSERVATION
    assert raw_material_rows == []
    assert production_rows == []
    assert ALISOL_AUXILIARY_OBSERVATION in traceability_case["observations"]
