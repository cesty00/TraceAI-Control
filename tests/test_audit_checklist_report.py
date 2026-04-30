from src.audit.audit_checklist_report import (
    audit_checklist_report_to_dict,
    build_audit_checklist_report,
)
from src.audit.audit_traceability_report import build_audit_traceability_report
from tests.test_audit_traceability_report import make_case


def test_audit_checklist_report_exposes_required_checklist_sections() -> None:
    checklist = build_audit_checklist_report(build_audit_traceability_report(make_case()))

    requirements = [item.requirement for item in checklist.conformity]

    assert "01_EXERCITIU — fișa principală și bilanț produs finit" in requirements
    assert "02_TABEL_I_AMONTE — materii prime, ambalaje, auxiliare/gaz" in requirements
    assert "03_TABEL_II_AVAL — livrări produs finit" in requirements
    assert "04_PRODUCTIE_CONSUM — detaliere pe comenzi de producție" in requirements
    assert "05_FLUX_LOTURI_SI_DOCUMENTE — fluxuri și registru documente" in requirements
    assert all(item.status == "DA" for item in checklist.conformity)


def test_audit_checklist_report_maps_downstream_columns_required_by_checklist() -> None:
    checklist = build_audit_checklist_report(build_audit_traceability_report(make_case()))

    assert len(checklist.downstream) == 1
    delivery = checklist.downstream[0]

    assert delivery.client == "LIDL ROMAN"
    assert delivery.address == "FARA DATE IDENTIFICATE"
    assert delivery.delivery_date == "FARA DATE IDENTIFICATE"
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
    assert raw_material.receipt_date == "FARA DATE IDENTIFICATE"
    assert raw_material.supplier == "FARA DATE IDENTIFICATE"
    assert raw_material.document_type == "FARA DATE IDENTIFICATE"
    assert raw_material.document_number == "FARA DATE IDENTIFICATE"
    assert raw_material.document_date == "FARA DATE IDENTIFICATE"

    assert packaging.material_type == "Ambalaj"
    assert packaging.third_party_delivery_status == "Nu se aplică"
    assert gas.material_type == "Material auxiliar / gaz"
    assert gas.third_party_delivery_status == "Nu se aplică"


def test_audit_checklist_report_splits_wms_receipt_summary_when_available() -> None:
    traceability_case = make_case()
    raw_row = traceability_case.report_tables.order_traceability.rows[0]
    raw_row.values["Recepții WMS consum"] = "total 5000 Kilogram; 300005747/Fish Invest LTD: 5000 Kilogram"
    raw_row.values["Stoc consum la moment"] = "125 Kilogram; locații: Depozit Principal"

    checklist = build_audit_checklist_report(build_audit_traceability_report(traceability_case))
    raw_material = next(line for line in checklist.upstream if line.code == "DS099903930")

    assert raw_material.document_type == "WMS recepție"
    assert raw_material.document_number == "300005747"
    assert raw_material.supplier == "Fish Invest LTD"
    assert raw_material.stock_at_moment == "125 Kilogram; locații: Depozit Principal"


def test_audit_checklist_report_keeps_production_consumption_and_document_register() -> None:
    checklist = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    report_dict = audit_checklist_report_to_dict(checklist)

    assert len(checklist.production_consumption) == 3
    assert checklist.production_consumption[0].production_order == "0030412_DC"
    assert {row.consumed_code for row in checklist.production_consumption} == {"DS099903930", "10002", "60001"}
    assert checklist.lot_flows
    assert checklist.document_register
    assert report_dict["exercise"]["code"] == "DS099904011"
    assert report_dict["balance"]["prd_produced"] == "168 BUCATA"
