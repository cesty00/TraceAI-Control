import json
from dataclasses import asdict

from scripts.build_local_app import (
    BUILD_INFO_FILENAME,
    LocalBuildMetadata,
    build_metadata,
    pyinstaller_add_data_arg,
    write_build_info_file,
)


def test_write_build_info_file_creates_packaged_metadata(tmp_path) -> None:
    metadata = LocalBuildMetadata(
        app_version="1.2.3",
        build_commit="abcdef1234567890",
        build_date="2026-05-03T15:00:00+00:00",
        build_channel="test-build",
    )

    output = write_build_info_file(tmp_path, metadata)

    assert output == tmp_path / BUILD_INFO_FILENAME
    assert json.loads(output.read_text(encoding="utf-8")) == asdict(metadata)


def test_build_metadata_accepts_explicit_commit(monkeypatch) -> None:
    metadata = build_metadata(version="1.2.3", channel="test", commit="explicit-commit")

    assert metadata.app_version == "1.2.3"
    assert metadata.build_commit == "explicit-commit"
    assert metadata.build_channel == "test"
    assert metadata.build_date


def test_pyinstaller_add_data_arg_contains_source_and_target(tmp_path) -> None:
    source = tmp_path / BUILD_INFO_FILENAME
    value = pyinstaller_add_data_arg(source, ".")

    assert str(source) in value
    assert value.endswith(".")
