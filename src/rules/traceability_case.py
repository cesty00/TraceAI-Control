"""
TraceabilityCase contract for TraceAI Control.

This module defines the internal object that feeds the DOCX report. It maps the
available RulesPipelineResult metadata into a stable, audit-friendly structure
and populates report tables from Core selected records.

It intentionally does not calculate upstream/downstream traceability and does
not generate DOCX. Display aliases are normalization only: they expose source
values under stable report-column names while preserving the original normalized
keys for audit.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from decimal import Decimal, InvalidOperation
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

QUANTITY_COLUMNS = ("Cantitate", "Stoc")
UNIT_COLUMNS = ("UM", "U.M.", "Unitate", "Unitate masura", "Unitate măsură")

RAW_MATERIAL_ROLE = "materie primă alimentară"
PACKAGING_ROLE = "ambalaj"

CANONICAL_REPORT_ALIASES: dict[str, tuple[str, ...]] = {
    "Cod": ("cod", "code", "cod_articol", "cod_produs", "articol", "item", "sku"),
    "Lot": ("lot", "batch", "nr_lot", "numar_lot", "număr_lot"),
    "Denumire": (
        "denumire",
        "denumire_articol",
        "denumire_produs",
        "descriere",
        "nume_produs",
        "produs",
    ),
    "Cantitate": (
        "cantitate",
        "cant",
        "qty",
        "quantity",
        "cantitate_miscare",
        "cantitate_mișcare",
        "cantitate_reala",
        "cantitate_reală",
        "stoc",
    ),
    "UM": ("um", "u_m", "unitate", "unitate_masura", "unitate_măsură", "unit"),
    "Stoc": ("stoc", "cantitate_stoc", "stock"),
    "Locație": ("locatie", "locație", "depozit", "warehouse", "magazie"),
    "Numar comanda": (
        "numar_comanda",
        "număr_comandă",
        "nr_comanda",
        "nr_comandă",
        "comanda",
        "comandă",
    ),
    "Document intrare": (
        "document_intrare",
        "doc_intrare",
        "nr_document_intrare",
        "numar_document_intrare",
        "document_receptie",
        "document_recepție",
        "nr_receptie",
        "nr_recepție",
        "nir",
    ),
    "Document comanda": (
        "document_comanda",
        "document_comandă",
        "doc_comanda",
        "doc_comandă",
        "nr_document_comanda",
        "numar_document_comanda",
        "aviz",
        "factura",
        "factură",
    ),
    "Client": ("client", "beneficiar", "destinatar", "customer", "partener_client"),
    "Furnizor": ("furnizor", "supplier", "vendor", "partener_furnizor"),
    "Comandă": ("comanda", "comandă", "numar_comanda", "număr_comandă", "nr_comanda", "nr_comandă"),
    "Comandă producție": (
        "comanda_productie",
        "comandă_producție",
        "comanda_productie_prd",
        "nr_comanda_productie",
    ),
}


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
class TraceabilityBalanceLine:
    """One conservative preliminary balance line."""

    table_key: str
    table_title: str
    quantity_column: str
    unit: str
    total: str
    source_row_count: int
    skipped_row_count: int
    message: str


@dataclass(frozen=True)
class TraceabilityPreliminaryBalance:
    """Conservative balance calculated only from already populated report tables."""

    lines: list[TraceabilityBalanceLine] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class TraceabilityCase:
    """Internal contract for DOCX reporting."""

    subject: TraceabilityCaseSubject
    evidence: list[TraceabilityCaseEvidence] = field(default_factory=list)
    observations: list[str] = field(default_factory=list)
    sections: dict[str, Any] = field(default_factory=dict)
    report_tables: TraceabilityReportTables = field(default_factory=lambda: build_empty_report_tables())
    preliminary_balance: TraceabilityPreliminaryBalance = field(default_factory=lambda: build_empty_preliminary_balance())


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

    report_tables = build_report_tables_from_rules_result(result)

    return TraceabilityCase(
        subject=TraceabilityCaseSubject(code=code, lot=lot, case_type=detection.case_type),
        evidence=evidence,
        observations=observations,
        sections=sections,
        report_tables=report_tables,
        preliminary_balance=build_preliminary_balance(report_tables),
    )


def build_report_tables_from_rules_result(result: RulesPipelineResult) -> TraceabilityReportTables:
    """Populate report tables from selected Core records only.

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


