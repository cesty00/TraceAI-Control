"""Typed data quality report models for TraceAI Control."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class DataQualityStatus(str, Enum):
    """Top-level data quality status."""

    OK = "OK"
    WARNING = "WARNING"
    ERROR = "ERROR"


class DataQualitySeverity(str, Enum):
    """Severity for one data quality issue."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass(frozen=True)
class DataQualityIssue:
    """One explicit data quality issue with source context."""

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
    """Compact source-level quality summary."""

    source_key: str
    source_name: str
    found: bool
    file_size_bytes: int | None = None
    row_count: int | None = None
    column_count: int | None = None
    sheet_count: int | None = None


@dataclass(frozen=True)
class DataQualityReport:
    """Top-level data quality report."""

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

    def compact_summary(self) -> dict[str, Any]:
        """Return a stable compact summary suitable for TraceabilityCase.sections."""

        return {
            "status": self.status.value,
            "source_count": self.source_count,
            "sources_found": self.sources_found,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "issue_count": len(self.issues),
        }


def data_quality_report_to_dict(report: DataQualityReport) -> dict[str, Any]:
    """Convert a data quality report to a JSON-safe dictionary."""

    payload = asdict(report)
    payload["status"] = report.status.value
    for issue in payload["issues"]:
        issue["severity"] = issue["severity"].value
    return payload
