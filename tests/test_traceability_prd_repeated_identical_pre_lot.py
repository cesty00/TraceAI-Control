from __future__ import annotations

from dataclasses import dataclass, field
import unittest

from src.rules.order_traceability_mapping import matching_prd_rows as order_matching_prd_rows
from src.rules.pre_lot_classification import (
    PRE_LOT_MULTI_LOT_DIFFERENT,
    PRE_LOT_REPEATED_IDENTICAL,
    PRE_LOT_SINGULAR,
    PRE_LOT_UNCLEAR,
    classify_pre_lot,
)
from src.rules.prd_table_mapping import (
    build_prd_component_rows,
    build_source_specific_rows,
    matching_prd_rows,
    pre_lot_matches_input,
)


@dataclass
class FakeRow:
    row_number: int
    values: dict[str, str]
    original_values: dict[str, str] = field(default_factory=dict)
    code_lot_hints: dict[str, str] = field(default_factory=dict)


@dataclass
class FakeTable:
    source_key: str
    source_name: str
    sheet_name: str | None
    rows: list[FakeRow]


@dataclass
class FakeDataset:
    tables: list[FakeTable]


@dataclass
class FakeSelection:
    input_code: str
    input_lot: str
    records: list[object] = field(default_factory=list)


@dataclass
class FakeCore:
    normalized_dataset: FakeDataset
    selection: FakeSelection


@dataclass
class FakeResult:
    core: FakeCore


def make_production_row(pre_code: str, pre_lot: str, con_code: str = "100001", con_lot: str = "PKG-1", con_name: str = "Ambalaj folie", qty: str = "12") -> FakeRow:
    return FakeRow(
        row_number=1,
        values={
            "PRE_Cod Articol": pre_code,
            "PRE_LOT": pre_lot,
            "Numar Comanda": "0030518_AE",
            "CON_Cod Articol": con_code,
            "CON_LOT": con_lot,
            "CON_Denumire Articol": con_name,
            "CON_Cantitate Consumata": qty,
            "CON_U.M.": "KG",
        },
    )


def make_result(code: str, lot: str, rows: list[FakeRow]) -> FakeResult:
    dataset = FakeDataset([FakeTable("production", "raport_productie.csv", "Sheet1", rows)])
    return FakeResult(FakeCore(dataset, FakeSelection(code, lot)))


class PreLotClassificationTests(unittest.TestCase):
    def test_singular_classified_correctly(self) -> None:
        classification = classify_pre_lot("092.26")
        self.assertEqual(classification.kind, PRE_LOT_SINGULAR)
        self.assertEqual(classification.tokens, ("092.26",))

    def test_repeated_identical_classified_correctly(self) -> None:
        classification = classify_pre_lot("092.26, 092.26, 092.26")
        self.assertEqual(classification.kind, PRE_LOT_REPEATED_IDENTICAL)
        self.assertEqual(classification.tokens, ("092.26", "092.26", "092.26"))

    def test_multi_lot_different_classified_correctly(self) -> None:
        classification = classify_pre_lot("092.26, 093.26")
        self.assertEqual(classification.kind, PRE_LOT_MULTI_LOT_DIFFERENT)

    def test_blank_classified_unclear(self) -> None:
        self.assertEqual(classify_pre_lot("   ").kind, PRE_LOT_UNCLEAR)

    def test_malformed_no_useful_token_classified_unclear(self) -> None:
        self.assertEqual(classify_pre_lot("092.26, ,092.26").kind, PRE_LOT_UNCLEAR)
        self.assertEqual(classify_pre_lot(";;;").kind, PRE_LOT_UNCLEAR)

    def test_comma_separator_supported(self) -> None:
        self.assertEqual(classify_pre_lot("092.26,092.26").kind, PRE_LOT_REPEATED_IDENTICAL)

    def test_semicolon_separator_supported(self) -> None:
        self.assertEqual(classify_pre_lot("092.26; 092.26").kind, PRE_LOT_REPEATED_IDENTICAL)

    def test_whitespace_normalization(self) -> None:
        classification = classify_pre_lot("  092.26 ;   092.26  ")
        self.assertEqual(classification.kind, PRE_LOT_REPEATED_IDENTICAL)
        self.assertEqual(classification.tokens, ("092.26", "092.26"))

    def test_quantity_suffix_singular_classified_correctly(self) -> None:
        classification = classify_pre_lot("061.26 (Cant: 240)")
        self.assertEqual(classification.kind, PRE_LOT_SINGULAR)
        self.assertEqual(classification.tokens, ("061.26",))

    def test_quantity_suffix_repeated_identical_classified_correctly(self) -> None:
        classification = classify_pre_lot("090.26 (Cant: 731), 090.26 (Cant: 2425)")
        self.assertEqual(classification.kind, PRE_LOT_REPEATED_IDENTICAL)
        self.assertEqual(classification.tokens, ("090.26", "090.26"))

    def test_quantity_suffix_multi_lot_different_classified_correctly(self) -> None:
        classification = classify_pre_lot("129.26F1 (Cant: 262), 129.26F2 (Cant: 268)")
        self.assertEqual(classification.kind, PRE_LOT_MULTI_LOT_DIFFERENT)
        self.assertEqual(classification.tokens, ("129.26f1", "129.26f2"))


