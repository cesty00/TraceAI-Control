from src.core.dataset_validation import ValidationReport
from src.core.normalized_dataset import NormalizedColumn, NormalizedDataSet, NormalizedRow, NormalizedTable
from src.core.record_selection import select_records_by_code_lot
from src.core.run_pipeline import CorePipelineResult
from src.core.source_inventory import InventoryReport
from src.rules.case_type_detection import CASE_FINISHED_PRODUCT, detect_case_type
from src.rules.run_rules_pipeline import RulesPipelineResult
from src.rules.traceability_case import (
    ALISOL_AUXILIARY_OBSERVATION,
    PACKAGING_ROLE,
    RAW_MATERIAL_ROLE,
    TraceabilityReportTable,
    TraceabilityTableRow,
    build_empty_report_tables,
    build_preliminary_balance,
    build_traceability_case,
    parse_clear_decimal,
    report_tables_as_list,
    traceability_case_to_dict,
)


def make_table(source_key: str, source_name: str, values: dict[str, str]) -> NormalizedTable:
    return NormalizedTable(
        source_key=source_key,
        source_name=source_name,
        sheet_name=None,
        columns=[NormalizedColumn(name, name) for name in values.keys()],
        rows=[
            NormalizedRow(
                row_number=2,
                values=values,
                original_values=values,
                code_lot_hints={"code": values.get("cod", values.get("Cod articol", "")), "lot": values.get("lot", values.get("Lot", ""))},
            )
        ],
        row_count=1,
    )


def make_rules_result(tables: list[NormalizedTable]) -> RulesPipelineResult:
    dataset = NormalizedDataSet(source_directory="/tmp/data", tables=tables)
    selection = select_records_by_code_lot(dataset, "DS0001", "L001")
    detection = detect_case_type(dataset, selection, "DS0001", "L001")
    core = CorePipelineResult(
        inventory=InventoryReport(source_directory="/tmp/data", expected_sources=[], sources=[]),
        normalized_dataset=dataset,
        validation=ValidationReport(status="VALID"),
        selection=selection,
    )
    return RulesPipelineResult(core=core, case_type_detection=detection)


def test_build_traceability_case_maps_rules_pipeline_metadata() -> None:
    rules = make_rules_result([make_table("production", "rapoarte productie.csv", {"cod": "DS0001", "lot": "L001"})])
    traceability_case = traceability_case_to_dict(build_traceability_case(rules, "DS0001", "L001"))
    assert traceability_case["subject"] == {"code": "DS0001", "lot": "L001", "case_type": CASE_FINISHED_PRODUCT}
    assert traceability_case["evidence"]
    assert traceability_case["sections"]["core_validation_status"] == "VALID"
    assert traceability_case["sections"]["selected_record_count"] == 1
    assert traceability_case["report_tables"]["production"]["title"] == "Producția lotului"
    assert traceability_case["report_tables"]["stock"]["empty_message"]
    assert "order_traceability" in traceability_case["report_tables"]
    assert "preliminary_balance" in traceability_case


def test_build_empty_report_tables_contains_expected_sections_in_display_order() -> None:
    tables = report_tables_as_list(build_empty_report_tables())
    assert [table.key for table in tables] == [
        "production",
        "finished_goods_deliveries",
        "raw_materials",
        "packaging",
        "auxiliaries_gas",
        "wms_receipts",
        "prd_consumptions",
        "stock",
        "order_traceability",
    ]
    assert all(table.columns for table in tables)
    assert all(table.empty_message for table in tables)
    assert all(table.rows == [] for table in tables)


def test_build_traceability_case_populates_selected_report_tables() -> None:
    rules = make_rules_result(
        [
            make_table("production", "rapoarte productie.csv", {"cod": "DS0001", "lot": "L001", "cantitate": "10", "um": "kg"}),
            make_table("wms", "trasabilitate_wms.csv", {"cod": "DS0001", "lot": "L001", "document intrare": "NIR-1", "cantitate": "10"}),
            make_table("stock", "stoc la moment original.xlsx", {"cod": "DS0001", "lot": "L001", "stoc": "5", "um": "kg"}),
        ]
    )
    traceability_case = traceability_case_to_dict(build_traceability_case(rules, "DS0001", "L001"))
    production_rows = traceability_case["report_tables"]["production"]["rows"]
    wms_rows = traceability_case["report_tables"]["wms_receipts"]["rows"]
    stock_rows = traceability_case["report_tables"]["stock"]["rows"]
    assert production_rows[0]["values"]["cantitate"] == "10"
    assert production_rows[0]["source_key"] == "production"
    assert wms_rows[0]["values"]["document intrare"] == "NIR-1"
    assert wms_rows[0]["values"]["Document intrare"] == "NIR-1"
    assert wms_rows[0]["source_key"] == "wms"
    assert stock_rows[0]["values"]["stoc"] == "5"
    assert stock_rows[0]["source_key"] == "stock"
    assert traceability_case["report_tables"]["raw_materials"]["rows"] == []


