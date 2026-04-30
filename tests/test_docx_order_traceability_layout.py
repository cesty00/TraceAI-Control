from src.report.docx_minimal import build_document_xml
from src.rules.traceability_case import (
    TraceabilityCase,
    TraceabilityCaseSubject,
    TraceabilityReportTable,
    TraceabilityReportTables,
    TraceabilityTableRow,
)


def test_docx_renders_order_traceability_as_per_order_sections() -> None:
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
                    )
                ],
            ),
            finished_goods_deliveries=TraceabilityReportTable(
                key="finished_goods_deliveries",
                title="Livrări produs finit",
                columns=["Numar comanda", "Document comanda", "Client", "Cantitate", "UM"],
            ),
            raw_materials=TraceabilityReportTable("raw_materials", "Materii prime alimentare", ["Cod", "Lot", "Denumire", "Cantitate", "UM", "Rol"]),
            packaging=TraceabilityReportTable("packaging", "Ambalaje", ["Cod", "Lot", "Denumire", "Cantitate", "UM"]),
            auxiliaries_gas=TraceabilityReportTable("auxiliaries_gas", "Materiale auxiliare / gaz", ["Cod", "Lot", "Denumire", "Cantitate", "UM", "Observații"]),
            wms_receipts=TraceabilityReportTable("wms_receipts", "Recepții WMS", ["Numar comanda", "Document intrare", "Document comanda", "Furnizor", "Cantitate", "UM"]),
            prd_consumptions=TraceabilityReportTable("prd_consumptions", "Consumuri PRD", ["Cod", "Lot", "Comandă producție", "Cantitate", "UM"]),
            stock=TraceabilityReportTable("stock", "Stoc la moment", ["Cod", "Lot", "Stoc", "UM", "Locație"]),
            order_traceability=TraceabilityReportTable(
                key="order_traceability",
                title="Trasabilitate pe comenzi de producție",
                columns=[
                    "Comandă producție",
                    "Produs finit",
                    "Cantitate produs finit",
                    "UM produs finit",
                    "WMS production-out",
                    "Livrare produs finit asociată",
                    "Categorie consum",
                    "Cod consum",
                    "Lot consum",
                    "Denumire consum",
                    "Cantitate consum",
                    "UM consum",
                    "Livrări consum către terți",
                ],
                rows=[
                    TraceabilityTableRow(
                        values={
                            "Comandă producție": "0030518_AE",
                            "Produs finit": "PF-REFRIGERAT-P PASTRAV EVISCERAT GREUTATE VARIABILA ATM PENNY",
                            "Cantitate produs finit": "242",
                            "UM produs finit": "Kilogram",
                            "WMS production-out": "242 Kilogram",
                            "Livrare produs finit asociată": "WME111146 / 38760 / REWE / -242 Kilogram",
                            "Categorie consum": "Materie primă alimentară",
                            "Cod consum": "DS099903730",
                            "Lot consum": "L260409",
                            "Denumire consum": "REFRIGERAT-P PASTRAV EVISCERAT 300-400",
                            "Cantitate consum": "232",
                            "UM consum": "Kilogram",
                            "Livrări consum către terți": "NU",
                        },
                        source_key="production",
                    ),
                    TraceabilityTableRow(
                        values={
                            "Comandă producție": "0030518_AE",
                            "Produs finit": "PF-REFRIGERAT-P PASTRAV EVISCERAT GREUTATE VARIABILA ATM PENNY",
                            "Cantitate produs finit": "242",
                            "UM produs finit": "Kilogram",
                            "WMS production-out": "242 Kilogram",
                            "Livrare produs finit asociată": "WME111146 / 38760 / REWE / -242 Kilogram",
                            "Categorie consum": "Ambalaj",
                            "Cod consum": "10008",
                            "Lot consum": "270278",
                            "Denumire consum": "CUTIE FRESH DIM INTERIOARA 342x342x155MM",
                            "Cantitate consum": "61.2",
                            "UM consum": "BUCATA",
                            "Livrări consum către terți": "Nu se aplică",
                        },
                        source_key="production",
                    ),
                    TraceabilityTableRow(
                        values={
                            "Comandă producție": "0030518_AE",
                            "Produs finit": "PF-REFRIGERAT-P PASTRAV EVISCERAT GREUTATE VARIABILA ATM PENNY",
                            "Cantitate produs finit": "242",
                            "UM produs finit": "Kilogram",
                            "WMS production-out": "242 Kilogram",
                            "Livrare produs finit asociată": "WME111146 / 38760 / REWE / -242 Kilogram",
                            "Categorie consum": "Auxiliar / gaz",
                            "Cod consum": "60001",
                            "Lot consum": "08012026",
                            "Denumire consum": "GAZ ALIMENTAR ALISOL",
                            "Cantitate consum": "4.8",
                            "UM consum": "M3",
                            "Livrări consum către terți": "Nu se aplică",
                        },
                        source_key="production",
                    ),
                ],
            ),
        ),
    )

    xml = build_document_xml(case)

    assert "Trasabilitate pe comenzi de producție" in xml
    assert "Secțiunea este grupată pe comandă de producție pentru lizibilitate" in xml
    assert "7.1 Comanda producție 0030518_AE" in xml
    assert "Materii prime" in xml
    assert "Ambalaje" in xml
    assert "Materiale auxiliare / gaz" in xml
    assert "Livrări către terți" in xml
    assert "DS099903730" in xml
    assert "10008" in xml
    assert "60001" in xml
    assert "NU" in xml
