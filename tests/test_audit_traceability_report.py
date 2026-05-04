from src.audit.audit_traceability_report import (
    STATUS_PASS,
    THIRD_PARTY_NO,
    THIRD_PARTY_NOT_APPLICABLE,
    audit_traceability_report_to_dict,
    build_audit_traceability_report,
)
from src.rules.traceability_case import (
    TraceabilityCase,
    TraceabilityCaseSubject,
    TraceabilityReportTable,
    TraceabilityReportTables,
    TraceabilityTableRow,
)


def make_report_tables() -> TraceabilityReportTables:
    return TraceabilityReportTables(
        production=TraceabilityReportTable(
            key="production",
            title="Producția lotului",
            columns=["Cod", "Lot", "Denumire", "Comandă", "Cantitate", "UM", "Data producției", "Observații"],
            rows=[
                TraceabilityTableRow(
                    values={
                        "Cod": "DS099904011",
                        "Lot": "103.26",
                        "Denumire": "PF-REFRIGERAT-FD CREVETI PREFIERTI 20/30 500G ATM LIDL",
                        "Comandă": "0030412_DC",
                        "Cantitate": "168",
                        "UM": "BUCATA",
                        "Data producției": "2026-04-10",
                    },
                    source_key="production",
                    source_name="rapoarte productie.csv",
                    row_number=10,
                )
            ],
        ),
        finished_goods_deliveries=TraceabilityReportTable(
            key="finished_goods_deliveries",
            title="Livrări produs finit",
            columns=["Numar comanda", "Document comanda", "Client", "Data livrare", "Cantitate", "UM"],
            rows=[
                TraceabilityTableRow(
                    values={
                        "Numar comanda": "WME110972",
                        "Document comanda": "38569",
                        "Client": "LIDL ROMAN - DEPOZIT NORD",
                        "Data livrare": "2026-04-11",
                        "Cantitate": "-168",
                        "UM": "BUCATA",
                    },
                    source_key="wms",
                    source_name="trasabilitate_wms.csv",
                    row_number=20,
                )
            ],
        ),
        raw_materials=TraceabilityReportTable(
            key="raw_materials",
            title="Materii prime alimentare",
            columns=["Cod", "Lot", "Denumire", "Cantitate", "UM", "Rol"],
            rows=[
                TraceabilityTableRow(
                    values={
                        "Cod": "DS099903930",
                        "Lot": "90924-070",
                        "Denumire": "CREVETI INTREGI PREFIERTI 20-30 BAX 5 KG",
                        "Cantitate": "85",
                        "UM": "Kilogram",
                        "Rol": "materie primă alimentară",
                    },
                    source_key="production",
                    source_name="rapoarte productie.csv",
                    row_number=11,
                )
            ],
        ),
        packaging=TraceabilityReportTable(
            key="packaging",
            title="Ambalaje",
            columns=["Cod", "Lot", "Denumire", "Cantitate", "UM"],
            rows=[
                TraceabilityTableRow(
                    values={
                        "Cod": "10002",
                        "Lot": "281340",
                        "Denumire": "CUTIE FRESH DIM INTERIOARA 342x342x208MM",
                        "Cantitate": "21.42",
                        "UM": "BUCATA",
                    },
                    source_key="production",
                    source_name="rapoarte productie.csv",
                    row_number=12,
                )
            ],
        ),
        auxiliaries_gas=TraceabilityReportTable(
            key="auxiliaries_gas",
            title="Materiale auxiliare / gaz",
            columns=["Cod", "Lot", "Denumire", "Cantitate", "UM", "Observații"],
            rows=[
                TraceabilityTableRow(
                    values={
                        "Cod": "60001",
                        "Lot": "09.04.26",
                        "Denumire": "GAZ ALIMENTAR ALISOL",
                        "Cantitate": "1.89",
                        "UM": "M3",
                        "Observații": "gaz tehnologic",
                    },
                    source_key="production",
                    source_name="rapoarte productie.csv",
                    row_number=13,
                )
            ],
        ),
        wms_receipts=TraceabilityReportTable(
            key="wms_receipts",
            title="Recepții WMS",
            columns=["Numar comanda", "Document intrare", "Document comanda", "Furnizor", "Cantitate", "UM"],
        ),
        prd_consumptions=TraceabilityReportTable(
            key="prd_consumptions",
            title="Consumuri PRD",
            columns=["Cod", "Lot", "Comandă producție", "Cantitate", "UM"],
        ),
        stock=TraceabilityReportTable(
            key="stock",
            title="Stoc la moment",
            columns=["Cod", "Lot", "Stoc", "UM", "Locație"],
        ),
        order_traceability=TraceabilityReportTable(
            key="order_traceability",
            title="Trasabilitate pe comenzi de producție",
            columns=[
                "Comandă producție",
                "Produs finit",
                "Cantitate produs finit",
                "UM produs finit",
                "Data producției",
                "WMS production-out",
                "Livrare produs finit asociată",
                "Categorie consum",
                "Cod consum",
                "Lot consum",
                "Denumire consum",
                "Cantitate consum",
                "UM consum",
                "Livrări consum către terți",
                "Recepții WMS consum",
                "Stoc consum la moment",
            ],
            rows=[
                TraceabilityTableRow(
                    values={
                        "Comandă producție": "0030412_DC",
                        "Produs finit": "PF-REFRIGERAT-FD CREVETI PREFIERTI 20/30 500G ATM LIDL",
                        "Cantitate produs finit": "168",
                        "UM produs finit": "BUCATA",
                        "Data producției": "2026-04-10",
                        "WMS production-out": "168 BUCATA",
                        "Livrare produs finit asociată": "WME110972 / 38569 / LIDL ROMAN / -168 BUCATA",
                        "Categorie consum": "Materie primă alimentară",
                        "Cod consum": "DS099903930",
                        "Lot consum": "90924-070",
                        "Denumire consum": "CREVETI INTREGI PREFIERTI 20-30 BAX 5 KG",
                        "Cantitate consum": "85",
                        "UM consum": "Kilogram",
                        "Livrări consum către terți": "NU",
                        "Recepții WMS consum": "total 5000 Kilogram; 300005747/Fish Invest LTD/2026-04-09: 5000 Kilogram",
                        "Stoc consum la moment": "125 Kilogram; locații: Depozit Principal",
                    },
                    source_key="production",
                    source_name="rapoarte productie.csv",
                    row_number=11,
                ),
                TraceabilityTableRow(
                    values={
                        "Comandă producție": "0030412_DC",
                        "Produs finit": "PF-REFRIGERAT-FD CREVETI PREFIERTI 20/30 500G ATM LIDL",
                        "Cantitate produs finit": "168",
                        "UM produs finit": "BUCATA",
                        "Data producției": "2026-04-10",
                        "WMS production-out": "168 BUCATA",
                        "Livrare produs finit asociată": "WME110972 / 38569 / LIDL ROMAN / -168 BUCATA",
                        "Categorie consum": "Ambalaj",
                        "Cod consum": "10002",
                        "Lot consum": "281340",
                        "Denumire consum": "CUTIE FRESH DIM INTERIOARA 342x342x208MM",
                        "Cantitate consum": "21.42",
                        "UM consum": "BUCATA",
                        "Livrări consum către terți": "Nu se aplică",
                    },
                    source_key="production",
                    source_name="rapoarte productie.csv",
                    row_number=12,
                ),
                TraceabilityTableRow(
                    values={
                        "Comandă producție": "0030412_DC",
                        "Produs finit": "PF-REFRIGERAT-FD CREVETI PREFIERTI 20/30 500G ATM LIDL",
                        "Cantitate produs finit": "168",
                        "UM produs finit": "BUCATA",
                        "Data producției": "2026-04-10",
                        "WMS production-out": "168 BUCATA",
                        "Livrare produs finit asociată": "WME110972 / 38569 / LIDL ROMAN / -168 BUCATA",
                        "Categorie consum": "Auxiliar / gaz",
                        "Cod consum": "60001",
                        "Lot consum": "09.04.26",
                        "Denumire consum": "GAZ ALIMENTAR ALISOL",
                        "Cantitate consum": "1.89",
                        "UM consum": "M3",
                        "Livrări consum către terți": "Nu se aplică",
                    },
                    source_key="production",
                    source_name="rapoarte productie.csv",
                    row_number=13,
                ),
            ],
        ),
    )


