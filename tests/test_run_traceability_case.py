import csv
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

import pytest

from src.errors import (
    AmbiguousCaseTypeError,
    DataQualityBlockingError,
    MissingRequiredColumnError,
    MissingSourceFileError,
    NoMatchingRecordsError,
)
from src.rules.case_type_detection import CASE_FINISHED_PRODUCT
from src.rules.run_traceability_case import run_traceability_case
from src.rules.traceability_case import traceability_case_to_dict


def write_csv(path: Path, headers: list[str], row: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerow(row)


def write_minimal_xlsx(path: Path, sheet_name: str, headers: list[str], row: list[str]) -> None:
    header_cells = "".join(
        f'<c r="{chr(65 + index)}1" t="inlineStr"><is><t>{escape(header)}</t></is></c>'
        for index, header in enumerate(headers)
    )
    row_cells = "".join(
        f'<c r="{chr(65 + index)}2" t="inlineStr"><is><t>{escape(value)}</t></is></c>'
        for index, value in enumerate(row)
    )
    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData><row r="1">{header_cells}</row><row r="2">{row_cells}</row></sheetData>'
        '</worksheet>'
    )

    with zipfile.ZipFile(path, "w") as workbook:
        workbook.writestr("[Content_Types].xml", "")
        workbook.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f'<sheets><sheet name="{escape(sheet_name)}" sheetId="1" r:id="rId1"/></sheets>'
            '</workbook>',
        )
        workbook.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            'Target="worksheets/sheet1.xml"/>'
            '</Relationships>',
        )
        workbook.writestr("xl/worksheets/sheet1.xml", sheet_xml)


def write_valid_minimal_sources(root: Path) -> None:
    write_csv(
        root / "trasabilitate_wms.csv",
        ["Cod articol", "Lot", "Cantitate", "UM"],
        ["DS0001", "L001", "10", "kg"],
    )
    write_csv(
        root / "rapoarte productie.csv",
        ["Cod produs", "Lot produs", "Cantitate produsa"],
        ["DS0001", "L001", "10"],
    )
    write_minimal_xlsx(
        root / "nomenclator.xlsx",
        "Articole",
        ["Cod", "Lot", "Denumire"],
        ["DS0001", "L001", "Produs test"],
    )
    write_minimal_xlsx(
        root / "stoc la moment original.xlsx",
        "Stoc",
        ["Cod articol", "Lot", "Stoc", "UM"],
        ["DS0001", "L001", "5", "kg"],
    )


def test_run_traceability_case_returns_minimal_case(tmp_path: Path) -> None:
    write_valid_minimal_sources(tmp_path)

    traceability_case = traceability_case_to_dict(run_traceability_case(tmp_path, "DS0001", "L001"))

    assert traceability_case["subject"] == {
        "code": "DS0001",
        "lot": "L001",
        "case_type": CASE_FINISHED_PRODUCT,
    }
    assert traceability_case["evidence"]
    assert traceability_case["sections"]["core_validation_status"] == "VALID"


def test_run_traceability_case_raises_missing_source_file_error_when_no_sources_found(tmp_path: Path) -> None:
    with pytest.raises(MissingSourceFileError) as exc_info:
        run_traceability_case(tmp_path, "DS0001", "L001")

    assert "nu am găsit sursele oficiale" in exc_info.value.user_message.casefold()
    assert "trasabilitate_wms.csv" in (exc_info.value.technical_detail or "")


def test_run_traceability_case_raises_missing_required_column_error_for_blocking_structure(tmp_path: Path) -> None:
    write_csv(
        tmp_path / "trasabilitate_wms.csv",
        ["Cod articol", "Cantitate", "UM"],
        ["DS0001", "10", "kg"],
    )
    write_csv(
        tmp_path / "rapoarte productie.csv",
        ["Cod produs", "Cantitate produsa"],
        ["DS0001", "10"],
    )
    write_minimal_xlsx(
        tmp_path / "nomenclator.xlsx",
        "Articole",
        ["Cod", "Denumire"],
        ["DS0001", "Produs test"],
    )
    write_minimal_xlsx(
        tmp_path / "stoc la moment original.xlsx",
        "Stoc",
        ["Cod articol", "Stoc", "UM"],
        ["DS0001", "5", "kg"],
    )

    with pytest.raises(MissingRequiredColumnError) as exc_info:
        run_traceability_case(tmp_path, "DS0001", "L001")

    assert "coloanele obligatorii" in exc_info.value.user_message.casefold()
    assert "lot" in (exc_info.value.technical_detail or "").casefold()


def test_run_traceability_case_raises_no_matching_records_error_when_case_is_missing(tmp_path: Path) -> None:
    write_valid_minimal_sources(tmp_path)

    with pytest.raises(NoMatchingRecordsError) as exc_info:
        run_traceability_case(tmp_path, "DS9999", "L999")

    assert "nu am găsit date" in exc_info.value.user_message.casefold()
    assert "DS9999" in (exc_info.value.technical_detail or "")


def test_run_traceability_case_raises_ambiguous_case_type_error_when_records_exist_but_classification_stays_unknown(tmp_path: Path) -> None:
    write_minimal_xlsx(
        tmp_path / "nomenclator.xlsx",
        "Articole",
        ["Cod", "Lot", "Denumire"],
        ["DS0001", "L001", "Produs test neclasificat"],
    )

    with pytest.raises(AmbiguousCaseTypeError) as exc_info:
        run_traceability_case(tmp_path, "DS0001", "L001")

    assert "nu poate fi clasificat" in exc_info.value.user_message.casefold()
    assert "DS0001" in (exc_info.value.technical_detail or "")
    assert "L001" in (exc_info.value.technical_detail or "")
    assert "produs finit" in (exc_info.value.recommended_action or "").casefold()


def test_run_traceability_case_raises_data_quality_blocking_error_for_unreadable_official_source(
    tmp_path: Path,
) -> None:
    write_csv(
        tmp_path / "trasabilitate_wms.csv",
        ["Cod articol", "Lot", "Cantitate", "UM"],
        ["DS9999", "L999", "10", "kg"],
    )
    write_csv(
        tmp_path / "rapoarte productie.csv",
        ["Cod produs", "Lot produs", "Cantitate produsa"],
        ["DS9999", "L999", "10"],
    )
    write_minimal_xlsx(
        tmp_path / "nomenclator.xlsx",
        "Articole",
        ["Cod", "Lot", "Denumire"],
        ["DS9999", "L999", "Produs test"],
    )
    (tmp_path / "stoc la moment original.xlsx").write_bytes(b"not-a-zip")

    with pytest.raises(DataQualityBlockingError) as exc_info:
        run_traceability_case(tmp_path, "DS0001", "L001")

    assert "nu pot fi citite" in exc_info.value.user_message.casefold()
    assert "stoc la moment original.xlsx" in (exc_info.value.technical_detail or "")
    assert "corupt" in (exc_info.value.technical_detail or "").casefold()
