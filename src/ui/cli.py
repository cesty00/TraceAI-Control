"""Minimal CLI shell over the UI orchestrator.

This module is intentionally thin: it parses CLI arguments, builds a
UiGenerationRequest, calls the orchestrator, prints the returned message, and
returns a process exit code.

It does not read operational source files directly and does not contain business
logic.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable

from src.ui.orchestrator import UiGenerationRequest, UiGenerationResult, generate_report_from_ui_request

UiRequestHandler = Callable[[UiGenerationRequest], UiGenerationResult]


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser for the minimal UI shell."""

    parser = argparse.ArgumentParser(
        description="Generate a TraceAI Control DOCX report through the UI orchestrator."
    )
    parser.add_argument("source_directory", help="Folderul cu sursele oficiale.")
    parser.add_argument("--code", required=True, help="Cod articol/produs.")
    parser.add_argument("--lot", required=True, help="Lot verificat.")
    parser.add_argument("--output", required=True, help="Calea raportului DOCX generat.")
    return parser


def build_request_from_args(args: argparse.Namespace) -> UiGenerationRequest:
    """Build a UiGenerationRequest from parsed CLI arguments."""

    return UiGenerationRequest(
        source_directory=args.source_directory,
        code=args.code,
        lot=args.lot,
        output_docx_path=args.output,
    )


def main(
    argv: list[str] | None = None,
    request_handler: UiRequestHandler = generate_report_from_ui_request,
) -> int:
    """Run the minimal CLI shell and return a process exit code."""

    parser = build_parser()
    args = parser.parse_args(argv)
    result = request_handler(build_request_from_args(args))

    if result.success:
        print(result.message)
        return 0

    print(result.error or result.message)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
