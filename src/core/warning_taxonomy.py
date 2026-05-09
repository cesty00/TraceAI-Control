"""Internal warning taxonomy classifier.

This module is intentionally pure and user-interface agnostic. It classifies
known warning conditions into internal review/escalation metadata without
changing public preflight status, DTO/JSON contracts, DOCX output, or UI text.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class WarningTaxonomySeverity(str, Enum):
    """Internal warning severity buckets."""

    WARNING_INFO = "WARNING_INFO"
    WARNING_REVIEW = "WARNING_REVIEW"
    WARNING_ESCALATE = "WARNING_ESCALATE"
    WARNING_CRITICAL = "WARNING_CRITICAL"


class OperatorAction(str, Enum):
    """Internal operator action recommendation."""

    CONTINUE = "CONTINUE"
    REVIEW_AND_CONTINUE = "REVIEW_AND_CONTINUE"
    CONTROLLED_CONTINUE = "CONTROLLED_CONTINUE"
    STOP_FOR_HUMAN_REVIEW = "STOP_FOR_HUMAN_REVIEW"


class DiagnosticZipPolicy(str, Enum):
    """Internal diagnostic ZIP retention policy."""

    NO = "NO"
    RECOMMENDED = "RECOMMENDED"
    REQUIRED = "REQUIRED"


class EscalationPolicy(str, Enum):
    """Internal escalation recommendation."""

    NO = "NO"
    RECOMMENDED = "RECOMMENDED"
    REQUIRED = "REQUIRED"


@dataclass(frozen=True)
class WarningClassification:
    """Internal classification for one warning condition or warning group."""

    severity: WarningTaxonomySeverity
    operator_action: OperatorAction
    diagnostic_zip_policy: DiagnosticZipPolicy
    escalation_policy: EscalationPolicy
    can_transition_to_blocker: bool
    operator_message: str


CONDITION_MISSING_STOCK_FOR_CODE_LOT = "missing_stock_for_code_lot"
CONDITION_MISSING_SINGLE_PRIMARY_SOURCE = "missing_single_primary_source"
CONDITION_DATA_QUALITY_ERROR_NON_BLOCKING = "data_quality_error_non_blocking"
CONDITION_AUXILIARY_SHEET_DEGRADED = "auxiliary_sheet_degraded"
CONDITION_ROW_WITHOUT_CODE = "row_without_code"
CONDITION_ROW_WITHOUT_LOT = "row_without_lot"
CONDITION_DIAGNOSTIC_ZIP_MISSING_SIMPLE = "diagnostic_zip_missing_simple"
CONDITION_DIAGNOSTIC_ZIP_MISSING_MATERIAL_WARNING = "diagnostic_zip_missing_material_warning"
CONDITION_DIAGNOSTIC_ZIP_MISSING_MAJOR_CONFLICT = "diagnostic_zip_missing_major_conflict"
CONDITION_MAJOR_SOURCE_CONFLICT = "major_source_conflict"

_SEVERITY_ORDER = [
    WarningTaxonomySeverity.WARNING_INFO,
    WarningTaxonomySeverity.WARNING_REVIEW,
    WarningTaxonomySeverity.WARNING_ESCALATE,
    WarningTaxonomySeverity.WARNING_CRITICAL,
]


def warning_info(operator_message: str) -> WarningClassification:
    return WarningClassification(
        severity=WarningTaxonomySeverity.WARNING_INFO,
        operator_action=OperatorAction.CONTINUE,
        diagnostic_zip_policy=DiagnosticZipPolicy.NO,
        escalation_policy=EscalationPolicy.NO,
        can_transition_to_blocker=False,
        operator_message=operator_message,
    )


def warning_review(operator_message: str) -> WarningClassification:
    return WarningClassification(
        severity=WarningTaxonomySeverity.WARNING_REVIEW,
        operator_action=OperatorAction.REVIEW_AND_CONTINUE,
        diagnostic_zip_policy=DiagnosticZipPolicy.RECOMMENDED,
        escalation_policy=EscalationPolicy.NO,
        can_transition_to_blocker=False,
        operator_message=operator_message,
    )


def warning_escalate(operator_message: str) -> WarningClassification:
    return WarningClassification(
        severity=WarningTaxonomySeverity.WARNING_ESCALATE,
        operator_action=OperatorAction.CONTROLLED_CONTINUE,
        diagnostic_zip_policy=DiagnosticZipPolicy.RECOMMENDED,
        escalation_policy=EscalationPolicy.RECOMMENDED,
        can_transition_to_blocker=True,
        operator_message=operator_message,
    )


def warning_critical(operator_message: str) -> WarningClassification:
    return WarningClassification(
        severity=WarningTaxonomySeverity.WARNING_CRITICAL,
        operator_action=OperatorAction.STOP_FOR_HUMAN_REVIEW,
        diagnostic_zip_policy=DiagnosticZipPolicy.REQUIRED,
        escalation_policy=EscalationPolicy.REQUIRED,
        can_transition_to_blocker=True,
        operator_message=operator_message,
    )


def missing_stock_for_code_lot() -> WarningClassification:
    return warning_review("Codul și lotul lipsesc din stocul la moment; revizuire recomandată.")


def missing_single_primary_source() -> WarningClassification:
    return warning_escalate("Codul și lotul lipsesc dintr-o singură sursă principală; escaladare recomandată.")


def data_quality_error_non_blocking() -> WarningClassification:
    return warning_escalate("Data Quality ERROR non-blocking; continuare controlată cu escaladare recomandată.")


def auxiliary_sheet_degraded() -> WarningClassification:
    return warning_review("Sheet auxiliar degradat; revizuire recomandată înainte de continuare.")


def row_without_code() -> WarningClassification:
    return warning_escalate("Rând fără cod identificabil; escaladare recomandată.")


def row_without_lot() -> WarningClassification:
    return warning_escalate("Rând fără lot identificabil; escaladare recomandată.")


def diagnostic_zip_missing_simple() -> WarningClassification:
    return warning_review("Diagnostic ZIP lipsă pentru observație simplă; păstrarea dovezilor este recomandată.")


def diagnostic_zip_missing_material_warning() -> WarningClassification:
    return warning_escalate("Diagnostic ZIP lipsă pentru warning material; escaladare recomandată.")


def diagnostic_zip_missing_major_conflict() -> WarningClassification:
    return warning_critical("Diagnostic ZIP lipsă pentru conflict major; oprire pentru review uman.")


def major_source_conflict() -> WarningClassification:
    return warning_critical("Conflict major între surse; oprire pentru review uman.")


_CONDITION_CLASSIFIERS = {
    CONDITION_MISSING_STOCK_FOR_CODE_LOT: missing_stock_for_code_lot,
    CONDITION_MISSING_SINGLE_PRIMARY_SOURCE: missing_single_primary_source,
    CONDITION_DATA_QUALITY_ERROR_NON_BLOCKING: data_quality_error_non_blocking,
    CONDITION_AUXILIARY_SHEET_DEGRADED: auxiliary_sheet_degraded,
    CONDITION_ROW_WITHOUT_CODE: row_without_code,
    CONDITION_ROW_WITHOUT_LOT: row_without_lot,
    CONDITION_DIAGNOSTIC_ZIP_MISSING_SIMPLE: diagnostic_zip_missing_simple,
    CONDITION_DIAGNOSTIC_ZIP_MISSING_MATERIAL_WARNING: diagnostic_zip_missing_material_warning,
    CONDITION_DIAGNOSTIC_ZIP_MISSING_MAJOR_CONFLICT: diagnostic_zip_missing_major_conflict,
    CONDITION_MAJOR_SOURCE_CONFLICT: major_source_conflict,
}


def classify_warning_condition(condition: str) -> WarningClassification:
    """Classify a known warning condition key."""

    classifier = _CONDITION_CLASSIFIERS.get(condition)
    if classifier is None:
        raise ValueError(f"Unknown warning taxonomy condition: {condition}")
    return classifier()


def classify_repeated_warning(
    classification: WarningClassification,
    occurrence_count: int,
) -> WarningClassification:
    """Escalate one level when the same warning repeats."""

    if occurrence_count <= 1:
        return classification
    return classification_for_severity(
        increase_severity(classification.severity, levels=1),
        operator_message=f"Warning repetat de {occurrence_count} ori: {classification.operator_message}",
    )


def classify_cumulative_warnings(classifications: Iterable[WarningClassification]) -> WarningClassification:
    """Classify a cumulative group of warning classifications."""

    items = list(classifications)
    if not items:
        return warning_info("Nu există avertizări cumulative.")

    severities = [item.severity for item in items]
    if WarningTaxonomySeverity.WARNING_CRITICAL in severities:
        return warning_critical("Avertizări cumulative includ un warning critic; review uman necesar.")

    escalate_count = severities.count(WarningTaxonomySeverity.WARNING_ESCALATE)
    review_count = severities.count(WarningTaxonomySeverity.WARNING_REVIEW)

    if escalate_count >= 3:
        return warning_critical("Avertizări cumulative multiple cu escaladare; review uman necesar.")
    if escalate_count:
        return warning_escalate("Avertizări cumulative includ condiții care cer escaladare.")
    if review_count >= 2:
        return warning_escalate("Avertizări cumulative de revizuire; escaladare recomandată.")
    if review_count:
        return warning_review("Avertizări cumulative de revizuire; continuare cu atenție.")
    return warning_info("Avertizări cumulative informative; continuare permisă.")


def increase_severity(
    severity: WarningTaxonomySeverity,
    levels: int = 1,
) -> WarningTaxonomySeverity:
    """Increase severity by a fixed number of levels, capped at critical."""

    index = _SEVERITY_ORDER.index(severity)
    return _SEVERITY_ORDER[min(index + levels, len(_SEVERITY_ORDER) - 1)]


def classification_for_severity(
    severity: WarningTaxonomySeverity,
    operator_message: str,
) -> WarningClassification:
    """Build a default internal classification for a severity."""

    if severity == WarningTaxonomySeverity.WARNING_CRITICAL:
        return warning_critical(operator_message)
    if severity == WarningTaxonomySeverity.WARNING_ESCALATE:
        return warning_escalate(operator_message)
    if severity == WarningTaxonomySeverity.WARNING_REVIEW:
        return warning_review(operator_message)
    return warning_info(operator_message)