def test_wms_aliases_are_exposed_for_docx_without_overwriting_source_keys() -> None:
    rules = make_rules_result(
        [
            make_table(
                "wms",
                "trasabilitate_wms.csv",
                {
                    "cod": "DS0001",
                    "lot": "L001",
                    "nr_document_intrare": "NIR-77",
                    "doc_comanda": "AVZ-77",
                    "beneficiar": "Client alias",
                    "supplier": "Furnizor alias",
                    "qty": "12",
                    "unitate_masura": "Kilogram",
                },
            )
        ]
    )
    traceability_case = traceability_case_to_dict(build_traceability_case(rules, "DS0001", "L001"))
    receipt_values = traceability_case["report_tables"]["wms_receipts"]["rows"][0]["values"]
    assert receipt_values["Document intrare"] == "NIR-77"
    assert receipt_values["Furnizor"] == "Furnizor alias"
    assert receipt_values["Cantitate"] == "12"
    assert receipt_values["UM"] == "Kilogram"


def test_wms_only_finished_good_rows_do_not_create_false_upstream_lines() -> None:
    rules = make_rules_result(
        [
            make_table(
                "wms",
                "trasabilitate_wms.csv",
                {
                    "Cod articol": "DS0001",
                    "Lot": "L001",
                    "Denumire": "PF-REFRIGERAT-P PASTRAV EVISCERAT GREUTATE VARIABILA",
                    "Tip operatiune": "Livrare",
                    "Document comanda": "38748",
                    "Numar comanda": "WME111147",
                    "Partener": "REWE (ROMANIA) SRL_DEPOZIT FILIASI",
                    "Cantitate": "-33",
                    "UM": "Kilogram",
                    "Data": "15/04/2026 18:24:30",
                },
            )
        ]
    )

    traceability_case = traceability_case_to_dict(build_traceability_case(rules, "DS0001", "L001"))

    assert traceability_case["report_tables"]["finished_goods_deliveries"]["rows"]
    assert traceability_case["report_tables"]["raw_materials"]["rows"] == []
    assert traceability_case["report_tables"]["packaging"]["rows"] == []
    assert traceability_case["report_tables"]["auxiliaries_gas"]["rows"] == []
    assert traceability_case["report_tables"]["prd_consumptions"]["rows"] == []
    assert traceability_case["report_tables"]["order_traceability"]["rows"] == []


def test_alisol_is_classified_as_auxiliary_gas_not_raw_material() -> None:
    rules = make_rules_result([make_table("production", "rapoarte productie.csv", {"cod": "DS0001", "lot": "L001", "denumire": "Gaz ALISOL", "cantitate": "2", "um": "kg"})])
    traceability_case = traceability_case_to_dict(build_traceability_case(rules, "DS0001", "L001"))
    auxiliary_rows = traceability_case["report_tables"]["auxiliaries_gas"]["rows"]
    raw_material_rows = traceability_case["report_tables"]["raw_materials"]["rows"]
    production_rows = traceability_case["report_tables"]["production"]["rows"]
    assert auxiliary_rows[0]["values"]["denumire"] == "Gaz ALISOL"
    assert auxiliary_rows[0]["values"]["Observații"] == ALISOL_AUXILIARY_OBSERVATION
    assert raw_material_rows == []
    assert production_rows == []
    assert ALISOL_AUXILIARY_OBSERVATION in traceability_case["observations"]


def test_selected_rows_with_explicit_hints_are_classified_as_raw_materials_and_packaging() -> None:
    rules = make_rules_result(
        [
            make_table("production", "rapoarte productie.csv", {"cod": "DS0001", "lot": "L001", "denumire": "Materie primă zahăr", "cantitate": "3", "um": "kg"}),
            make_table("production", "rapoarte productie.csv", {"cod": "DS0001", "lot": "L001", "denumire": "Folie ambalaj", "cantitate": "4", "um": "buc"}),
        ]
    )
    traceability_case = traceability_case_to_dict(build_traceability_case(rules, "DS0001", "L001"))
    raw_rows = traceability_case["report_tables"]["raw_materials"]["rows"]
    packaging_rows = traceability_case["report_tables"]["packaging"]["rows"]
    production_rows = traceability_case["report_tables"]["production"]["rows"]
    assert raw_rows[0]["values"]["denumire"] == "Materie primă zahăr"
    assert raw_rows[0]["values"]["Rol"] == RAW_MATERIAL_ROLE
    assert packaging_rows[0]["values"]["denumire"] == "Folie ambalaj"
    assert packaging_rows[0]["values"]["Rol"] == PACKAGING_ROLE
    assert production_rows == []


