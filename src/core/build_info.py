"""Build metadata helpers for TraceAI Control.

The installed local application must expose enough build metadata to correlate a
DOCX report with the GitHub commit used to generate it. Packaged builds can set
these values through environment variables; source checkouts can fall back to
Git when available.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

UNKNOWN = "UNKNOWN"
APP_NAME = "TraceAI Control"
APP_VERSION = "0.5.0"

ENV_BUILD_COMMIT = "TRACEAI_BUILD_COMMIT"
ENV_BUILD_VERSION = "TRACEAI_BUILD_VERSION"
ENV_BUILD_DATE = "TRACEAI_BUILD_DATE"
ENV_BUILD_CHANNEL = "TRACEAI_BUILD_CHANNEL"


@dataclass(frozen=True)
class BuildInfo:
    """Stable build metadata shown in UI, JSON/diagnostics and DOCX."""

    app_name: str
    app_version: str
    build_commit: str
    build_date: str
    build_channel: str
    generated_at: str

    @property
    def short_commit(self) -> str:
        """Return a compact commit identifier suitable for UI display."""

        if not self.build_commit or self.build_commit == UNKNOWN:
            return UNKNOWN
        return self.build_commit[:12]


def get_build_info(generated_at: datetime | None = None) -> BuildInfo:
    """Return build metadata for the current application process."""

    now = generated_at or datetime.now(timezone.utc)
    commit = os.getenv(ENV_BUILD_COMMIT) or detect_git_commit() or UNKNOWN
    return BuildInfo(
        app_name=APP_NAME,
        app_version=os.getenv(ENV_BUILD_VERSION, APP_VERSION),
        build_commit=commit,
        build_date=os.getenv(ENV_BUILD_DATE, UNKNOWN),
        build_channel=os.getenv(ENV_BUILD_CHANNEL, "local"),
        generated_at=now.replace(microsecond=0).isoformat(),
    )


def build_info_to_dict(build_info: BuildInfo) -> dict[str, Any]:
    """Convert build info to a JSON-safe dictionary."""

    return asdict(build_info) | {"short_commit": build_info.short_commit}


def format_build_info_line(build_info: BuildInfo | None = None) -> str:
    """Format one compact build line for UI/status output."""

    info = build_info or get_build_info()
    return (
        f"{info.app_name} {info.app_version} | "
        f"commit {info.short_commit} | "
        f"channel {info.build_channel} | "
        f"generated {info.generated_at}"
    )


def build_info_table_rows(build_info: BuildInfo | None = None) -> list[list[str]]:
    """Return label/value rows for report rendering."""

    info = build_info or get_build_info()
    return [
        ["Aplicație", info.app_name],
        ["Versiune", info.app_version],
        ["Commit build", info.build_commit],
        ["Data build", info.build_date],
        ["Canal build", info.build_channel],
        ["Generat la", info.generated_at],
    ]


def detect_git_commit() -> str | None:
    """Try to detect the current Git commit from a source checkout."""

    repo_root = Path(__file__).resolve().parents[2]
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    commit = result.stdout.strip()
    return commit or None
