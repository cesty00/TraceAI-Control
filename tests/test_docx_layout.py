from src.report.docx_layout import (
    NON_SPLITTING_ROW_XML,
    REPEATING_HEADER_ROW_XML,
    TOP_ALIGNED_CELL_XML,
    apply_cell_layout_properties,
    apply_table_layout_properties,
    table_cell_layout_xml,
    table_layout_properties_xml,
    table_row_properties_xml,
)


def test_table_layout_properties_include_width_autofit_and_look() -> None:
    xml = table_layout_properties_xml()

    assert '<w:tblW w:w="5000" w:type="pct"/>' in xml
    assert '<w:tblLayout w:type="autofit"/>' in xml
    assert '<w:tblLook w:firstRow="1"' in xml


def test_table_row_properties_repeat_headers_and_prevent_row_splitting() -> None:
    assert table_row_properties_xml(is_header=True) == REPEATING_HEADER_ROW_XML
    assert table_row_properties_xml(is_header=False) == NON_SPLITTING_ROW_XML
    assert '<w:tblHeader/>' in table_row_properties_xml(is_header=True)
    assert '<w:cantSplit/>' in table_row_properties_xml(is_header=False)


def test_table_cell_layout_aligns_content_to_top() -> None:
    assert table_cell_layout_xml() == TOP_ALIGNED_CELL_XML
    assert '<w:vAlign w:val="top"/>' in table_cell_layout_xml()


def test_apply_layout_properties_are_append_only() -> None:
    assert apply_table_layout_properties('<w:tblStyle w:val="TraceAITable"/>').startswith('<w:tblStyle')
    assert '<w:tblLayout w:type="autofit"/>' in apply_table_layout_properties('<w:tblStyle w:val="TraceAITable"/>')
    assert apply_cell_layout_properties('<w:shd w:fill="EDEDED"/>') == '<w:shd w:fill="EDEDED"/><w:vAlign w:val="top"/>'
