from __future__ import annotations

from dataclasses import dataclass, field
import unittest

from src.rules.pre_lot_classification import pre_lot_matches_input
from src.rules.pre_lot_multi_lot_prd_wms_split import (
    CONFIRMED,
    NEEDS_REVIEW,
    _confirm_finished_good_wms_quantity,
    _extract_multi_lot_prd_candidates,
    _multi_lot_different_has_exact_token,
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


def make_prd_row(
    pre_code: str,
    pre_lot: str,
    order: str = "0030518_AE",
    pre_quantity: str = "530",
    pre_unit: str = "KG",
    con_code: str = "RM-01",
    con_lot: str = "LOT-RM-01",
    con_name: str = "Materie prima",
    con_quantity: str = "12",
    con_unit: str = "KG",
) -> FakeRow:
    return FakeRow(
        row_number=1,
        values={
            "PRE_Cod Articol": pre_code,
            "PRE_LOT": pre_lot,
            "Numar Comanda": order,
            "PRE_Cantitate Predare": pre_quantity,
            "PRE_U.M.": pre_unit,
            "CON_Cod Articol": con_code,
            "CON_LOT": con_lot,
            "CON_Denumire Articol": con_name,
            "CON_Cantitate Consumata": con_quantity,
            "CON_U.M.": con_unit,
        },
    )


def make_wms_row(
    code: str,
    lot: str,
    quantity: str,
    operation: str = "livrare",
    unit: str = "KG",
    reason: str = "",
) -> FakeRow:
    return FakeRow(
        row_number=1,
        values={
            "Cod articol": code,
            "Lot": lot,
            "Cantitate": quantity,
            "Tip operatiune": operation,
            "UM": unit,
            "Cod-motiv": reason,
        },
    )


class MultiLotDifferentHelpersTests(unittest.TestCase):
    def test_exact_token_helper_accepts_only_exact_token_for_multi_lot_different(self) -> None:
        self.assertTrue(_multi_lot_different_has_exact_token("129.26F1, 129.26F2", "129.26F1"))
        self.assertFalse(_multi_lot_different_has_exact_token("129.26F11, 129.26F2", "129.26F1"))

    def test_quantity_suffix_remains_ignored_for_internal_exact_token_matching(self) -> None:
        self.assertTrue(_multi_lot_different_has_exact_token("129.26F1 (Cant: 262), 129.26F2 (Cant: 268)", "129.26F1"))

    def test_public_pre_lot_matching_still_rejects_multi_lot_different(self) -> None:
        self.assertFalse(pre_lot_matches_input("129.26F1, 129.26F2", "129.26F1"))

    def test_extract_multi_lot_prd_candidate_returns_order_and_consumption_context(self) -> None:
        dataset = FakeDataset(
            [
                FakeTable(
                    "production",
                    "raport_productie.csv",
                    "Sheet1",
                    [
                        make_prd_row("DS099904181", "129.26F1, 129.26F2", con_code="RM-01", con_lot="LOT-RM-01", con_quantity="12"),
                        make_prd_row("DS099904181", "129.26F1, 129.26F2", con_code="PKG-02", con_lot="LOT-PKG-02", con_quantity="3"),
                    ],
                )
            ]
        )

        candidates = _extract_multi_lot_prd_candidates(dataset, "DS099904181", "129.26F1")

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate.order_number, "0030518_AE")
        self.assertEqual(candidate.order_quantity_total, "530")
        self.assertEqual(candidate.order_unit, "KG")
        self.assertEqual(candidate.pre_lot_value, "129.26f1, 129.26f2")
        self.assertEqual([(item.code, item.lot, item.quantity) for item in candidate.consumptions], [("PKG-02", "LOT-PKG-02", "3"), ("RM-01", "LOT-RM-01", "12")])

    def test_extract_multi_lot_prd_candidate_requires_exact_product_code(self) -> None:
        dataset = FakeDataset([FakeTable("production", "raport_productie.csv", "Sheet1", [make_prd_row("DS099904182", "129.26F1, 129.26F2")])])
        self.assertEqual(_extract_multi_lot_prd_candidates(dataset, "DS099904181", "129.26F1"), ())

    def test_extract_multi_lot_prd_candidate_returns_empty_when_audited_lot_is_missing(self) -> None:
        dataset = FakeDataset([FakeTable("production", "raport_productie.csv", "Sheet1", [make_prd_row("DS099904181", "129.26F2, 129.26F3")])])
        self.assertEqual(_extract_multi_lot_prd_candidates(dataset, "DS099904181", "129.26F1"), ())

    def test_extract_multi_lot_prd_candidate_rejects_substring_token(self) -> None:
        dataset = FakeDataset([FakeTable("production", "raport_productie.csv", "Sheet1", [make_prd_row("DS099904181", "129.26F11, 129.26F2")])])
        self.assertEqual(_extract_multi_lot_prd_candidates(dataset, "DS099904181", "129.26F1"), ())

    def test_extract_multi_lot_prd_candidate_keeps_pre_quantity_as_order_total_context(self) -> None:
        dataset = FakeDataset([FakeTable("production", "raport_productie.csv", "Sheet1", [make_prd_row("DS099904181", "129.26F1, 129.26F2", pre_quantity="999")])])
        candidate = _extract_multi_lot_prd_candidates(dataset, "DS099904181", "129.26F1")[0]
        self.assertEqual(candidate.order_quantity_total, "999")
        self.assertFalse(hasattr(candidate, "lot_quantity"))

    def test_confirm_finished_good_wms_quantity_uses_only_exact_code_and_lot(self) -> None:
        dataset = FakeDataset(
            [
                FakeTable(
                    "wms",
                    "trasabilitate_wms.csv",
                    "Sheet1",
                    [
                        make_wms_row("DS099904181", "129.26F1", "10", operation="livrare"),
                        make_wms_row("DS099904181", "129.26F1", "5", operation="ajustare pozitiva", reason="production-out"),
                        make_wms_row("DS099904181", "129.26F11", "99", operation="livrare"),
                        make_wms_row("DS099904181X", "129.26F1", "77", operation="livrare"),
                    ],
                )
            ]
        )

        confirmation = _confirm_finished_good_wms_quantity(dataset, "DS099904181", "129.26F1")

        self.assertEqual(confirmation.status, CONFIRMED)
        self.assertTrue(confirmation.has_exact_confirmation)
        self.assertEqual(
            [(item.operation, item.reason, item.quantity, item.unit) for item in confirmation.confirmations],
            [("ajustare pozitiva", "production-out", "5", "KG"), ("livrare", "", "10", "KG")],
        )

    def test_confirm_finished_good_wms_quantity_rejects_substring_matches(self) -> None:
        dataset = FakeDataset([FakeTable("wms", "trasabilitate_wms.csv", "Sheet1", [make_wms_row("DS099904181", "129.26F11", "99")])])
        confirmation = _confirm_finished_good_wms_quantity(dataset, "DS099904181", "129.26F1")
        self.assertEqual(confirmation.status, NEEDS_REVIEW)
        self.assertFalse(confirmation.has_exact_confirmation)
        self.assertEqual(confirmation.confirmations, ())


if __name__ == "__main__":
    unittest.main()
