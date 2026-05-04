from src.audit.audit_checklist_report import (
    audit_checklist_report_to_dict,
    build_audit_checklist_report,
)
from src.audit.audit_traceability_report import STATUS_INCOMPLETE, build_audit_traceability_report
from tests.test_audit_traceability_report import make_case


def test_audit_checklist_report_exposes_required_checklist_sections() -> None:
    checklist = build_audit_checklist_report(build_audit_traceability_report(make_case()))

    items_by_requirement = {item.requirement: item for item in checklist.conformity}

    data_quality = items_by_requirement["00_DATA_QUALITY — verificare surse înainte de raport"]
    assert data_quality.status == "DA_CU_OBSERVATII"
    assert data_quality.evidence == "Status=WARNING; surse=4/4; erori=0; warning=2; issues=2"

    required_existing_sections = [
        "01_EXERCITIU — fișa principală și bilanț produs finit",
        "02_TABEL_I_AMONTE — materii prime, ambalaje, auxiliare/gaz",
        "03_TABEL_II_AVAL — livrări produs finit",
        "04_PRODUCTIE_CONSUM — detaliere pe comenzi de producție",
        "05_FLUX_LOTURI_SI_DOCUMENTE — fluxuri și registru documente",
    ]
    for requirement in required_existing_sections:
        assert requirement in items_by_requirement
        assert items_by_requirement[requirement].status == "DA"


def test_audit_checklist_report_marks_incomplete_finished_product_result() -> None:
    traceability_case = make_case()
    traceability_case.report_tables.raw_materials.rows.clear()
    traceability_case.report_tables.packaging.rows.clear()
    traceability_case.report_tables.auxiliaries_gas.rows.clear()
    traceability_case.report_tables.order_traceability.rows.clear()

    checklist = build_audit_checklist_report(build_audit_traceability_report(traceability_case))

    assert checklist.exercise.result == STATUS_INCOMPLETE
    assert checklist.conclusion_status == STATUS_INCOMPLETE
    assert any("Raport preliminar/incomplet" in observation for observation in checklist.observations)


def test_audit_checklist_report_maps_downstream_columns_required_by_checklist() -> None:
    checklist = build_audit_checklist_report(build_audit_traceability_report(make_case()))

    assert len(checklist.downstream) == 1
    delivery = checklist.downstream[0]

    assert delivery.client == "LIDL ROMAN"
    assert delivery.address == "DEPOZIT NORD"
    assert delivery.delivery_date == "2026-04-11"
    assert delivery.delivered_quantity == "-168 BUCATA"
    assert delivery.delivery_document_type == "WMS document livrare"
    assert delivery.delivery_document_number == "38569"
    assert delivery.wms_order == "WME110972"


def test_audit_checklist_report_maps_upstream_columns_required_by_checklist() -> None:
    checklist = build_audit_checklist_report(build_audit_traceability_report(make_case()))

    raw_material = next(line for line in checklist.upstream if line.code == "DS099903930")
    packaging = next(line for line in checklist.upstream if line.code == "10002")
    gas = next(line for line in checklist.upstream if line.code == "60001")

    assert raw_material.material_type == "Materie primă"
    assert raw_material.lot == "90924-070"
    assert raw_material.consumed_quantity == "85 Kilogram"
    assert raw_material.third_party_delivery_status == "NU"
    assert raw_material.receipt_date == "2026-04-09"
    assert raw_material.supplier == "Fish Invest LTD"
    assert raw_material.document_type == "WMS recepție"
    assert raw_material.document_number == "300005747"
    assert raw_material.document_date == "2026-04-09"

    assert packaging.material_type == "Ambalaj"
    assert packaging.third_party_delivery_status == "Nu se aplică"
    assert gas.material_type == "Material auxiliar / gaz"
    assert gas.third_party_delivery_status == "Nu se aplică"


def test_audit_checklist_report_splits_wms_receipt_summary_when_available() -> None:
    traceability_case = make_case()
    raw_row = traceability_case.report_tables.order_traceability.rows[0]
    raw_row.values["Recepții WMS consum"] = "total 5000 Kilogram; 300005747/Fish Invest LTD/2026-04-10: 5000 Kilogram"
    raw_row.values["Stoc consum la moment"] = "125 Kilogram; locații: Depozit Principal"

    checklist = build_audit_checklist_report(build_audit_traceability_report(traceability_case))
    raw_material = next(line for line in checklist.upstream if line.code == "DS099903930")

    assert raw_material.document_type == "WMS recepție"
    assert raw_material.document_number == "300005747"
    assert raw_material.supplier == "Fish Invest LTD"
    assert raw_material.receipt_date == "2026-04-10"
    assert raw_material.document_date == "2026-04-10"
    assert raw_material.stock_at_moment == "125 Kilogram; locații: Depozit Principal"


def test_audit_checklist_report_splits_wms_receipt_summary_with_slash_date() -> None:
    traceability_case = make_case()
    raw_row = traceability_case.report_tables.order_traceability.rows[0]
    raw_row.values["Recepții WMS consum"] = "total 5000 Kilogram; 300005747/Fish Invest LTD/14/01/2026 11:54:40: 5000 Kilogram"

    checklist = build_audit_checklist_report(build_audit_traceability_report(traceability_case))
    raw_material = next(line for line in checklist.upstream if line.code == "DS099903930")

    assert raw_material.document_number == "300005747"
    assert raw_material.supplier == "Fish Invest LTD"
    assert raw_material.receipt_date == "14/01/2026"
    assert raw_material.document_date == "14/01/2026"


def test_audit_checklist_report_keeps_production_consumption_and_document_register() -> None:
    checklist = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    report_dict = audit_checklist_report_to_dict(checklist)

    assert len(checklist.production_consumption) == 3
    assert checklist.production_consumption[0].production_order == "0030412_DC"
    assert checklist.production_consumption[0].production_date == "2026-04-10"
    assert {row.consumed_code for row in checklist.production_consumption} == {"DS099903930", "10002", "60001"}
    assert checklist.lot_flows
    assert checklist.document_register
    assert report_dict["exercise"]["code"] == "DS099904011"
    assert report_dict["data_quality"]["status"] == "WARNING"
    assert report_dict["balance"]["prd_produced"] == "168 BUCATA"
    assert report_dict["production_consumption"][0]["production_date"] == "2026-04-10"
