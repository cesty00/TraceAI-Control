from src.report.docx_layout import (
    NON_SPLITTING_ROW_XML,
    REPEATING_HEADER_ROW_XML,
    TOP_ALIGNED_CELL_XML,
    apply_cell_layout_properties,
    apply_table_layout_properties,
    compact_audit_table,
    normalize_docx_cell_text,
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


def test_compact_audit_table_contains_print_layout_markers() -> None:
    xml = compact_audit_table(["Col A", "Col B"], [["value", "other"], [None, ""]])

    assert '<w:tblW w:w="5000" w:type="pct"/>' in xml
    assert '<w:tblLayout w:type="autofit"/>' in xml
    assert '<w:tblLook w:firstRow="1"' in xml
    assert '<w:tblHeader/>' in xml
    assert '<w:cantSplit/>' in xml
    assert '<w:vAlign w:val="top"/>' in xml
    assert '<w:sz w:val="14"/>' in xml
    assert '<w:sz w:val="13"/>' in xml
    assert 'FARA DATE IDENTIFICATE' in xml


def test_compact_audit_table_escapes_cell_text() -> None:
    xml = compact_audit_table(["A&B"], [["<lot>"]])

    assert "A&amp;B" in xml
    assert "&lt;lot&gt;" in xml


def test_normalize_docx_cell_text_keeps_missing_explicit() -> None:
    assert normalize_docx_cell_text(None) == "FARA DATE IDENTIFICATE"
    assert normalize_docx_cell_text("") == "FARA DATE IDENTIFICATE"
    assert normalize_docx_cell_text("  abc  ") == "abc"
