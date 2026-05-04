"""Build the local TraceAI Control visual app with packaged build metadata.

This script is intentionally small and explicit. It prepares the metadata file
read by ``src.core.build_info`` and, when requested, invokes PyInstaller so the
installed app can show the real Git commit in the UI and DOCX reports.

Usage examples:

    python scripts/build_local_app.py --metadata-only
    python scripts/build_local_app.py
    python scripts/build_local_app.py --channel release --version 0.5.1
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

APP_NAME = "TraceAI-Control"
DEFAULT_VERSION = "0.5.0"
DEFAULT_CHANNEL = "local-build"
BUILD_INFO_FILENAME = "traceai_build_info.json"


@dataclass(frozen=True)
class LocalBuildMetadata:
    """Metadata bundled into packaged builds."""

    app_version: str
    build_commit: str
    build_date: str
    build_channel: str



def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]



def run_command(args: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(
        args,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()



def detect_git_commit(root: Path) -> str:
    try:
        return run_command(["git", "rev-parse", "HEAD"], cwd=root)
    except (OSError, subprocess.SubprocessError):
        return "UNKNOWN"



def build_metadata(version: str, channel: str, commit: str | None = None) -> LocalBuildMetadata:
    root = repo_root()
    return LocalBuildMetadata(
        app_version=version,
        build_commit=commit or detect_git_commit(root),
        build_date=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        build_channel=channel,
    )



def write_build_info_file(output_dir: Path, metadata: LocalBuildMetadata) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / BUILD_INFO_FILENAME
    path.write_text(json.dumps(asdict(metadata), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path



def clean_build_outputs(root: Path) -> None:
    for relative in ("build", "dist"):
        target = root / relative
        if target.exists():
            shutil.rmtree(target)



def pyinstaller_add_data_arg(source: Path, target_name: str) -> str:
    separator = ";" if sys.platform.startswith("win") else ":"
    return f"{source}{separator}{target_name}"



def run_pyinstaller(root: Path, metadata_file: Path, onefile: bool = False) -> None:
    pyinstaller = shutil.which("pyinstaller")
    if pyinstaller is None:
        raise RuntimeError("PyInstaller nu este instalat. Rulează: pip install pyinstaller")

    entry_script = root / "src" / "ui" / "launch.py"
    command = [
        pyinstaller,
        "--noconfirm",
        "--clean",
        "--name",
        APP_NAME,
        "--add-data",
        pyinstaller_add_data_arg(metadata_file, "."),
    ]
    if onefile:
        command.append("--onefile")
    else:
        command.append("--onedir")
    command.append(str(entry_script))
    subprocess.run(command, cwd=root, check=True)



def copy_metadata_next_to_onedir_executable(root: Path, metadata_file: Path) -> Path | None:
    """Copy metadata next to onedir executable for direct inspection/use."""

    app_dir = root / "dist" / APP_NAME
    if not app_dir.exists():
        return None
    target = app_dir / BUILD_INFO_FILENAME
    shutil.copy2(metadata_file, target)
    return target



def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build local TraceAI Control app with build metadata.")
    parser.add_argument("--version", default=DEFAULT_VERSION, help="Application version written to build metadata.")
    parser.add_argument("--channel", default=DEFAULT_CHANNEL, help="Build channel written to build metadata.")
    parser.add_argument("--commit", help="Override detected Git commit.")
    parser.add_argument("--metadata-only", action="store_true", help="Only generate traceai_build_info.json; do not run PyInstaller.")
    parser.add_argument("--onefile", action="store_true", help="Build a one-file PyInstaller executable instead of onedir.")
    parser.add_argument("--no-clean", action="store_true", help="Do not remove build/ and dist/ before building.")
    return parser.parse_args(argv)



def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = repo_root()
    if not args.no_clean:
        clean_build_outputs(root)

    metadata = build_metadata(args.version, args.channel, args.commit)
    metadata_file = write_build_info_file(root / "build" / "metadata", metadata)
    print(f"Build metadata written: {metadata_file}")
    print(json.dumps(asdict(metadata), ensure_ascii=False, indent=2))

    if args.metadata_only:
        return 0

    run_pyinstaller(root, metadata_file, onefile=args.onefile)
    copied = copy_metadata_next_to_onedir_executable(root, metadata_file)
    if copied is not None:
        print(f"Build metadata copied next to executable: {copied}")
    print(f"Build completed. Output folder: {root / 'dist'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())