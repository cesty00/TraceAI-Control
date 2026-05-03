"""Robust discovery for official operational source files."""

from __future__ import annotations

import re
from pathlib import Path

SUPPORTED_EXTENSIONS = {".csv", ".xlsx"}

SOURCE_NAME_ALIASES: dict[str, tuple[str, ...]] = {
    "trasabilitate_wms.csv": (
        "trasabilitate_wms.csv",
        "trasabilitate wms.csv",
        "trasabilitate-wms.csv",
        "wms.csv",
        "wms trasabilitate.csv",
    ),
    "rapoarte productie.csv": (
        "rapoarte productie.csv",
        "rapoarte producție.csv",
        "raport_productie.csv",
        "raport productie.csv",
        "raport-producție.csv",
        "raport productie.csv",
        "productie.csv",
        "producție.csv",
        "prd.csv",
    ),
    "nomenclator.xlsx": (
        "nomenclator.xlsx",
        "nomenclator produse.xlsx",
        "nomenclator_produse.xlsx",
        "nomenclator articole.xlsx",
        "articole.xlsx",
    ),
    "stoc la moment original.xlsx": (
        "stoc la moment original.xlsx",
        "stoc_la_moment_original.xlsx",
        "stoc-la-moment-original.xlsx",
        "stoc la moment.xlsx",
        "stoc_la_moment.xlsx",
        "stoc moment.xlsx",
        "stoc.xlsx",
    ),
}


def find_official_source_path(root: Path, expected_name: str) -> Path | None:
    """Find an official source file by exact name, alias, or normalized name.

    The selected UI folder may be a parent folder, and Windows users often have
    extensions hidden while files use underscores instead of spaces. This helper
    keeps inventory strict by source role, but tolerant by file name spelling.
    """

    root = root.expanduser().resolve()
    direct = root / expected_name
    if direct.exists():
        return direct

    candidates = discover_supported_files(root)
    aliases = {normalize_source_filename(alias) for alias in SOURCE_NAME_ALIASES.get(expected_name, (expected_name,))}
    expected_normalized = normalize_source_filename(expected_name)

    exact_matches = [path for path in candidates if normalize_source_filename(path.name) == expected_normalized]
    if exact_matches:
        return nearest_path(root, exact_matches)

    alias_matches = [path for path in candidates if normalize_source_filename(path.name) in aliases]
    if alias_matches:
        return nearest_path(root, alias_matches)

    return None


def discover_supported_files(root: Path) -> list[Path]:
    """Return supported files below root, preferring deterministic order."""

    if not root.exists() or not root.is_dir():
        return []
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS)


def nearest_path(root: Path, candidates: list[Path]) -> Path:
    """Choose the closest deterministic match to root."""

    return sorted(candidates, key=lambda path: (len(path.relative_to(root).parts), str(path).casefold()))[0]


def normalize_source_filename(value: str) -> str:
    """Normalize spaces, underscores, hyphens, casing and Romanian diacritics."""

    path = Path(remove_diacritics(value).casefold().strip())
    suffix = path.suffix
    stem = re.sub(r"[^a-z0-9]+", "_", path.stem).strip("_")
    return f"{stem}{suffix}"


def remove_diacritics(value: str) -> str:
    """Remove Romanian diacritics for stable filename matching."""

    return value.translate(
        str.maketrans(
            {
                "ă": "a",
                "â": "a",
                "î": "i",
                "ș": "s",
                "ş": "s",
                "ț": "t",
                "ţ": "t",
                "Ă": "A",
                "Â": "A",
                "Î": "I",
                "Ș": "S",
                "Ş": "S",
                "Ț": "T",
                "Ţ": "T",
            }
        )
    )
