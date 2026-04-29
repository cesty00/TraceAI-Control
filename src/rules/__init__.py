"""Rules Engine package for TraceAI Control."""

from .case_type_detection import (
    CASE_FINISHED_PRODUCT,
    CASE_RAW_MATERIAL,
    CASE_UNKNOWN,
    CASE_WMS_ONLY_PRODUCT,
    CaseTypeDetectionResult,
    CaseTypeEvidence,
    case_type_result_to_dict,
    detect_case_type,
    detect_case_type_from_dataset,
)
from .run_rules_pipeline import (
    RulesPipelineResult,
    rules_pipeline_result_to_dict,
    run_rules_pipeline,
)
from .run_traceability_case import run_traceability_case
from .traceability_case import (
    TraceabilityCase,
    TraceabilityCaseEvidence,
    TraceabilityCaseSubject,
    TraceabilityReportTable,
    TraceabilityReportTables,
    TraceabilityTableRow,
    build_empty_report_tables,
    build_report_tables_from_rules_result,
    build_traceability_case,
    report_tables_as_list,
    table_row_from_selected_record,
    traceability_case_to_dict,
    traceability_case_to_json,
)

__all__ = [
    "CASE_FINISHED_PRODUCT",
    "CASE_RAW_MATERIAL",
    "CASE_UNKNOWN",
    "CASE_WMS_ONLY_PRODUCT",
    "CaseTypeDetectionResult",
    "CaseTypeEvidence",
    "RulesPipelineResult",
    "TraceabilityCase",
    "TraceabilityCaseEvidence",
    "TraceabilityCaseSubject",
    "TraceabilityReportTable",
    "TraceabilityReportTables",
    "TraceabilityTableRow",
    "build_empty_report_tables",
    "build_report_tables_from_rules_result",
    "build_traceability_case",
    "case_type_result_to_dict",
    "detect_case_type",
    "detect_case_type_from_dataset",
    "report_tables_as_list",
    "rules_pipeline_result_to_dict",
    "run_rules_pipeline",
    "run_traceability_case",
    "table_row_from_selected_record",
    "traceability_case_to_dict",
    "traceability_case_to_json",
]
