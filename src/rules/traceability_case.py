"""
TraceabilityCase skeleton for TraceAI Control.

This module defines the internal object that will later feed the DOCX report.
At this stage it only maps the available RulesPipelineResult metadata into a
stable, audit-friendly structure.

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
class TraceabilityCase:
    """Internal contract for future DOCX reporting."""

    subject: TraceabilityCaseSubject
    evidence: list[TraceabilityCaseEvidence] = field(default_factory=list)
    observations: list[str] = field(default_factory=list)
    sections: dict[str, Any] = field(default_factory=dict)


def build_traceability_case(result: RulesPipelineResult, code: str, lot: str) -> TraceabilityCase:
    """Build a minimal TraceabilityCase from the Rules Pipeline result."""

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
    )


def traceability_case_to_dict(traceability_case: TraceabilityCase) -> dict[str, Any]:
    """Convert TraceabilityCase dataclasses to a JSON-safe dictionary."""

    return asdict(traceability_case)


def traceability_case_to_json(traceability_case: TraceabilityCase) -> str:
    """Serialize TraceabilityCase for inspection/debugging."""

    return json.dumps(traceability_case_to_dict(traceability_case), ensure_ascii=False, indent=2)