def build_preliminary_balance(report_tables: TraceabilityReportTables) -> TraceabilityPreliminaryBalance:
    """Build conservative totals from already populated report tables."""

    lines: list[TraceabilityBalanceLine] = []
    messages: list[str] = [
        "Bilanț preliminar calculat doar din TraceabilityCase.report_tables.",
        "Unitățile de măsură sunt grupate separat; nu se fac conversii automate.",
    ]

    for table in report_tables_as_list(report_tables):
        table_lines, table_messages = build_balance_lines_for_table(table)
        lines.extend(table_lines)
        messages.extend(table_messages)

    if not lines:
        messages.append("Nu există valori numerice clare pentru calculul unui bilanț preliminar.")

    return TraceabilityPreliminaryBalance(lines=lines, messages=messages)


def build_balance_lines_for_table(table: TraceabilityReportTable) -> tuple[list[TraceabilityBalanceLine], list[str]]:
    """Build conservative balance lines for one report table."""

    if not table.rows:
        return [], [f"{table.title}: {table.empty_message}"]

    quantity_column = find_first_available_column(table.columns, QUANTITY_COLUMNS)
    unit_column = find_first_available_column(table.columns, UNIT_COLUMNS)
    if not quantity_column:
        return [], [f"{table.title}: nu există coloană explicită de cantitate / stoc."]
    if not unit_column:
        return [], [f"{table.title}: nu există coloană explicită UM; nu se calculează total."]

    totals: dict[str, Decimal] = {}
    source_counts: dict[str, int] = {}
    skipped = 0

    for row in table.rows:
        raw_quantity = get_value_case_insensitive(row.values, quantity_column)
        raw_unit = get_value_case_insensitive(row.values, unit_column)
        parsed = parse_clear_decimal(raw_quantity)
        unit = str(raw_unit).strip() if raw_unit is not None else ""
        if parsed is None or not unit:
            skipped += 1
            continue
        totals[unit] = totals.get(unit, Decimal("0")) + parsed
        source_counts[unit] = source_counts.get(unit, 0) + 1

    if not totals:
        return [], [f"{table.title}: nu există valori numerice clare pentru totalizare."]

    lines = [
        TraceabilityBalanceLine(
            table_key=table.key,
            table_title=table.title,
            quantity_column=quantity_column,
            unit=unit,
            total=format_decimal(total),
            source_row_count=source_counts[unit],
            skipped_row_count=skipped,
            message="Total preliminar pe UM, fără conversie automată.",
        )
        for unit, total in sorted(totals.items())
    ]
    messages = []
    if skipped:
        messages.append(f"{table.title}: {skipped} rând(uri) ignorate din cauza cantității/UM neclare.")
    return lines, messages


def find_first_available_column(columns: list[str], candidates: tuple[str, ...]) -> str | None:
    """Return the first candidate present in the table columns, case-insensitive."""

    normalized_columns = {column.casefold(): column for column in columns}
    for candidate in candidates:
        found = normalized_columns.get(candidate.casefold())
        if found:
            return found
    return None


def get_value_case_insensitive(values: dict[str, str], key: str) -> str | None:
    """Return a row value by key using case-insensitive matching."""

    if key in values:
        return values[key]
    key_folded = key.casefold()
    for existing_key, value in values.items():
        if existing_key.casefold() == key_folded:
            return value
    normalized_key = normalize_report_key(key)
    for existing_key, value in values.items():
        if normalize_report_key(existing_key) == normalized_key:
            return value
    return None