def make_case() -> TraceabilityCase:
    return TraceabilityCase(
        subject=TraceabilityCaseSubject(
            code="DS099904011",
            lot="103.26",
            case_type="FINISHED_PRODUCT",
        ),
        sections={
            "core_validation_status": "VALID",
            "selected_record_count": 83,
            "data_quality": {
                "status": "WARNING",
                "source_count": 4,
                "sources_found": 4,
                "error_count": 0,
                "warning_count": 2,
                "issue_count": 2,
            },
        },
        report_tables=make_report_tables(),
    )


def test_build_audit_traceability_report_maps_core_audit_sections() -> None:
    report = build_audit_traceability_report(make_case())

    assert report.exercise.code == "DS099904011"
    assert report.exercise.lot == "103.26"
    assert report.exercise.product_name == "PF-REFRIGERAT-FD CREVETI PREFIERTI 20/30 500G ATM LIDL"
    assert report.exercise.traceability_result == STATUS_PASS
    assert report.balance.prd_produced_quantity == "168"
    assert report.balance.prd_produced_um == "BUCATA"
    assert report.balance.wms_production_out_quantity == "168"
    assert report.balance.wms_production_out_um == "BUCATA"
    assert report.balance.wms_delivered_quantity == "-168"
    assert report.balance.wms_delivered_um == "BUCATA"
    assert report.data_quality["status"] == "WARNING"
    assert report.data_quality["source_count"] == 4
    assert len(report.downstream) == 1
    assert report.downstream[0].document_number == "38569"
    assert report.downstream[0].delivery_date == "2026-04-11"
    assert len(report.upstream) == 3
    assert len(report.production_orders) == 1
    assert report.production_orders[0].production_order == "0030412_DC"
    assert report.production_orders[0].production_date == "2026-04-10"
    assert report.production_orders[0].associated_delivery == "WME110972 / 38569 / LIDL ROMAN / -168 BUCATA"
    assert report.production_orders[0].raw_materials[0].third_party_delivery_status == THIRD_PARTY_NO
    assert report.production_orders[0].raw_materials[0].receipt_summary == "total 5000 Kilogram; 300005747/Fish Invest LTD/2026-04-09: 5000 Kilogram"
    assert report.production_orders[0].packaging[0].code == "10002"
    assert report.production_orders[0].auxiliaries_gas[0].code == "60001"
    assert report.conclusion.status == STATUS_PASS


def test_audit_report_to_dict_is_json_ready_and_keeps_document_register() -> None:
    report_dict = audit_traceability_report_to_dict(build_audit_traceability_report(make_case()))

    assert report_dict["exercise"]["code"] == "DS099904011"
    assert report_dict["data_quality"]["status"] == "WARNING"
    assert report_dict["downstream"][0]["delivery_date"] == "2026-04-11"
    assert report_dict["production_orders"][0]["production_date"] == "2026-04-10"
    assert report_dict["production_orders"][0]["raw_materials"][0]["third_party_delivery_status"] == THIRD_PARTY_NO
    assert report_dict["production_orders"][0]["packaging"][0]["third_party_delivery_status"] == THIRD_PARTY_NOT_APPLICABLE
    document_references = {item["document_reference"] for item in report_dict["physical_documents"]}
    assert "0030412_DC" in document_references
    assert "38569" in document_references
    assert "total 5000 Kilogram; 300005747/Fish Invest LTD/2026-04-09: 5000 Kilogram" in document_references
    assert report_dict["source_lot_flows"]
