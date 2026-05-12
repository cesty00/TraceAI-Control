from __future__ import annotations

import re
from dataclasses import dataclass


PRE_LOT_SINGULAR = "singular"
PRE_LOT_REPEATED_IDENTICAL = "repeated_identical"
PRE_LOT_MULTI_LOT_DIFFERENT = "multi_lot_different"
PRE_LOT_UNCLEAR = "unclear"
PRE_LOT_QUANTITY_SUFFIX_RE = re.compile(r"\s*\(\s*cant\s*:\s*[^)]*\)\s*$")


@dataclass(frozen=True)
class PreLotClassification:
    kind: str
    normalized_value: str
    tokens: tuple[str, ...]


def classify_pre_lot(value: object) -> PreLotClassification:
    if not normalize_match_value(value):
        return PreLotClassification(PRE_LOT_UNCLEAR, "", ())

    tokens = split_normalized_lot_tokens(value)
    if not tokens:
        return PreLotClassification(PRE_LOT_UNCLEAR, "", ())

    normalized_value = ", ".join(tokens)

    if len(tokens) == 1:
        return PreLotClassification(PRE_LOT_SINGULAR, normalized_value, tokens)

    if len(set(tokens)) == 1:
        return PreLotClassification(PRE_LOT_REPEATED_IDENTICAL, normalized_value, tokens)

    return PreLotClassification(PRE_LOT_MULTI_LOT_DIFFERENT, normalized_value, tokens)


def pre_lot_matches_input(pre_lot_value: object, input_lot: object) -> bool:
    normalized_input = normalize_match_value(input_lot)
    if not normalized_input:
        return False

    classification = classify_pre_lot(pre_lot_value)
    if classification.kind not in (PRE_LOT_SINGULAR, PRE_LOT_REPEATED_IDENTICAL):
        return False
    return classification.tokens[0] == normalized_input


def split_normalized_lot_tokens(value: object) -> tuple[str, ...]:
    normalized_value = normalize_match_value(value)
    if not normalized_value:
        return ()

    raw_parts = re.split(r"[,;]", str(value).strip().casefold())
    normalized_parts = [normalize_match_value(part) for part in raw_parts]
    if any(part == "" for part in normalized_parts):
        return ()
    return tuple(normalized_parts)


def normalize_match_value(value: object) -> str:
    normalized = " ".join(str(value).strip().casefold().split())
    without_quantity = PRE_LOT_QUANTITY_SUFFIX_RE.sub("", normalized).strip()
    return " ".join(without_quantity.split())
