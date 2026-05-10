from src.audit.audit_checklist_report import build_audit_checklist_report
from src.audit.audit_traceability_report import build_audit_traceability_report
from src.report.audit_checklist_docx import QUICK_AUDITOR_GUIDE_ITEMS, build_document_xml
from tests.test_audit_traceability_report import make_case


def test_audit_checklist_docx_quick_guide_places_amonte_before_aval() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    xml = build_document_xml(report)
    assert "Ghidul rapid indică ordinea recomandată de citire: verdict, Data Quality, conformare checklist, AMONTE, AVAL, consumuri, fluxuri, registru și build." in xml
    assert xml.index("02_TABEL_I_AMONTE") < xml.index("03_TABEL_II_AVAL")


def test_audit_checklist_docx_amonte_is_finished_product_and_deliveries() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    xml = build_document_xml(report)
    assert "02_TABEL_I_AMONTE — Produs finit, producție și livrări" in xml
    assert "Amonte / produs finit, producție și livrări" in xml
    assert "Repere produs finit și lot auditat" in xml
    assert "Cod produs finit" in xml
    assert "Bilanț produs finit" in xml
    assert "Livrări produs finit" in xml
    assert "Cantitate livrată" in xml


def test_audit_checklist_docx_aval_is_materials_and_source_lots() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    xml = build_document_xml(report)
    assert "03_TABEL_II_AVAL — Materii prime, ambalaje, auxiliare și loturi sursă" in xml
    assert "Aval / materii prime, ambalaje și loturi sursă" in xml
    assert "Materie primă / ambalaj" in xml
    assert "Tip material" in xml


def test_audit_checklist_docx_data_quality_stays_before_amonte() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    xml = build_document_xml(
        report,
        data_quality_summary={"status": "WARNING", "source_count": 4, "sources_found": 4, "error_count": 0, "warning_count": 8, "issue_count": 8, "issues": []},
    )
    assert xml.index("Sumar Data Quality") < xml.index("02_TABEL_I_AMONTE")


def test_audit_checklist_docx_terms_are_not_inverted() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    xml = build_document_xml(report)
    assert "02_TABEL_I_AMONTE — Produs finit, producție și livrări" in xml
    assert "03_TABEL_II_AVAL — Materii prime, ambalaje, auxiliare și loturi sursă" in xml
    assert "Verifică AMONTE: produs finit, producție și livrări." in xml
    assert "Verifică AVAL: materii prime, ambalaje, auxiliare și loturi sursă." in xml


def test_audit_checklist_docx_uses_pp03_section_order() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    xml = build_document_xml(report)
    assert xml.index("Card verdict auditor") < xml.index("Sumar Data Quality")
    assert xml.index("Sumar Data Quality") < xml.index("Rezumat de conformare checklist")
    assert xml.index("Rezumat de conformare checklist") < xml.index("02_TABEL_I_AMONTE")
    assert xml.index("02_TABEL_I_AMONTE") < xml.index("03_TABEL_II_AVAL")
    assert xml.index("03_TABEL_II_AVAL") < xml.index("04_PRODUCTIE_CONSUM")
    assert xml.index("04_PRODUCTIE_CONSUM") < xml.index("05_FLUX_LOTURI_SI_DOCUMENTE")
    assert xml.index("05_FLUX_LOTURI_SI_DOCUMENTE") < xml.index("Registru documente fizice de pregătit pentru auditor")
    assert xml.index("Registru documente fizice de pregătit pentru auditor") < xml.index("Informații build raport")


def test_audit_checklist_docx_contains_quick_auditor_guide_points() -> None:
    report = build_audit_checklist_report(build_audit_traceability_report(make_case()))
    xml = build_document_xml(report)
    for guide_item in QUICK_AUDITOR_GUIDE_ITEMS:
        assert guide_item in xml
