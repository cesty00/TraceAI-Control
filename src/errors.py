"""Typed application errors for TraceAI Control.

The UI layer can render these errors as user-actionable messages without
showing raw stack traces. Engine layers should raise these when a failure has a
known category and a clear recommended action.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TraceAIError(Exception):
    """Base class for typed, user-actionable TraceAI errors."""

    user_message: str
    technical_detail: str | None = None
    recommended_action: str | None = None

    def __str__(self) -> str:
        parts = [self.user_message]
        if self.technical_detail:
            parts.append(f"Detalii tehnice: {self.technical_detail}")
        if self.recommended_action:
            parts.append(f"Acțiune recomandată: {self.recommended_action}")
        return "\n\n".join(parts)


class MissingSourceFileError(TraceAIError):
    """Raised when an expected operational source file is missing."""


class MissingRequiredColumnError(TraceAIError):
    """Raised when an operational source misses a required column."""


class InvalidInputError(TraceAIError):
    """Raised when user-provided input is incomplete or invalid."""


class NoMatchingRecordsError(TraceAIError):
    """Raised when no records match the requested code and lot."""


class AmbiguousCaseTypeError(TraceAIError):
    """Raised when the case type cannot be classified confidently."""


class ReportGenerationError(TraceAIError):
    """Raised when report rendering/export fails."""


class DataQualityBlockingError(TraceAIError):
    """Raised when data quality is severe enough to block generation."""
