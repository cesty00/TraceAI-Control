from src.rules.order_traceability_mapping import (
    MISSING,
    SourceRow,
    build_wms_production_out_dates_by_order,
    fill_missing_production_dates,
)


def test_build_wms_production_out_dates_by_order_uses_real_wms_dates() -> None:
    rows = [
        make_wms_row(
            order="0030518_AE",
            code="DS099903883",
            lot="105.26",
            quantity="242",
            operation_date="15/04/2026 18:10:00",
        ),
        make_wms_row(
            order="0030520_AE",
            code="DS099903883",
            lot="105.26",
            quantity="209",
            operation_date="15/04/2026 18:12:00",
        ),
        make_wms_row(
            order="IGNORED_OTHER_LOT",
            code="DS099903883",
            lot="999.99",
            quantity="1",
            operation_date="16/04/2026 10:00:00",
        ),
    ]

    dates = build_wms_production_out_dates_by_order(rows, "DS099903883", "105.26")

    assert dates == {
        "0030518_AE": "15/04/2026 18:10:00",
        "0030520_AE": "15/04/2026 18:12:00",
    }


def test_build_wms_production_out_dates_by_order_deduplicates_multiple_rows_for_same_order() -> None:
    rows = [
        make_wms_row("0030518_AE", "DS099903883", "105.26", "100", "15/04/2026 18:10:00"),
        make_wms_row("0030518_AE", "DS099903883", "105.26", "142", "15/04/2026 18:10:00"),
        make_wms_row("0030518_AE", "DS099903883", "105.26", "0", "15/04/2026 18:11:00"),
    ]

    dates = build_wms_production_out_dates_by_order(rows, "DS099903883", "105.26")

    assert dates == {"0030518_AE": "15/04/2026 18:10:00; 15/04/2026 18:11:00"}


def test_fill_missing_production_dates_uses_wms_production_out_fallback_only_when_missing() -> None:
    production_by_order = {
        "0030518_AE": {"production_date": MISSING},
        "0030520_AE": {"production_date": "2026-04-15"},
        "0030558_AE": {},
    }
    dates_by_order = {
        "0030518_AE": "15/04/2026 18:10:00",
        "0030520_AE": "15/04/2026 18:12:00",
        "0030558_AE": "15/04/2026 19:00:00",
    }

    fill_missing_production_dates(production_by_order, dates_by_order)

    assert production_by_order["0030518_AE"]["production_date"] == "15/04/2026 18:10:00"
    assert production_by_order["0030520_AE"]["production_date"] == "2026-04-15"
    assert production_by_order["0030558_AE"]["production_date"] == "15/04/2026 19:00:00"


def make_wms_row(
    order: str,
    code: str,
    lot: str,
    quantity: str,
    operation_date: str,
) -> SourceRow:
    return SourceRow(
        source_key="wms",
        source_name="trasabilitate_wms.csv",
        sheet_name=None,
        row_number=1,
        values={
            "Cod articol": code,
            "Lot": lot,
            "Tip operatiune": "Ajustare pozitiva",
            "Cod-motiv": "production-out",
            "Numar comanda": order,
            "Cantitate": quantity,
            "UM": "Kilogram",
            "Data": operation_date,
        },
        original_values={},
    )