def parse_clear_decimal(value: object) -> Decimal | None:
    """Parse only clear decimal values; reject mixed separators and text."""

    if value is None:
        return None
    text = str(value).strip().replace(" ", "")
    if not text:
        return None
    if "," in text and "." in text:
        return None
    normalized = text.replace(",", ".")
    try:
        parsed = Decimal(normalized)
    except InvalidOperation:
        return None
    return parsed


def format_decimal(value: Decimal) -> str:
    """Format Decimal without scientific notation and without unnecessary zeros."""

    normalized = value.normalize()
    if normalized == normalized.to_integral():
        return str(normalized.quantize(Decimal("1")))
    return format(normalized, "f")


def build_empty_preliminary_balance() -> TraceabilityPreliminaryBalance:
    """Build an explicit empty preliminary balance."""

    return TraceabilityPreliminaryBalance(
        lines=[],
        messages=["Bilanț preliminar necalculat: TraceabilityCase nu conține încă tabele populate."],
    )


def table_row_from_selected_record(record: Any) -> TraceabilityTableRow:
    """Convert one selected Core record into a generic report table row.

    Normalized Core values remain untouched. Original source headers, when
    available, are appended without overwriting normalized keys. Canonical report
    aliases are then added only as convenience display keys.
    """

    values = dict(record.values)
    original_values = getattr(record, "original_values", {}) or {}
    for key, value in original_values.items():
        values.setdefault(key, value)
    values = add_canonical_report_values(values)

    return TraceabilityTableRow(
        values=values,
        source_key=record.source_key,
        source_name=record.source_name,
        sheet_name=record.sheet_name,
        row_number=record.row_number,
    )


def add_canonical_report_values(values: dict[str, str]) -> dict[str, str]:
    """Expose source values under stable report-column names.

    This is presentation normalization only. It does not infer missing values and
    does not overwrite existing source keys.
    """

    enriched = dict(values)
    for canonical, aliases in CANONICAL_REPORT_ALIASES.items():
        if str(enriched.get(canonical, "")).strip():
            continue
        value = first_value_by_alias(enriched, aliases)
        if value is not None and str(value).strip():
            enriched[canonical] = value
    return enriched


def first_value_by_alias(values: dict[str, str], aliases: tuple[str, ...]) -> str | None:
    alias_keys = {normalize_report_key(alias) for alias in aliases}
    for key, value in values.items():
        if normalize_report_key(key) in alias_keys and str(value).strip():
            return value
    return None


def normalize_report_key(value: object) -> str:
    text = remove_diacritics(str(value)).casefold().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_")


def remove_diacritics(value: str) -> str:
    return value.translate(
        str.maketrans(
            {
                "ă": "a",
                "â": "a",
                "î": "i",
                "ș": "s",
                "ş": "s",
                "ț": "t",
                "ţ": "t",
                "Ă": "A",
                "Â": "A",
                "Î": "I",
                "Ș": "S",
                "Ş": "S",
                "Ț": "T",
                "Ţ": "T",
            }
        )
    )


def is_alisol_auxiliary_record(record: Any) -> bool:
    """Return True when the selected record refers to ALISOL."""

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
    """Build a normalized text blob from selected record values."""

    values = list(getattr(record, "values", {}).values())
    values.extend((getattr(record, "original_values", {}) or {}).values())
    return " ".join(str(value) for value in values).casefold()


def add_alisol_auxiliary_note(row: TraceabilityTableRow) -> TraceabilityTableRow:
    """Add explicit ALISOL classification note to a report table row."""

    values = dict(row.values)
    values.setdefault("Observații", ALISOL_AUXILIARY_OBSERVATION)
    return TraceabilityTableRow(values, row.source_key, row.source_name, row.sheet_name, row.row_number)


def add_classification_role(row: TraceabilityTableRow, role: str) -> TraceabilityTableRow:
    """Add a report role when one is not already present."""

    values = dict(row.values)
    values.setdefault("Rol", role)
    return TraceabilityTableRow(values, row.source_key, row.source_name, row.sheet_name, row.row_number)


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
