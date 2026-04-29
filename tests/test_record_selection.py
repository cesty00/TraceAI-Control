from src.core.normalized_dataset import (
    NormalizedColumn,
    NormalizedDataSet,
    NormalizedRow,
    NormalizedTable,
)
from src.core.record_selection import select_records_by_code_lot, selection_result_to_dict


def make_dataset() -> NormalizedDataSet:
    return NormalizedDataSet(
        source_directory="/tmp/data",
        tables=[
            NormalizedTable(
                source_key="wms",
                source_name="trasabilitate_wms.csv",
                sheet_name=None,
                columns=[
                    NormalizedColumn("Cod articol", "cod_articol"),
                    NormalizedColumn("Lot", "lot"),
                    NormalizedColumn("Cantitate", "cantitate"),
                ],
                rows=[
                    NormalizedRow(
                        row_number=2,
                        values={"cod_articol": "DS0001", "lot": "L001", "cantitate": "10"},
                        original_values={"Cod articol": "DS0001", "Lot": "L001", "Cantitate": "10"},
                        quantity_values={"cantitate": "10"},
                        code_lot_hints={"code": "DS0001", "lot": "L001"},
                    ),
                    NormalizedRow(
                        row_number=3,
                        values={"cod_articol": "DS0002", "lot": "L002", "cantitate": "5"},
                        original_values={"Cod articol": "DS0002", "Lot": "L002", "Cantitate": "5"},
                        quantity_values={"cantitate": "5"},
                        code_lot_hints={"code": "DS0002", "lot": "L002"},
                    ),
                ],
                row_count=2,
            )
        ],
    )


def test_select_records_by_code_lot_returns_matching_record_context() -> None:
    result = selection_result_to_dict(select_records_by_code_lot(make_dataset(), "DS0001", "L001"))

    assert result["warnings"] == []
    assert len(result["records"]) == 1
    record = result["records"][0]
    assert record["source_key"] == "wms"
    assert record["source_name"] == "trasabilitate_wms.csv"
    assert record["row_number"] == 2
    assert record["code"] == "DS0001"
    assert record["lot"] == "L001"
    assert record["quantity_values"] == {"cantitate": "10"}


def test_select_records_by_code_lot_normalizes_input_spacing_and_case() -> None:
    result = selection_result_to_dict(select_records_by_code_lot(make_dataset(), " ds0001 ", " l001 "))

    assert len(result["records"]) == 1


def test_select_records_by_code_lot_warns_when_no_records_found() -> None:
    result = selection_result_to_dict(select_records_by_code_lot(make_dataset(), "DS9999", "L999"))

    assert result["records"] == []
    assert result["warnings"] == ["Nu au fost gasite randuri pentru codul si lotul cautate."]


def test_select_records_by_code_lot_warns_on_empty_input() -> None:
    result = selection_result_to_dict(select_records_by_code_lot(make_dataset(), "", ""))

    assert result["records"] == []
    assert "Codul de cautare este gol." in result["warnings"]
    assert "Lotul de cautare este gol." in result["warnings"]
