"""Display helpers for dedicated audit checklist UI sections.

The helpers in this module are pure presentation mapping. They consume
``AuditChecklistUiViewModel`` / ``AuditChecklistUiSection`` objects and produce
labels, table columns and detail pairs that a visual toolkit can render.

No traceability business rules, file parsing, calculations or unit conversions
belong here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.ui.audit_checklist_view_model import AuditChecklistUiSection, AuditChecklistUiViewModel


@dataclass(frozen=True)
class SectionListItem:
    """One item displayed in the visual section navigation list."""

    index: int
    key: str
    title: str
    label: str
    kind: str


@dataclass(frozen=True)
class SectionDisplayModel:
    """Render-ready data for the selected audit checklist section."""

    key: str
    title: str
    description: str
    kind: str
    detail_pairs: list[tuple[str, str]] = field(default_factory=list)
    table_columns: list[str] = field(default_factory=list)
    table_rows: list[list[str]] = field(default_factory=list)
    summary: str = ""
    empty_message: str = "FARA DATE IDENTIFICATE"


def build_section_list_items(view_model: AuditChecklistUiViewModel) -> list[SectionListItem]:
    """Build navigation items in the exact order supplied by the view model."""

    return [
        SectionListItem(
            index=index,
            key=section.key,
            title=section.title,
            label=f"{index:02d}. {section.title}",
            kind=section.kind,
        )
        for index, section in enumerate(view_model.sections, start=1)
    ]


def find_section_by_key(view_model: AuditChecklistUiViewModel, key: str) -> AuditChecklistUiSection | None:
    """Return a section by key without changing order or content."""

    for section in view_model.sections:
        if section.key == key:
            return section
    return None


def build_section_display_model(section: AuditChecklistUiSection) -> SectionDisplayModel:
    """Build the selected-section display model for the visual UI."""

    if section.kind == "details":
        detail_pairs = [(field_key, stringify_display_value(section.data.get(field_key, ""))) for field_key in section.field_keys]
        return SectionDisplayModel(
            key=section.key,
            title=section.title,
            description=section.description,
            kind=section.kind,
            detail_pairs=detail_pairs,
            summary=build_detail_summary(detail_pairs, section.empty_message),
            empty_message=section.empty_message,
        )

    if section.kind == "table":
        table_rows = [[stringify_display_value(row.get(column, "")) for column in section.column_keys] for row in section.rows]
        return SectionDisplayModel(
            key=section.key,
            title=section.title,
            description=section.description,
            kind=section.kind,
            table_columns=list(section.column_keys),
            table_rows=table_rows,
            summary=build_table_summary(section.rows, section.empty_message),
            empty_message=section.empty_message,
        )

    return SectionDisplayModel(
        key=section.key,
        title=section.title,
        description=section.description,
        kind=section.kind,
        summary=section.empty_message,
        empty_message=section.empty_message,
    )


def build_detail_summary(detail_pairs: list[tuple[str, str]], empty_message: str) -> str:
    """Summarize a detail section for the visual UI."""

    if not detail_pairs:
        return empty_message
    return f"{len(detail_pairs)} câmp(uri)"


def build_table_summary(rows: list[dict[str, Any]], empty_message: str) -> str:
    """Summarize a table section for the visual UI."""

    if not rows:
        return empty_message
    return f"{len(rows)} rând(uri)"


def stringify_display_value(value: Any) -> str:
    """Convert payload values to strings for visual widgets without rewriting data."""

    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(stringify_display_value(item) for item in value)
    if isinstance(value, dict):
        return "; ".join(f"{key}: {stringify_display_value(item)}" for key, item in value.items())
    return str(value)
