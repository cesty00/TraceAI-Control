from src.core.dataset_validation import validate_normalized_dataset, validation_report_to_dict
from src.core.normalized_dataset import (
    NormalizedColumn,
    NormalizedDataSet,
    NormalizedRow,
    NormalizedTable,
)


def make_valid_dataset() -> NormalizedDataSet:
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
                ],
                rows=[
                    NormalizedRow(
                        row_number=2,
                        values={"cod_articol": "DS0001", "lot": "L001"},
                        original_values={"Cod articol": "DS0001", "Lot": "L001"},
                    )
                ],
                row_count=1,
            )
        ],
    )


def test_validation_report_is_valid_for_structurally_ready_dataset() -> None:
    report = validation_report_to_dict(validate_normalized_dataset(make_valid_dataset()))

    assert report["status"] == "VALID"
    assert report["issues"] == []


def test_validation_report_is_invalid_when_dataset_has_global_errors() -> None:
    dataset = NormalizedDataSet(
        source_directory="/tmp/data",
        tables=[],
        problems=["Lipseste sursa obligatorie: trasabilitate_wms.csv"],
    )

    report = validation_report_to_dict(validate_normalized_dataset(dataset))

    assert report["status"] == "INVALID"
    assert any(issue["severity"] == "ERROR" for issue in report["issues"])


def test_validation_report_warns_for_missing_lot_column_without_invalidating() -> None:
    dataset = NormalizedDataSet(
        source_directory="/tmp/data",
        tables=[
            NormalizedTable(
                source_key="nomenclator",
                source_name="nomenclator.xlsx",
                sheet_name="Articole",
                columns=[NormalizedColumn("Cod", "cod")],
                rows=[],
                row_count=0,
            )
        ],
    )

    report = validation_report_to_dict(validate_normalized_dataset(dataset))

    assert report["status"] == "VALID"
    assert any(issue["severity"] == "WARNING" for issue in report["issues"])
    assert any("lot" in issue["message"].lower() for issue in report["issues"])
