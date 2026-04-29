from src.core.normalized_dataset import NormalizedDataSet, NormalizedTable, NormalizedColumn, NormalizedRow
from src.core.record_selection import select_records_by_code_lot
from src.rules.case_type_detection import (
    CASE_FINISHED_PRODUCT,
    CASE_RAW_MATERIAL,
    CASE_UNKNOWN,
    CASE_WMS_ONLY_PRODUCT,
    case_type_result_to_dict,
    detect_case_type,
)


def make_table(source_key: str, source_name: str, row_values: dict[str, str]) -> NormalizedTable:
    columns = [NormalizedColumn(name, name) for name in row_values.keys()]
    row = NormalizedRow(
        row_number=2,
        values=row_values,
        original_values=row_values,
        code_lot_hints={"code": row_values.get("cod", ""), "lot": row_values.get("lot", "")},
    )
    return NormalizedTable(
        source_key=source_key,
        source_name=source_name,
        sheet_name=None,
        columns=columns,
        rows=[row],
        row_count=1,
    )


def detect(dataset: NormalizedDataSet, code: str = "DS0001", lot: str = "L001") -> dict:
    selection = select_records_by_code_lot(dataset, code, lot)
    return case_type_result_to_dict(detect_case_type(dataset, selection, code, lot))


def test_detects_finished_product_when_production_has_code_and_lot() -> None:
    dataset = NormalizedDataSet(
        source_directory="/tmp/data",
        tables=[make_table("production", "rapoarte productie.csv", {"cod": "DS0001", "lot": "L001"})],
    )

    result = detect(dataset)

    assert result["case_type"] == CASE_FINISHED_PRODUCT
    assert result["evidence"][0]["source_key"] == "production"


def test_detects_raw_material_from_nomenclator_classification() -> None:
    dataset = NormalizedDataSet(
        source_directory="/tmp/data",
        tables=[make_table("nomenclator", "nomenclator.xlsx", {"cod": "DS0001", "lot": "L001", "clasa": "materie prima"})],
    )

    result = detect(dataset)

    assert result["case_type"] == CASE_RAW_MATERIAL
    assert result["evidence"][0]["source_key"] == "nomenclator"


def test_detects_wms_only_when_wms_has_record_without_production() -> None:
    dataset = NormalizedDataSet(
        source_directory="/tmp/data",
        tables=[make_table("wms", "trasabilitate_wms.csv", {"cod": "DS0001", "lot": "L001"})],
    )

    result = detect(dataset)

    assert result["case_type"] == CASE_WMS_ONLY_PRODUCT
    assert result["evidence"][0]["source_key"] == "wms"


def test_detects_unknown_when_no_records_match() -> None:
    dataset = NormalizedDataSet(source_directory="/tmp/data", tables=[])

    result = detect(dataset)

    assert result["case_type"] == CASE_UNKNOWN
    assert result["evidence"] == []
    assert result["observations"]
