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

DEFAULT_TABLE_ROW_LIMIT = 200
DEFAULT_DISPLAY_VALUE_LIMIT = 240
KIND_LABELS = {
    "details": "Detalii",
    "table": "Tabel",
    "empty": "Fără date",
}


@dataclass(frozen=True)
class SectionListItem:
    """One item displayed in the visual section navigation list."""

    index: int
    key: str
    title: str
    label: str
    kind: str
    kind_label: str = ""
    summary: str = ""


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
    total_row_count: int = 0
    displayed_row_count: int = 0
    hidden_row_count: int = 0


def build_section_list_items(view_model: AuditChecklistUiViewModel) -> list[SectionListItem]:
    """Build navigation items in the exact order supplied by the view model."""

    items: list[SectionListItem] = []
    for index, section in enumerate(view_model.sections, start=1):
        kind_label = KIND_LABELS.get(section.kind, section.kind or "Secțiune")
        summary = summarize_section_for_navigation(section)
        items.append(
            SectionListItem(
                index=index,
                key=section.key,
                title=section.title,
                label=build_section_navigation_label(index, section.title, summary),
                kind=section.kind,
                kind_label=kind_label,
                summary=summary,
            )
        )
    return items


def build_section_navigation_label(index: int, title: str, summary: str) -> str:
    """Build a compact, readable label for the section navigation list."""

    base = f"{index:02d}. {title}"
    if summary:
        return f"{base} · {summary}"
    return base


def summarize_section_for_navigation(section: AuditChecklistUiSection) -> str:
    """Summarize one section for the navigation list without business logic."""

    if section.kind == "table":
        return build_table_summary(section.rows, section.empty_message)
    if section.kind == "details":
        return build_detail_summary([(key, "") for key in section.field_keys], section.empty_message)
    return section.empty_message


def find_section_by_key(view_model: AuditChecklistUiViewModel, key: str) -> AuditChecklistUiSection | None:
    """Return a section by key without changing order or content."""

    for section in view_model.sections:
        if section.key == key:
            return section
    return None


def build_section_display_model(
    section: AuditChecklistUiSection,
    max_table_rows: int = DEFAULT_TABLE_ROW_LIMIT,
    max_value_length: int = DEFAULT_DISPLAY_VALUE_LIMIT,
) -> SectionDisplayModel:
    """Build the selected-section display model for the visual UI."""

    if section.kind == "details":
        detail_pairs = [
            (field_key, stringify_display_value(section.data.get(field_key, ""), max_length=max_value_length))
            for field_key in section.field_keys
        ]
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
        safe_row_limit = max(0, max_table_rows)
        visible_rows = section.rows[:safe_row_limit]
        table_rows = [
            [stringify_display_value(row.get(column, ""), max_length=max_value_length) for column in section.column_keys]
            for row in visible_rows
        ]
        total_row_count = len(section.rows)
        displayed_row_count = len(table_rows)
        hidden_row_count = max(total_row_count - displayed_row_count, 0)
        return SectionDisplayModel(
            key=section.key,
            title=section.title,
            description=section.description,
            kind=section.kind,
            table_columns=[humanize_field_label(column) for column in section.column_keys],
            table_rows=table_rows,
            summary=build_limited_table_summary(total_row_count, displayed_row_count, hidden_row_count, section.empty_message),
            empty_message=section.empty_message,
            total_row_count=total_row_count,
            displayed_row_count=displayed_row_count,
            hidden_row_count=hidden_row_count,
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


def build_limited_table_summary(total_count: int, displayed_count: int, hidden_count: int, empty_message: str) -> str:
    """Summarize a table section, including display limits when applicable."""

    if total_count <= 0:
        return empty_message
    if hidden_count > 0:
        return f"{displayed_count} din {total_count} rând(uri) afișate; {hidden_count} ascunse pentru lizibilitate"
    return f"{total_count} rând(uri)"


def humanize_field_label(value: str) -> str:
    """Make payload keys easier to read in visual widgets."""

    text = str(value).strip()
    if not text:
        return ""
    return " ".join(part for part in text.replace("_", " ").split()).capitalize()


def stringify_display_value(value: Any, max_length: int = DEFAULT_DISPLAY_VALUE_LIMIT) -> str:
    """Convert payload values to strings for visual widgets without rewriting data."""

    if value is None:
        text = ""
    elif isinstance(value, list):
        text = "; ".join(stringify_display_value(item, max_length=max_length) for item in value)
    elif isinstance(value, dict):
        text = "; ".join(f"{key}: {stringify_display_value(item, max_length=max_length)}" for key, item in value.items())
    else:
        text = str(value)
    return truncate_display_text(text, max_length=max_length)


def truncate_display_text(value: str, max_length: int = DEFAULT_DISPLAY_VALUE_LIMIT) -> str:
    """Trim very long visual values while making truncation explicit."""

    if max_length <= 0:
        return ""
    text = str(value)
    if len(text) <= max_length:
        return text
    if max_length <= 1:
        return "…"
    return text[: max_length - 1].rstrip() + "…"
