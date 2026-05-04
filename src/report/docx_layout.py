"""WordprocessingML layout helpers for TraceAI DOCX tables.

These helpers are presentation-only. They do not change audit data, business
rules, quantities or source parsing. They centralize table layout markers used
by Word to render long audit tables more predictably across pages.
"""

from __future__ import annotations

import html
from collections.abc import Iterable

MISSING = "FARA DATE IDENTIFICATE"
TABLE_WIDTH_XML = '<w:tblW w:w="5000" w:type="pct"/>'
TABLE_LAYOUT_XML = '<w:tblLayout w:type="autofit"/>'
TABLE_LOOK_XML = '<w:tblLook w:firstRow="1" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/>'
REPEATING_HEADER_ROW_XML = '<w:trPr><w:tblHeader/></w:trPr>'
NON_SPLITTING_ROW_XML = '<w:trPr><w:cantSplit/></w:trPr>'
TOP_ALIGNED_CELL_XML = '<w:vAlign w:val="top"/>'
COMPACT_TABLE_STYLE_XML = '<w:tblStyle w:val="TraceAITable"/>'
COMPACT_TABLE_BORDERS_XML = '<w:tblBorders><w:top w:val="single" w:sz="4" w:space="0" w:color="808080"/><w:left w:val="single" w:sz="4" w:space="0" w:color="808080"/><w:bottom w:val="single" w:sz="4" w:space="0" w:color="808080"/><w:right w:val="single" w:sz="4" w:space="0" w:color="808080"/><w:insideH w:val="single" w:sz="4" w:space="0" w:color="808080"/><w:insideV w:val="single" w:sz="4" w:space="0" w:color="808080"/></w:tblBorders>'
COMPACT_CELL_MARGINS_XML = '<w:tcMar><w:top w:w="35" w:type="dxa"/><w:left w:w="35" w:type="dxa"/><w:bottom w:w="35" w:type="dxa"/><w:right w:w="35" w:type="dxa"/></w:tcMar>'


def table_layout_properties_xml() -> str:
    """Return table-level layout properties for audit DOCX tables."""

    return TABLE_WIDTH_XML + TABLE_LAYOUT_XML + TABLE_LOOK_XML


def table_row_properties_xml(is_header: bool = False) -> str:
    """Return row properties for header repetition or row integrity."""

    return REPEATING_HEADER_ROW_XML if is_header else NON_SPLITTING_ROW_XML


def table_cell_layout_xml() -> str:
    """Return cell layout properties shared by audit DOCX tables."""

    return TOP_ALIGNED_CELL_XML


def apply_table_layout_properties(table_properties_xml: str) -> str:
    """Append stable layout markers to an existing table properties block."""

    return table_properties_xml + table_layout_properties_xml()


def apply_cell_layout_properties(cell_properties_xml: str) -> str:
    """Append top vertical alignment to an existing cell properties block."""

    return cell_properties_xml + table_cell_layout_xml()


def compact_audit_table(headers: list[str], rows: list[list[object]]) -> str:
    """Render a compact, print-oriented audit table.

    The output keeps the same data values it receives, while applying DOCX layout
    markers for printed audit readability: full width, repeating header row,
    non-splitting body rows, top-aligned cells and compact cell margins.
    """

    xml_rows = [compact_audit_table_row(headers, is_header=True)]
    xml_rows.extend(compact_audit_table_row(row) for row in rows)
    table_properties = apply_table_layout_properties(COMPACT_TABLE_STYLE_XML)
    return f"<w:tbl><w:tblPr>{table_properties}{COMPACT_TABLE_BORDERS_XML}</w:tblPr>{''.join(xml_rows)}</w:tbl>"


def compact_audit_table_row(values: Iterable[object], is_header: bool = False) -> str:
    """Render one compact audit table row."""

    return f"<w:tr>{table_row_properties_xml(is_header)}{''.join(compact_audit_table_cell(value, is_header=is_header) for value in values)}</w:tr>"


def compact_audit_table_cell(value: object, is_header: bool = False) -> str:
    """Render one compact audit table cell."""

    shading_xml = '<w:shd w:fill="EDEDED"/>' if is_header else ""
    bold_xml = "<w:b/>" if is_header else ""
    size = "14" if is_header else "13"
    text = normalize_docx_cell_text(value)
    cell_properties = apply_cell_layout_properties(f"{shading_xml}{COMPACT_CELL_MARGINS_XML}")
    return f"<w:tc><w:tcPr>{cell_properties}</w:tcPr><w:p><w:pPr><w:spacing w:after=\"0\"/></w:pPr><w:r><w:rPr>{bold_xml}<w:sz w:val=\"{size}\"/><w:rFonts w:ascii=\"Arial\" w:hAnsi=\"Arial\"/></w:rPr><w:t>{html.escape(text, quote=False)}</w:t></w:r></w:p></w:tc>"


def normalize_docx_cell_text(value: object) -> str:
    """Return explicit text for a DOCX cell without changing semantic data."""

    if value is None:
        return MISSING
    text = str(value).strip()
    return text or MISSING
