from datetime import datetime, timezone

from src.core import build_info as module
from src.core.build_info import BuildInfo, format_build_info_line, get_build_info, read_packaged_build_info


def test_get_build_info_uses_packaged_resource_when_env_is_absent(monkeypatch, tmp_path) -> None:
    resource = tmp_path / "traceai_build_info.json"
    resource.write_text(
        '{"app_version":"9.9.9","build_commit":"abcdef1234567890","build_date":"build-date","build_channel":"packaged"}',
        encoding="utf-8",
    )
    monkeypatch.delenv("TRACEAI_BUILD_COMMIT", raising=False)
    monkeypatch.delenv("TRACEAI_BUILD_VERSION", raising=False)
    monkeypatch.delenv("TRACEAI_BUILD_DATE", raising=False)
    monkeypatch.delenv("TRACEAI_BUILD_CHANNEL", raising=False)
    monkeypatch.setenv("TRACEAI_BUILD_INFO_FILE", str(resource))
    monkeypatch.setattr(module, "detect_git_commit", lambda: None)

    info = get_build_info(datetime(2026, 5, 3, 12, 0, tzinfo=timezone.utc))

    assert info == BuildInfo(
        app_name="TraceAI Control",
        app_version="9.9.9",
        build_commit="abcdef1234567890",
        build_date="build-date",
        build_channel="packaged",
        generated_at="2026-05-03T12:00:00+00:00",
    )
    assert info.short_commit == "abcdef123456"


def test_env_vars_override_packaged_resource(monkeypatch, tmp_path) -> None:
    resource = tmp_path / "traceai_build_info.json"
    resource.write_text(
        '{"app_version":"resource-version","build_commit":"resource-commit","build_date":"resource-date","build_channel":"resource"}',
        encoding="utf-8",
    )
    monkeypatch.setenv("TRACEAI_BUILD_INFO_FILE", str(resource))
    monkeypatch.setenv("TRACEAI_BUILD_COMMIT", "env-commit")
    monkeypatch.setenv("TRACEAI_BUILD_VERSION", "env-version")
    monkeypatch.setenv("TRACEAI_BUILD_DATE", "env-date")
    monkeypatch.setenv("TRACEAI_BUILD_CHANNEL", "env-channel")
    monkeypatch.setattr(module, "detect_git_commit", lambda: "git-commit")

    info = get_build_info(datetime(2026, 5, 3, 12, 0, tzinfo=timezone.utc))

    assert info.app_version == "env-version"
    assert info.build_commit == "env-commit"
    assert info.build_date == "env-date"
    assert info.build_channel == "env-channel"


def test_git_is_used_after_missing_resource(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("TRACEAI_BUILD_INFO_FILE", str(tmp_path / "missing.json"))
    monkeypatch.delenv("TRACEAI_BUILD_COMMIT", raising=False)
    monkeypatch.delenv("TRACEAI_BUILD_VERSION", raising=False)
    monkeypatch.delenv("TRACEAI_BUILD_DATE", raising=False)
    monkeypatch.delenv("TRACEAI_BUILD_CHANNEL", raising=False)
    monkeypatch.setattr(module, "detect_git_commit", lambda: "git-commit")

    info = get_build_info(datetime(2026, 5, 3, 12, 0, tzinfo=timezone.utc))

    assert info.build_commit == "git-commit"
    assert info.app_version == "0.5.0"


def test_invalid_packaged_resource_is_ignored(monkeypatch, tmp_path) -> None:
    resource = tmp_path / "traceai_build_info.json"
    resource.write_text("not-json", encoding="utf-8")
    monkeypatch.setenv("TRACEAI_BUILD_INFO_FILE", str(resource))

    assert read_packaged_build_info() == {}


def test_format_build_info_line_is_compact() -> None:
    line = format_build_info_line(
        BuildInfo(
            app_name="TraceAI Control",
            app_version="1.0.0",
            build_commit="abcdef1234567890",
            build_date="build-date",
            build_channel="local",
            generated_at="generated-at",
        )
    )

    assert line == "TraceAI Control 1.0.0 | commit abcdef123456 | channel local | generated generated-at"