def test_alisol_priority_over_raw_material_hint() -> None:
    rules = make_rules_result([make_table("production", "rapoarte productie.csv", {"cod": "DS0001", "lot": "L001", "denumire": "ALISOL materie primă", "cantitate": "2", "um": "kg"})])
    traceability_case = traceability_case_to_dict(build_traceability_case(rules, "DS0001", "L001"))
    assert traceability_case["report_tables"]["auxiliaries_gas"]["rows"]
    assert traceability_case["report_tables"]["raw_materials"]["rows"] == []


def test_wms_delivery_rows_are_mapped_to_finished_goods_deliveries() -> None:
    rules = make_rules_result(
        [
            make_table("wms", "trasabilitate_wms.csv", {"cod": "DS0001", "lot": "L001", "document comanda": "CMD-OUT-1", "client": "Client test", "cantitate": "7"}),
            make_table("wms", "trasabilitate_wms.csv", {"cod": "DS0001", "lot": "L001", "document intrare": "NIR-1", "furnizor": "Furnizor test", "cantitate": "10"}),
        ]
    )
    traceability_case = traceability_case_to_dict(build_traceability_case(rules, "DS0001", "L001"))
    delivery_rows = traceability_case["report_tables"]["finished_goods_deliveries"]["rows"]
    receipt_rows = traceability_case["report_tables"]["wms_receipts"]["rows"]
    assert delivery_rows[0]["values"]["document comanda"] == "CMD-OUT-1"
    assert delivery_rows[0]["values"]["client"] == "Client test"
    assert delivery_rows[0]["source_key"] == "wms"
    assert receipt_rows[0]["values"]["document intrare"] == "NIR-1"
    assert receipt_rows[0]["values"]["Document intrare"] == "NIR-1"
    assert receipt_rows[0]["source_key"] == "wms"


def test_preliminary_balance_groups_clear_numeric_values_by_unit_without_conversion() -> None:
    tables = build_empty_report_tables()
    production = TraceabilityReportTable(
        key="production",
        title="Producția lotului",
        columns=["Cod", "Lot", "Cantitate", "UM"],
        rows=[
            TraceabilityTableRow(values={"Cod": "DS0001", "Lot": "L001", "Cantitate": "10", "UM": "kg"}),
            TraceabilityTableRow(values={"Cod": "DS0001", "Lot": "L001", "Cantitate": "2,5", "UM": "kg"}),
            TraceabilityTableRow(values={"Cod": "DS0001", "Lot": "L001", "Cantitate": "3", "UM": "buc"}),
        ],
        empty_message="Nu au fost identificate date detaliate de producție în TraceabilityCase.",
    )
    report_tables = type(tables)(production, tables.finished_goods_deliveries, tables.raw_materials, tables.packaging, tables.auxiliaries_gas, tables.wms_receipts, tables.prd_consumptions, tables.stock, tables.order_traceability)
    balance = build_preliminary_balance(report_tables)
    totals = {(line.table_key, line.unit): line.total for line in balance.lines}
    assert totals[("production", "kg")] == "12.5"
    assert totals[("production", "buc")] == "3"
    assert any("nu se fac conversii automate" in message for message in balance.messages)


def test_preliminary_balance_skips_unclear_values_and_reports_message() -> None:
    tables = build_empty_report_tables()
    stock = TraceabilityReportTable(
        key="stock",
        title="Stoc la moment",
        columns=["Cod", "Lot", "Stoc", "UM"],
        rows=[
            TraceabilityTableRow(values={"Cod": "DS0001", "Lot": "L001", "Stoc": "5", "UM": "kg"}),
            TraceabilityTableRow(values={"Cod": "DS0001", "Lot": "L001", "Stoc": "1.234,50", "UM": "kg"}),
            TraceabilityTableRow(values={"Cod": "DS0001", "Lot": "L001", "Stoc": "abc", "UM": "kg"}),
            TraceabilityTableRow(values={"Cod": "DS0001", "Lot": "L001", "Stoc": "2", "UM": ""}),
        ],
        empty_message="Articolul nu apare explicit în stocul la moment în TraceabilityCase.",
    )
    report_tables = type(tables)(tables.production, tables.finished_goods_deliveries, tables.raw_materials, tables.packaging, tables.auxiliaries_gas, tables.wms_receipts, tables.prd_consumptions, stock, tables.order_traceability)
    balance = build_preliminary_balance(report_tables)
    assert balance.lines[0].total == "5"
    assert balance.lines[0].skipped_row_count == 3
    assert any("3 rând(uri) ignorate" in message for message in balance.messages)


def test_parse_clear_decimal_rejects_mixed_separators_and_text() -> None:
    assert str(parse_clear_decimal("10")) == "10"
    assert str(parse_clear_decimal("2,5")) == "2.5"
    assert parse_clear_decimal("1.234,50") is None
    assert parse_clear_decimal("abc") is None
