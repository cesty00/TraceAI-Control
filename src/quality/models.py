"""Typed data quality report models for TraceAI Control."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class DataQualityStatus(str, Enum):
    OK = "OK"
    WARNING = "WARNING"
    ERROR = "ERROR"


class DataQualitySeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass(frozen=True)
class DataQualityIssue:
    severity: DataQualitySeverity
    source_key: str
    source_name: str
    message: str
    row_count: int | None = None
    column_name: str | None = None
    sheet_name: str | None = None
    sample_rows: list[int] = field(default_factory=list)


@dataclass(frozen=True)
class DataQualitySourceSummary:
    source_key: str
    source_name: str
    found: bool
    file_size_bytes: int | None = None
    row_count: int | None = None
    column_count: int | None = None
    sheet_count: int | None = None


@dataclass(frozen=True)
class DataQualityReport:
    status: DataQualityStatus
    source_count: int
    sources_found: int
    issues: list[DataQualityIssue] = field(default_factory=list)
    sources: list[DataQualitySourceSummary] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == DataQualitySeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == DataQualitySeverity.WARNING)

    @property
    def issue_summaries(self) -> list[dict[str, Any]]:
        return [
            {
                "severity": issue.severity.value,
                "source_name": issue.source_name,
                "sheet_name": issue.sheet_name,
                "column_name": issue.column_name,
                "message": issue.message,
            }
            for issue in self.issues
        ]

    def compact_summary(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "source_count": self.source_count,
            "sources_found": self.sources_found,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "issue_count": len(self.issues),
            "issues": self.issue_summaries,
        }


def data_quality_report_to_dict(report: DataQualityReport) -> dict[str, Any]:
    payload = asdict(report)
    payload["status"] = report.status.value
    for issue in payload["issues"]:
        issue["severity"] = issue["severity"].value
    return payload
