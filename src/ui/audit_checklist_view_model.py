"""View-model helpers for the audit checklist UI.

This module is the presentation boundary for UI-AUDIT-02. It consumes the
stable ``audit-checklist-ui.v1`` payload produced by ``audit_checklist_json`` and
maps only ``payload["sections"]`` into render-ready UI sections.

It intentionally does not rebuild traceability tables from TraceabilityCase or
from the raw ``report`` dictionary. Business rules stay in the audit/report
layers; this module only normalizes display metadata for a future visual UI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.ui.audit_checklist_json import UI_SCHEMA_VERSION


@dataclass(frozen=True)
class AuditChecklistUiSection:
    """One section ready to be displayed by an interface."""

    key: str
    title: str
    description: str
    kind: str
    rows: list[dict[str, Any]] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)
    column_keys: list[str] = field(default_factory=list)
    field_keys: list[str] = field(default_factory=list)
    empty_message: str = "FARA DATE IDENTIFICATE"


@dataclass(frozen=True)
class AuditChecklistUiViewModel:
    """Render-ready representation of an audit checklist payload."""

    schema_version: str
    subject: dict[str, Any]
    sections: list[AuditChecklistUiSection]


def build_audit_checklist_ui_view_model(payload: dict[str, Any]) -> AuditChecklistUiViewModel:
    """Build a render-ready view model from ``audit-checklist-ui.v1`` payload.

    The function deliberately reads section content from ``payload["sections"]``.
    The full report remains available in the payload for advanced consumers, but
    this UI mapping layer does not reconstruct or reinterpret it.
    """

    validate_audit_checklist_ui_payload(payload)
    return AuditChecklistUiViewModel(
        schema_version=str(payload["schema_version"]),
        subject=dict(payload["subject"]),
        sections=[section_view_model(section) for section in payload["sections"]],
    )


def validate_audit_checklist_ui_payload(payload: dict[str, Any]) -> None:
    """Validate only the UI contract shape, not traceability business content."""

    if payload.get("schema_version") != UI_SCHEMA_VERSION:
        raise ValueError(f"Schema UI nesuportată: {payload.get('schema_version')}")
    if not isinstance(payload.get("subject"), dict):
        raise ValueError("Payload UI invalid: subject lipsește sau nu este obiect.")
    if not isinstance(payload.get("sections"), list):
        raise ValueError("Payload UI invalid: sections lipsește sau nu este listă.")


def section_view_model(section: dict[str, Any]) -> AuditChecklistUiSection:
    """Map one payload section to a display section without business logic."""

    key = str(section.get("key", "")).strip()
    title = str(section.get("title", "")).strip()
    description = str(section.get("description", "")).strip()
    if not key:
        raise ValueError("Secțiune UI invalidă: key lipsește.")
    if not title:
        raise ValueError(f"Secțiune UI invalidă pentru {key}: title lipsește.")

    if "rows" in section:
        rows = normalize_rows(section.get("rows"))
        return AuditChecklistUiSection(
            key=key,
            title=title,
            description=description,
            kind="table",
            rows=rows,
            column_keys=collect_column_keys(rows),
        )

    if "data" in section:
        data = normalize_data(section.get("data"))
        return AuditChecklistUiSection(
            key=key,
            title=title,
            description=description,
            kind="details",
            data=data,
            field_keys=list(data.keys()),
        )

    return AuditChecklistUiSection(
        key=key,
        title=title,
        description=description,
        kind="empty",
    )


def normalize_rows(value: Any) -> list[dict[str, Any]]:
    """Return table rows as dictionaries while preserving payload values."""

    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("Secțiune UI invalidă: rows trebuie să fie listă.")
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(value, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"Secțiune UI invalidă: rows[{index}] nu este obiect.")
        rows.append(dict(row))
    return rows


def normalize_data(value: Any) -> dict[str, Any]:
    """Return detail data as a dictionary while preserving payload values."""

    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("Secțiune UI invalidă: data trebuie să fie obiect.")
    return dict(value)


def collect_column_keys(rows: list[dict[str, Any]]) -> list[str]:
    """Collect table columns in stable payload order.

    The first row defines the initial order. Extra keys found in later rows are
    appended in discovery order so the UI can still render sparse tables.
    """

    columns: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key in seen:
                continue
            seen.add(key)
            columns.append(key)
    return columns
