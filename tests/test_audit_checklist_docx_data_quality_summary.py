from dataclasses import replace

from src.audit.audit_checklist_report import build_audit_checklist_report
from src.audit.audit_traceability_report import build_audit_traceability_report
from src.report.audit_checklist_docx import (
    build_document_xml,
    sync_docx_data_quality_from_source,
)
from src.ui.audit_checklist_json import audit_checklist_ui_payload_from_report
from tests.test_audit_traceability_report import make_case


def warning_data_quality(issue_count: int = 1, warning_count: int = 1) -> dict[str, object]:
    return {
        'status': 'WARNING',
        'source_count': 4,
        'sources_found': 4,
        'error_count': 0,
        'warning_count': warning_count,
        'issue_count': issue_count,
        'issues': [
            {
                'severity': 'WARNING',
                'source_name': 'nomenclator.xlsx',
                'sheet_name': 'Sheet2',
                'column_name': 'cod articol/produs',
                'message': 'Lipsește coloana obligatorie pentru cod articol/produs.',
            }
        ],
    }


def make_docx_report(
    *,
    code: str = 'DS099904011',
    lot: str = '103.26',
    data_quality: dict[str, object] | None = None,
    observations: list[str] | None = None,
):
    traceability_case = make_case()
    sections = dict(traceability_case.sections)
    sections['data_quality'] = data_quality or warning_data_quality()
    traceability_case = replace(
        traceability_case,
        subject=replace(traceability_case.subject, code=code, lot=lot),
        sections=sections,
        observations=list(observations or []),
    )
    report = build_audit_checklist_report(build_audit_traceability_report(traceability_case))
    sync_docx_data_quality_from_source(report, sections['data_quality'])
    return report, sections['data_quality']


def test_audit_checklist_docx_includes_short_data_quality_summary() -> None:
    report, _data_quality = make_docx_report()

    xml = build_document_xml(report)

    assert 'Sumar Data Quality' in xml
    assert 'Status Data Quality' in xml
    assert 'WARNING' in xml
    assert 'Surse găsite' in xml
    assert '4/4' in xml
    assert 'Erori' in xml
    assert 'Warning-uri' in xml
    assert 'Issues' in xml
    assert 'Verdict raport' in xml


def test_audit_checklist_docx_renders_existing_data_quality_issues_readably() -> None:
    report, _data_quality = make_docx_report()

    xml = build_document_xml(report)

    assert 'Observații Data Quality' in xml
    assert 'nomenclator.xlsx' in xml
    assert 'Sheet2 / cod articol/produs' in xml
    assert 'Lipsește coloana obligatorie pentru cod articol/produs.' in xml


def test_audit_checklist_docx_preserves_pass_with_observations_verdict() -> None:
    report, _data_quality = make_docx_report(observations=['Observație existentă pentru caz.'])

    xml = build_document_xml(report)

    assert report.conclusion_status == 'PASS_WITH_OBSERVATIONS'
    assert report.exercise.result == 'PASS_WITH_OBSERVATIONS'
    assert 'PASS_WITH_OBSERVATIONS' in xml
    assert 'Status Data Quality' in xml


def test_audit_checklist_docx_summary_does_not_change_ui_json_payload() -> None:
    report, data_quality = make_docx_report()
    before = audit_checklist_ui_payload_from_report(report, data_quality=data_quality)

    build_document_xml(report)
    after = audit_checklist_ui_payload_from_report(report, data_quality=data_quality)

    assert after == before


def test_audit_checklist_docx_ds099903883_10526_warning_non_regression() -> None:
    report, _data_quality = make_docx_report(
        code='DS099903883',
        lot='105.26',
        data_quality=warning_data_quality(issue_count=8, warning_count=8),
        observations=['Observații Data Quality existente pentru cazul real.'],
    )

    xml = build_document_xml(report)

    assert report.exercise.code == 'DS099903883'
    assert report.exercise.lot == '105.26'
    assert report.conclusion_status == 'PASS_WITH_OBSERVATIONS'
    assert 'DS099903883' in xml
    assert '105.26' in xml
    assert 'WARNING' in xml
    assert 'Warning-uri' in xml
    assert 'Issues' in xml
    assert '8' in xml


def test_audit_checklist_docx_data_quality_summary_has_no_forbidden_claims() -> None:
    report, _data_quality = make_docx_report()

    xml = build_document_xml(report)

    for forbidden in ('DONE', 'release', 'production-ready', 'daily-use'):
        assert forbidden not in xml
