"""
TraceabilityCase contract for TraceAI Control.

This module defines the internal object that feeds the DOCX report. It maps the
available RulesPipelineResult metadata into a stable, audit-friendly structure
and reserves explicit report tables for later operational population.

It intentionally does not calculate upstream/downstream traceability details and
does not generate DOCX.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from src.rules.run_rules_pipeline import RulesPipelineResult


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
    """One audit-friendly table row.

    Values are stored as display strings because TraceabilityCase is a reporting
    contract, not a calculation engine. Original source context is preserved
    when available.
    """

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

    return TraceabilityCase(
        subject=TraceabilityCaseSubject(
            code=code,
            lot=lot,
            case_type=detection.case_type,
        ),
        evidence=evidence,
        observations=list(detection.observations),
        sections=sections,
        report_tables=build_empty_report_tables(),
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
