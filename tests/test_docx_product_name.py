from src.report.docx_minimal import build_document_xml
from src.rules.traceability_case import (
    TraceabilityCase,
    TraceabilityCaseSubject,
    TraceabilityReportTable,
    TraceabilityReportTables,
    TraceabilityTableRow,
)


def test_docx_header_prefers_finished_product_name_over_raw_material_name() -> None:
    case = TraceabilityCase(
        subject=TraceabilityCaseSubject(
            code="DS099903883",
            lot="105.26",
            case_type="FINISHED_PRODUCT",
        ),
        sections={"core_validation_status": "VALID", "selected_record_count": 51},
        report_tables=TraceabilityReportTables(
            production=TraceabilityReportTable(
                key="production",
                title="Producția lotului",
                columns=["Cod", "Lot", "Denumire", "Comandă", "Cantitate", "UM", "Observații"],
                rows=[
                    TraceabilityTableRow(
                        values={
                            "Cod": "DS099903883",
                            "Lot": "105.26",
                            "Denumire": "PF-REFRIGERAT-P PASTRAV EVISCERAT GREUTATE VARIABILA ATM PENNY",
                            "Comandă": "0030518_AE",
                            "Cantitate": "242",
                            "UM": "Kilogram",
                        },
                        source_key="production",
                        source_name="rapoarte productie.csv",
                    )
                ],
            ),
            finished_goods_deliveries=TraceabilityReportTable(
                key="finished_goods_deliveries",
                title="Livrări produs finit",
                columns=["Numar comanda", "Document comanda", "Client", "Cantitate", "UM"],
                rows=[
                    TraceabilityTableRow(
                        values={
                            "Numar comanda": "WME111146",
                            "Document comanda": "38760",
                            "Client": "REWE",
                            "Cantitate": "-242",
                            "UM": "Kilogram",
                        },
                        source_key="wms",
                        source_name="trasabilitate_wms.csv",
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
                            "Cod": "DS099903730",
                            "Lot": "L260409",
                            "Denumire": "REFRIGERAT-P PASTRAV EVISCERAT 300-400",
                            "Cantitate": "432",
                            "UM": "Kilogram",
                            "Rol": "materie primă alimentară",
                        },
                        source_key="production",
                        source_name="rapoarte productie.csv",
                    )
                ],
            ),
            packaging=TraceabilityReportTable("packaging", "Ambalaje", ["Cod", "Lot", "Denumire", "Cantitate", "UM"]),
            auxiliaries_gas=TraceabilityReportTable("auxiliaries_gas", "Materiale auxiliare / gaz", ["Cod", "Lot", "Denumire", "Cantitate", "UM", "Observații"]),
            wms_receipts=TraceabilityReportTable("wms_receipts", "Recepții WMS", ["Numar comanda", "Document intrare", "Document comanda", "Furnizor", "Cantitate", "UM"]),
            prd_consumptions=TraceabilityReportTable("prd_consumptions", "Consumuri PRD", ["Cod", "Lot", "Comandă producție", "Cantitate", "UM"]),
            stock=TraceabilityReportTable("stock", "Stoc la moment", ["Cod", "Lot", "Stoc", "UM", "Locație"]),
        ),
    )

    xml = build_document_xml(case)

    assert "Produs: PF-REFRIGERAT-P PASTRAV EVISCERAT GREUTATE VARIABILA ATM PENNY" in xml
    assert "Denumire produs: REFRIGERAT-P PASTRAV EVISCERAT 300-400" not in xml
    assert "Surse utilizate: PRD, WMS" in xml
