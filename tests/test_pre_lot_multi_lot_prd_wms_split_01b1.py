from __future__ import annotations

from dataclasses import dataclass, field
import unittest

from src.rules.order_traceability_mapping import matching_prd_rows as order_matching_prd_rows
from src.rules.pre_lot_classification import pre_lot_matches_input
from src.rules.pre_lot_multi_lot_prd_wms_split import _extract_multi_lot_prd_candidates
from src.rules.prd_table_mapping import matching_prd_rows as report_matching_prd_rows


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


def make_prd_row(
    pre_code: str,
    pre_lot: str,
    *,
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
    *,
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


def make_dataset(production_rows: list[FakeRow], wms_rows: list[FakeRow] | None = None) -> FakeDataset:
    tables = [FakeTable("production", "raport_productie.csv", "Sheet1", production_rows)]
    if wms_rows is not None:
        tables.append(FakeTable("wms", "trasabilitate_wms.csv", "Sheet1", wms_rows))
    return FakeDataset(tables)


def make_result(code: str, lot: str, production_rows: list[FakeRow], wms_rows: list[FakeRow] | None = None) -> FakeResult:
    dataset = make_dataset(production_rows, wms_rows)
    return FakeResult(FakeCore(dataset, FakeSelection(code, lot)))


class InternalMultiLotHelpers01B1Tests(unittest.TestCase):
    def test_internal_helper_extracts_multi_lot_different_candidate(self) -> None:
        dataset = make_dataset(
            [make_prd_row("DS099904181", "129.26F1, 129.26F2")],
            [make_wms_row("DS099904181", "129.26F1", "10")],
        )

        candidates = _extract_multi_lot_prd_candidates(dataset, "DS099904181", "129.26F1")

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].order_number, "0030518_AE")
        self.assertEqual(candidates[0].matched_token, "129.26f1")
        self.assertEqual(candidates[0].order_quantity_total, "530")


class PrdTableMapping01B1Tests(unittest.TestCase):
    def test_public_matching_success_returns_rows_without_internal_fallback(self) -> None:
        result = make_result(
            "DS099904181",
            "090.26",
            [make_prd_row("DS099904181", "090.26 (Cant: 731), 090.26 (Cant: 2425)")],
        )

        rows = report_matching_prd_rows(result)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].values["PRE_LOT"], "090.26 (Cant: 731), 090.26 (Cant: 2425)")

    def test_public_matching_keeps_multi_lot_different_out_of_public_output(self) -> None:
        result = make_result(
            "DS099904181",
            "129.26F1",
            [make_prd_row("DS099904181", "129.26F1, 129.26F2")],
            [make_wms_row("DS099904181", "129.26F1", "10")],
        )

        self.assertEqual(report_matching_prd_rows(result), [])

    def test_public_matching_returns_empty_without_exact_wms_code_lot_confirmation(self) -> None:
        result = make_result(
            "DS099904181",
            "129.26F1",
            [make_prd_row("DS099904181", "129.26F1, 129.26F2")],
            [make_wms_row("DS099904181", "129.26F11", "10")],
        )

        self.assertEqual(report_matching_prd_rows(result), [])

    def test_public_matching_returns_empty_for_substring_lot_only(self) -> None:
        result = make_result(
            "DS099904181",
            "129.26F1",
            [make_prd_row("DS099904181", "129.26F11, 129.26F2")],
            [make_wms_row("DS099904181", "129.26F1", "10")],
        )

        self.assertEqual(report_matching_prd_rows(result), [])

    def test_public_matching_returns_empty_for_product_code_mismatch(self) -> None:
        result = make_result(
            "DS099904181",
            "129.26F1",
            [make_prd_row("DS099904182", "129.26F1, 129.26F2")],
            [make_wms_row("DS099904181", "129.26F1", "10")],
        )

        self.assertEqual(report_matching_prd_rows(result), [])


class OrderTraceabilityMapping01B1Tests(unittest.TestCase):
    def test_public_matching_success_returns_rows_without_internal_fallback(self) -> None:
        dataset = make_dataset(
            [make_prd_row("DS099904181", "090.26 (Cant: 731), 090.26 (Cant: 2425)")]
        )

        rows = order_matching_prd_rows(dataset, "DS099904181", "090.26")

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].values["PRE_LOT"], "090.26 (Cant: 731), 090.26 (Cant: 2425)")

    def test_public_matching_keeps_multi_lot_different_out_of_public_output(self) -> None:
        dataset = make_dataset(
            [make_prd_row("DS099904181", "129.26F1, 129.26F2")],
            [make_wms_row("DS099904181", "129.26F1", "10")],
        )

        self.assertEqual(order_matching_prd_rows(dataset, "DS099904181", "129.26F1"), [])

    def test_public_matching_returns_empty_without_exact_wms_confirmation(self) -> None:
        dataset = make_dataset(
            [make_prd_row("DS099904181", "129.26F1, 129.26F2")],
            [make_wms_row("DS099904181", "129.26F11", "10")],
        )

        self.assertEqual(order_matching_prd_rows(dataset, "DS099904181", "129.26F1"), [])

    def test_public_matching_returns_empty_for_substring_token(self) -> None:
        dataset = make_dataset(
            [make_prd_row("DS099904181", "129.26F11, 129.26F2")],
            [make_wms_row("DS099904181", "129.26F1", "10")],
        )

        self.assertEqual(order_matching_prd_rows(dataset, "DS099904181", "129.26F1"), [])

    def test_public_matching_returns_empty_when_public_case_is_not_multi_lot_different(self) -> None:
        dataset = make_dataset(
            [make_prd_row("DS099904181", "129.26F1")],
            [make_wms_row("DS099904181", "129.26F1", "10")],
        )

        rows = order_matching_prd_rows(dataset, "DS099904181", "129.26F2")
        self.assertEqual(rows, [])


class PreLotPublicNonRegression01B1Tests(unittest.TestCase):
    def test_public_pre_lot_matching_contract_remains_unchanged(self) -> None:
        self.assertTrue(pre_lot_matches_input("092.26", "092.26"))
        self.assertTrue(pre_lot_matches_input("092.26, 092.26, 092.26", "092.26"))
        self.assertFalse(pre_lot_matches_input("129.26F1, 129.26F2", "129.26F1"))

    def test_pre_cantitate_predare_remains_order_total_context_not_lot_quantity(self) -> None:
        dataset = make_dataset(
            [make_prd_row("DS099904181", "129.26F1, 129.26F2", pre_quantity="999")]
        )

        candidate = _extract_multi_lot_prd_candidates(dataset, "DS099904181", "129.26F1")[0]

        self.assertEqual(candidate.order_quantity_total, "999")
        self.assertFalse(hasattr(candidate, "lot_quantity"))


if __name__ == "__main__":
    unittest.main()