class RepeatedPreLotMatchTests(unittest.TestCase):
    def test_pre_lot_matches_input_accepts_singular(self) -> None:
        self.assertTrue(pre_lot_matches_input("092.26", "092.26"))

    def test_pre_lot_matches_input_accepts_repeated_identical(self) -> None:
        self.assertTrue(pre_lot_matches_input("092.26, 092.26, 092.26", "092.26"))

    def test_pre_lot_matches_input_rejects_multi_lot_different(self) -> None:
        self.assertFalse(pre_lot_matches_input("092.26, 093.26", "092.26"))

    def test_pre_lot_matches_input_rejects_unclear(self) -> None:
        self.assertFalse(pre_lot_matches_input("092.26, ,092.26", "092.26"))
        self.assertFalse(pre_lot_matches_input("", "092.26"))

    def test_pre_lot_free_substring_matching_is_not_allowed(self) -> None:
        self.assertFalse(pre_lot_matches_input("X092.26", "092.26"))
        self.assertFalse(pre_lot_matches_input("129.26F14, 129.26F13", "129.26"))

    def test_quantity_suffix_matches_singular_input(self) -> None:
        self.assertTrue(pre_lot_matches_input("061.26 (Cant: 240)", "061.26"))

    def test_quantity_suffix_matches_repeated_identical_input(self) -> None:
        self.assertTrue(pre_lot_matches_input("090.26 (Cant: 731), 090.26 (Cant: 2425)", "090.26"))

    def test_quantity_suffix_multi_lot_is_rejected_as_match(self) -> None:
        self.assertFalse(pre_lot_matches_input("129.26F1 (Cant: 262), 129.26F2 (Cant: 268)", "129.26F1"))

    def test_quantity_suffix_substring_matching_remains_rejected(self) -> None:
        self.assertFalse(pre_lot_matches_input("061.26X (Cant: 240)", "061.26"))

    def test_product_code_remains_exactly_required(self) -> None:
        result = make_result("DS099904181", "092.26", [make_production_row("DS099904182", "092.26")])
        self.assertEqual(matching_prd_rows(result), [])
        self.assertEqual(order_matching_prd_rows(result.core.normalized_dataset, "DS099904181", "092.26"), [])

    def test_repeated_identical_pre_lot_matches_prd_rows_for_ds099904181_equivalent_fixture(self) -> None:
        result = make_result("DS099904181", "092.26", [make_production_row("DS099904181", "092.26, 092.26, 092.26")])
        self.assertEqual(len(matching_prd_rows(result)), 1)
        self.assertEqual(len(order_matching_prd_rows(result.core.normalized_dataset, "DS099904181", "092.26")), 1)

    def test_repeated_identical_quantity_suffix_matches_prd_rows(self) -> None:
        result = make_result("DS099904181", "090.26", [make_production_row("DS099904181", "090.26 (Cant: 731), 090.26 (Cant: 2425)")])
        self.assertEqual(len(matching_prd_rows(result)), 1)
        self.assertEqual(len(order_matching_prd_rows(result.core.normalized_dataset, "DS099904181", "090.26")), 1)

    def test_multi_lot_quantity_suffix_is_rejected_in_prd_matching(self) -> None:
        result = make_result("DS099904181", "129.26F1", [make_production_row("DS099904181", "129.26F1 (Cant: 262), 129.26F2 (Cant: 268)")])
        self.assertEqual(matching_prd_rows(result), [])
        self.assertEqual(order_matching_prd_rows(result.core.normalized_dataset, "DS099904181", "129.26F1"), [])

    def test_component_classification_is_unchanged_and_packaging_only_appears_after_prd_match(self) -> None:
        matching_result = make_result("DS099904181", "092.26", [make_production_row("DS099904181", "092.26, 092.26")])
        mismatching_result = make_result("DS099904181", "092.26", [make_production_row("DS099904181", "092.26, 093.26")])

        matched_packaging = build_source_specific_rows(matching_result)["packaging"]
        unmatched_packaging = build_source_specific_rows(mismatching_result)["packaging"]

        self.assertEqual(len(matched_packaging), 1)
        self.assertEqual(matched_packaging[0].values["Cod"], "100001")
        self.assertEqual(unmatched_packaging, [])

    def test_build_prd_component_rows_stays_empty_when_prd_rows_are_not_found(self) -> None:
        result = make_result("DS099904181", "092.26", [make_production_row("DS099904181", "092.26, 093.26")])
        self.assertEqual(build_prd_component_rows(matching_prd_rows(result), {}, "packaging"), [])


if __name__ == "__main__":
    unittest.main()
