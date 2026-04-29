"""
TraceabilityCase contract for TraceAI Control.

This module defines the internal object that feeds the DOCX report. It maps the
available RulesPipelineResult metadata into a stable, audit-friendly structure
and populates a small first set of report tables from Core selected records.

It intentionally does not calculate upstream/downstream traceability details and
does not generate DOCX.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from src.rules.run_rules_pipeline import RulesPipelineResult

ALISOL_HINT = "alisol"
ALISOL_AUXILIARY_OBSERVATION = "ALISOL este tratat ca auxiliar / gaz tehnologic, nu ca materie primă alimentară."

RAW_MATERIAL_HINTS = (
    "materie prima",
    "materie primă",
    "materii prime",
    "ingredient",
)

PACKAGING_HINTS = (
    "ambalaj",
    "ambalaje",
    "folie",
    "punga",
    "pungă",
    "cutie",
    "carton",
    "eticheta",
    "etichetă",
    "capac",
    "borcan",
    "palet",
    "pallet",
)

FINISHED_GOODS_DELIVERY_HINTS = (
    "livrare",
    "livrat",
    "livrari",
    "livrări",
    "iesire",
    "ieșire",
    "document comanda",
    "document comandă",
    "client",
)

RAW_MATERIAL_ROLE = "materie primă alimentară"
PACKAGING_ROLE = "ambalaj"


@dataclass(frozen=True)
class TraceabilityCaseSubject:
    """Subject requested by the operator."""

    code: str
    lot: str
    case_type: str


@dataclass(frozen=True)
class TraceabilityCaseEvidence:
    """Evidence attached to the case."""

    source_key: str
    source_name: str
    sheet_name: str | None
    row_number: int | None
    message: str


@dataclass(frozen=True)
class TraceabilityTableRow:
    """One audit-friendly table row."""

    values: dict[str, str]
    source_key: str | None = None
    source_name: str | None = None
    sheet_name: str | None = None
    row_number: int | None = None


@dataclass(frozen=True)
class TraceabilityReportTable:
    """One reportable table section for DOCX generation."""

    key: str
    title: str
    columns: list[str]
    rows: list[TraceabilityTableRow] = field(default_factory=list)
    empty_message: str = "FARA DATE IDENTIFICATE"


@dataclass(frozen=True)
class TraceabilityReportTables:
    """All reportable table sections expected by the narrative DOCX model."""

    production: TraceabilityReportTable
    finished_goods_deliveries: TraceabilityReportTable
    raw_materials: TraceabilityReportTable
    packaging: TraceabilityReportTable
    auxiliaries_gas: TraceabilityReportTable
    wms_receipts: TraceabilityReportTable
    prd_consumptions: TraceabilityReportTable
    stock: TraceabilityReportTable


@dataclass(frozen=True)
class TraceabilityCase:
    """Internal contract for DOCX reporting."""

    subject: TraceabilityCaseSubject
    evidence: list[TraceabilityCaseEvidence] = field(default_factory=list)
    observations: list[str] = field(default_factory=list)
    sections: dict[str, Any] = field(default_factory=dict)
    report_tables: TraceabilityReportTables = field(default_factory=lambda: build_empty_report_tables())


def build_traceability_case(result: RulesPipelineResult, code: str, lot: str) -> TraceabilityCase:
    """Build a TraceabilityCase from the Rules Pipeline result."""

    detection = result.case_type_detection
    evidence = [
        TraceabilityCaseEvidence(
            source_key=item.source_key,
            source_name=item.source_name,
            sheet_name=item.sheet_name,
            row_number=item.row_number,
            message=item.message,
        )
        for item in detection.evidence
    ]

    sections = {
        "core_validation_status": result.core.validation.status,
        "selected_record_count": len(result.core.selection.records),
        "inventory_problem_count": len(result.core.inventory.problems),
        "dataset_problem_count": len(result.core.normalized_dataset.problems),
    }

    observations = list(detection.observations)
    if any(is_alisol_auxiliary_record(record) for record in result.core.selection.records):
        observations.append(ALISOL_AUXILIARY_OBSERVATION)

    return TraceabilityCase(
        subject=TraceabilityCaseSubject(
            code=code,
            lot=lot,
            case_type=detection.case_type,
        ),
        evidence=evidence,
        observations=observations,
        sections=sections,
        report_tables=build_report_tables_from_rules_result(result),
    )


def build_report_tables_from_rules_result(result: RulesPipelineResult) -> TraceabilityReportTables:
    """Populate first report tables from selected Core records only.

    This is a controlled population step. It maps selected rows into reportable
    strings and does not infer upstream/downstream traceability.
    """

    tables = build_empty_report_tables()
    production_rows: list[TraceabilityTableRow] = []
    delivery_rows: list[TraceabilityTableRow] = []
    raw_material_rows: list[TraceabilityTableRow] = []
    packaging_rows: list[TraceabilityTableRow] = []
    auxiliary_rows: list[TraceabilityTableRow] = []
    wms_rows: list[TraceabilityTableRow] = []
    stock_rows: list[TraceabilityTableRow] = []

    for record in result.core.selection.records:
        row = table_row_from_selected_record(record)
        if is_alisol_auxiliary_record(record):
            auxiliary_rows.append(add_alisol_auxiliary_note(row))
        elif is_packaging_record(record):
            packaging_rows.append(add_classification_role(row, PACKAGING_ROLE))
        elif is_raw_material_record(record):
            raw_material_rows.append(add_classification_role(row, RAW_MATERIAL_ROLE))
        elif record.source_key == "production":
            production_rows.append(row)
        elif record.source_key == "wms" and is_finished_goods_delivery_record(record):
            delivery_rows.append(row)
        elif record.source_key == "wms":
            wms_rows.append(row)
        elif record.source_key == "stock":
            stock_rows.append(row)

    return TraceabilityReportTables(
        production=replace_table_rows(tables.production, production_rows),
        finished_goods_deliveries=replace_table_rows(tables.finished_goods_deliveries, delivery_rows),
        raw_materials=replace_table_rows(tables.raw_materials, raw_material_rows),
        packaging=replace_table_rows(tables.packaging, packaging_rows),
        auxiliaries_gas=replace_table_rows(tables.auxiliaries_gas, auxiliary_rows),
        wms_receipts=replace_table_rows(tables.wms_receipts, wms_rows),
        prd_consumptions=tables.prd_consumptions,
        stock=replace_table_rows(tables.stock, stock_rows),
    )


def table_row_from_selected_record(record: Any) -> TraceabilityTableRow:
    """Convert one selected Core record into a generic report table row."""

    return TraceabilityTableRow(
        values={key: value for key, value in record.values.items()},
        source_key=record.source_key,
        source_name=record.source_name,
        sheet_name=record.sheet_name,
        row_number=record.row_number,
    )


def is_alisol_auxiliary_record(record: Any) -> bool:
    """Return True when the selected record refers to ALISOL.

    Business rule: ALISOL is auxiliary / technological gas and must never be
    classified as food raw material.
    """

    return ALISOL_HINT in normalized_record_text(record)


def is_raw_material_record(record: Any) -> bool:
    """Return True for explicit food raw material hints only."""

    text = normalized_record_text(record)
    return any(hint in text for hint in RAW_MATERIAL_HINTS)


def is_packaging_record(record: Any) -> bool:
    """Return True for explicit packaging hints only."""

    text = normalized_record_text(record)
    return any(hint in text for hint in PACKAGING_HINTS)


def is_finished_goods_delivery_record(record: Any) -> bool:
    """Return True for explicit WMS finished goods delivery hints only."""

    if record.source_key != "wms":
        return False
    text = normalized_record_text(record)
    return any(hint in text for hint in FINISHED_GOODS_DELIVERY_HINTS)


def normalized_record_text(record: Any) -> str:
    """Build a normalized text blob from a selected record."""

    return " ".join(str(value) for value in record.values.values()).casefold()


def add_alisol_auxiliary_note(row: TraceabilityTableRow) -> TraceabilityTableRow:
    """Add explicit ALISOL classification note to a report table row."""

    values = dict(row.values)
    values.setdefault("Observații", ALISOL_AUXILIARY_OBSERVATION)
    return TraceabilityTableRow(
        values=values,
        source_key=row.source_key,
        source_name=row.source_name,
        sheet_name=row.sheet_name,
        row_number=row.row_number,
    )


def add_classification_role(row: TraceabilityTableRow, role: str) -> TraceabilityTableRow:
    """Add a report role when one is not already present."""

    values = dict(row.values)
    values.setdefault("Rol", role)
    return TraceabilityTableRow(
        values=values,
        source_key=row.source_key,
        source_name=row.source_name,
        sheet_name=row.sheet_name,
        row_number=row.row_number,
    )


def replace_table_rows(table: TraceabilityReportTable, rows: list[TraceabilityTableRow]) -> TraceabilityReportTable:
    """Return the same report table definition with new rows."""

    return TraceabilityReportTable(
        key=table.key,
        title=table.title,
        columns=table.columns,
        rows=rows,
        empty_message=table.empty_message,
    )


def build_empty_report_tables() -> TraceabilityReportTables:
    """Build all report table sections with explicit empty messages."""

    return TraceabilityReportTables(
        production=TraceabilityReportTable(
            key="production",
            title="Producția lotului",
            columns=["Cod", "Lot", "Comandă", "Cantitate", "UM", "Observații"],
            empty_message="Nu au fost identificate date detaliate de producție în TraceabilityCase.",
        ),
        finished_goods_deliveries=TraceabilityReportTable(
            key="finished_goods_deliveries",
            title="Livrări produs finit",
            columns=["Numar comanda", "Document comanda", "Client", "Cantitate", "UM"],
            empty_message="Nu au fost identificate livrări produs finit în TraceabilityCase.",
        ),
        raw_materials=TraceabilityReportTable(
            key="raw_materials",
            title="Materii prime alimentare",
            columns=["Cod", "Lot", "Denumire", "Cantitate", "UM", "Rol"],
            empty_message="Nu au fost identificate materii prime alimentare în TraceabilityCase.",
        ),
        packaging=TraceabilityReportTable(
            key="packaging",
            title="Ambalaje",
            columns=["Cod", "Lot", "Denumire", "Cantitate", "UM"],
            empty_message="Nu au fost identificate ambalaje în TraceabilityCase.",
        ),
        auxiliaries_gas=TraceabilityReportTable(
            key="auxiliaries_gas",
            title="Materiale auxiliare / gaz",
            columns=["Cod", "Lot", "Denumire", "Cantitate", "UM", "Observații"],
            empty_message="Nu au fost identificate materiale auxiliare / gaz în TraceabilityCase.",
        ),
        wms_receipts=TraceabilityReportTable(
            key="wms_receipts",
            title="Recepții WMS",
            columns=["Numar comanda", "Document intrare", "Document comanda", "Furnizor", "Cantitate", "UM"],
            empty_message="Nu au fost identificate recepții WMS detaliate în TraceabilityCase.",
        ),
        prd_consumptions=TraceabilityReportTable(
            key="prd_consumptions",
            title="Consumuri PRD",
            columns=["Cod", "Lot", "Comandă producție", "Cantitate", "UM"],
            empty_message="Nu au fost identificate consumuri PRD detaliate în TraceabilityCase.",
        ),
        stock=TraceabilityReportTable(
            key="stock",
            title="Stoc la moment",
            columns=["Cod", "Lot", "Stoc", "UM", "Locație"],
            empty_message="Articolul nu apare explicit în stocul la moment în TraceabilityCase.",
        ),
    )


def report_tables_as_list(report_tables: TraceabilityReportTables) -> list[TraceabilityReportTable]:
    """Return report tables in DOCX display order."""

    return [
        report_tables.production,
        report_tables.finished_goods_deliveries,
        report_tables.raw_materials,
        report_tables.packaging,
        report_tables.auxiliaries_gas,
        report_tables.wms_receipts,
        report_tables.prd_consumptions,
        report_tables.stock,
    ]


def traceability_case_to_dict(traceability_case: TraceabilityCase) -> dict[str, Any]:
    """Convert TraceabilityCase dataclasses to a JSON-safe dictionary."""

    return asdict(traceability_case)


def traceability_case_to_json(traceability_case: TraceabilityCase) -> str:
    """Serialize TraceabilityCase for inspection/debugging."""

    return json.dumps(traceability_case_to_dict(traceability_case), ensure_ascii=False, indent=2)
