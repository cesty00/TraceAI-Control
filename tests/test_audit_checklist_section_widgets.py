from src.ui.audit_checklist_section_widgets import (
    SectionDisplayModel,
    SectionListItem,
    build_section_display_model,
    build_section_list_items,
    find_section_by_key,
    stringify_display_value,
)
from src.ui.audit_checklist_view_model import AuditChecklistUiSection, AuditChecklistUiViewModel


def test_build_section_list_items_preserves_view_model_order() -> None:
    view_model = make_view_model()

    items = build_section_list_items(view_model)

    assert items == [
        SectionListItem(index=1, key="balance", title="Bilanț", label="01. Bilanț", kind="details"),
        SectionListItem(index=2, key="downstream", title="Livrări", label="02. Livrări", kind="table"),
        SectionListItem(index=3, key="empty", title="Gol", label="03. Gol", kind="empty"),
    ]


def test_find_section_by_key_returns_section_without_reordering() -> None:
    view_model = make_view_model()

    assert find_section_by_key(view_model, "downstream") == view_model.sections[1]
    assert find_section_by_key(view_model, "missing") is None


def test_build_section_display_model_for_details() -> None:
    section = make_view_model().sections[0]

    display = build_section_display_model(section)

    assert display == SectionDisplayModel(
        key="balance",
        title="Bilanț",
        description="Detalii bilanț.",
        kind="details",
        detail_pairs=[("prd_produced", "10 KG"), ("observations", "ok; verificat")],
        summary="2 câmp(uri)",
    )


def test_build_section_display_model_for_table() -> None:
    section = make_view_model().sections[1]

    display = build_section_display_model(section)

    assert display == SectionDisplayModel(
        key="downstream",
        title="Livrări",
        description="Livrări aval.",
        kind="table",
        table_columns=["document", "client"],
        table_rows=[["D1", "C1"], ["D2", "C2"]],
        summary="2 rând(uri)",
    )


def test_build_section_display_model_for_empty_section() -> None:
    section = make_view_model().sections[2]

    display = build_section_display_model(section)

    assert display == SectionDisplayModel(
        key="empty",
        title="Gol",
        description="Fără date.",
        kind="empty",
        summary="FARA DATE IDENTIFICATE",
    )


def test_stringify_display_value_preserves_nested_payload_values_as_text() -> None:
    assert stringify_display_value(None) == ""
    assert stringify_display_value(["a", "b"]) == "a; b"
    assert stringify_display_value({"x": 1, "y": ["a", "b"]}) == "x: 1; y: a; b"


def make_view_model() -> AuditChecklistUiViewModel:
    return AuditChecklistUiViewModel(
        schema_version="audit-checklist-ui.v1",
        subject={"code": "DS0001", "lot": "L001"},
        sections=[
            AuditChecklistUiSection(
                key="balance",
                title="Bilanț",
                description="Detalii bilanț.",
                kind="details",
                data={"prd_produced": "10 KG", "observations": ["ok", "verificat"]},
                field_keys=["prd_produced", "observations"],
            ),
            AuditChecklistUiSection(
                key="downstream",
                title="Livrări",
                description="Livrări aval.",
                kind="table",
                rows=[{"document": "D1", "client": "C1"}, {"document": "D2", "client": "C2"}],
                column_keys=["document", "client"],
            ),
            AuditChecklistUiSection(
                key="empty",
                title="Gol",
                description="Fără date.",
                kind="empty",
            ),
        ],
    )
