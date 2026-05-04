"""WordprocessingML layout helpers for TraceAI DOCX tables.

These helpers are presentation-only. They do not change audit data, business
rules, quantities or source parsing. They centralize table layout markers used
by Word to render long audit tables more predictably across pages.
"""

from __future__ import annotations

TABLE_WIDTH_XML = '<w:tblW w:w="5000" w:type="pct"/>'
TABLE_LAYOUT_XML = '<w:tblLayout w:type="autofit"/>'
TABLE_LOOK_XML = '<w:tblLook w:firstRow="1" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/>'
REPEATING_HEADER_ROW_XML = '<w:trPr><w:tblHeader/></w:trPr>'
NON_SPLITTING_ROW_XML = '<w:trPr><w:cantSplit/></w:trPr>'
TOP_ALIGNED_CELL_XML = '<w:vAlign w:val="top"/>'


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
