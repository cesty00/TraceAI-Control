from dataclasses import replace
import zipfile

from src.audit.audit_checklist_report import build_audit_checklist_report
from src.audit.audit_traceability_report import build_audit_traceability_report
from src.report.audit_checklist_docx import (
    MAX_DOCX_DATA_QUALITY_ISSUES,
    build_document_xml,
)
from src.ui.audit_checklist_json import audit_checklist_ui_payload_from_report
from src.ui.orchestrator import generate_audit_checklist_docx_from_traceability_case
from tests.test_audit_traceability_report import make_case


def warning_issue(index: int = 1) -> dict[str, object]:
    return {
        'severity': 'WARNING',
        'source_name': f'nomenclator_{index}.xlsx',
        'sheet_name': f'Sheet{index}',
        'column_name': 'cod articol/produs',
        'message': f'Lipsește coloana obligatorie pentru cod articol/produs #{index}.',
    }



def warning_data_quality(
    *,
    issue_count: int = 1,
    warning_count: int = 1,
    include_sources_found: bool = True,
) -> dict[str, object]:
    summary: dict[str, object] = {
        'status': 'WARNING',
        'source_count': 4,
        'error_count': 0,
        'warning_count': warning_count,
        'issue_count': issue_count,
        'issues': [warning_issue(index + 1) for index in range(issue_count)],
    }
    if include_sources_found:
        summary['sources_found'] = 4
    return summary



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
    return report, sections['data_quality']



def test_audit_checklist_docx_includes_short_data_quality_summary() -> None:
    report, data_quality = make_docx_report()

    xml = build_document_xml(report, data_quality_summary=data_quality)

    assert 'Sumar Data Quality' in xml
    assert 'Status Data Quality' in xml
    assert 'WARNING' in xml
    assert 'Surse găsite' in xml
    assert '4/4' in xml
    assert 'Erori' in xml
    assert 'Warning-uri' in xml
    assert 'Issues' in xml
    assert 'Verdict raport' in xml



def test_audit_checklist_docx_missing_sources_found_stays_conservative() -> None:
    report, data_quality = make_docx_report(data_quality=warning_data_quality(include_sources_found=False))

    xml = build_document_xml(report, data_quality_summary=data_quality)

    assert 'Surse găsite' in xml
    assert 'NOT_AVAILABLE' in xml
    assert '4/4' not in xml



def test_audit_checklist_docx_renders_existing_data_quality_issues_readably() -> None:
    report, data_quality = make_docx_report()

    xml = build_document_xml(report, data_quality_summary=data_quality)

    assert 'Observații Data Quality' in xml
    assert 'nomenclator_1.xlsx' in xml
    assert 'Sheet1 / cod articol/produs' in xml
    assert 'Lipsește coloana obligatorie pentru cod articol/produs #1.' in xml



def test_audit_checklist_docx_overflow_issues_remains_conservative() -> None:
    issue_count = MAX_DOCX_DATA_QUALITY_ISSUES + 2
    report, data_quality = make_docx_report(
        data_quality=warning_data_quality(issue_count=issue_count, warning_count=issue_count),
    )

    xml = build_document_xml(report, data_quality_summary=data_quality)

    assert f'+{issue_count - MAX_DOCX_DATA_QUALITY_ISSUES} observații suplimentare sunt păstrate în datele cazului.' in xml
    assert 'nomenclator_1.xlsx' in xml
    assert f'nomenclator_{MAX_DOCX_DATA_QUALITY_ISSUES}.xlsx' in xml
    assert f'nomenclator_{issue_count}.xlsx' not in xml



def test_audit_checklist_docx_preserves_pass_with_observations_verdict() -> None:
    report, data_quality = make_docx_report(observations=['Observație existentă pentru caz.'])

    xml = build_document_xml(report, data_quality_summary=data_quality)

    assert report.conclusion_status == 'PASS_WITH_OBSERVATIONS'
    assert report.exercise.result == 'PASS_WITH_OBSERVATIONS'
    assert 'PASS_WITH_OBSERVATIONS' in xml
    assert 'Status Data Quality' in xml



def test_audit_checklist_docx_renderer_does_not_mutate_report_data_quality() -> None:
    report, data_quality = make_docx_report()
    before = dict(report.data_quality)

    build_document_xml(report, data_quality_summary=warning_data_quality(include_sources_found=False))

    assert report.data_quality == before
    assert report.data_quality['sources_found'] == 4
    assert data_quality['sources_found'] == 4



def test_audit_checklist_docx_summary_does_not_change_ui_json_payload() -> None:
    report, data_quality = make_docx_report()
    before = audit_checklist_ui_payload_from_report(report, data_quality=data_quality)

    build_document_xml(report, data_quality_summary=warning_data_quality(include_sources_found=False))
    after = audit_checklist_ui_payload_from_report(report, data_quality=data_quality)

    assert after == before



def test_audit_checklist_docx_ds099903883_10526_warning_non_regression() -> None:
    report, data_quality = make_docx_report(
        code='DS099903883',
        lot='105.26',
        data_quality=warning_data_quality(issue_count=8, warning_count=8),
        observations=['Observații Data Quality existente pentru cazul real.'],
    )

    xml = build_document_xml(report, data_quality_summary=data_quality)

    assert report.exercise.code == 'DS099903883'
    assert report.exercise.lot == '105.26'
    assert report.conclusion_status == 'PASS_WITH_OBSERVATIONS'
    assert 'DS099903883' in xml
    assert '105.26' in xml
    assert 'WARNING' in xml
    assert 'Warning-uri' in xml
    assert 'Issues' in xml
    assert '8' in xml



def test_audit_checklist_docx_local_operator_path_wires_warning_summary_into_docx(tmp_path) -> None:
    data_quality = warning_data_quality(issue_count=8, warning_count=8)
    traceability_case = make_case()
    traceability_case = replace(
        traceability_case,
        subject=replace(traceability_case.subject, code='DS099903883', lot='105.26'),
        sections={**traceability_case.sections, 'data_quality': data_quality},
        observations=['Observații Data Quality existente pentru cazul local/operator.'],
    )
    audit_report = build_audit_traceability_report(traceability_case)
    checklist_report = build_audit_checklist_report(audit_report)
    payload_before = audit_checklist_ui_payload_from_report(checklist_report, data_quality=data_quality)
    output = tmp_path / 'local-operator-audit-checklist.docx'

    result = generate_audit_checklist_docx_from_traceability_case(traceability_case, output)

    assert result == output
    with zipfile.ZipFile(output) as package:
        xml = package.read('word/document.xml').decode('utf-8')
    payload_after = audit_checklist_ui_payload_from_report(checklist_report, data_quality=data_quality)

    assert 'Status Data Quality' in xml
    assert 'WARNING' in xml
    assert 'Surse găsite' in xml
    assert '4/4' in xml
    assert 'Erori' in xml
    assert '0' in xml
    assert 'Warning-uri' in xml
    assert '8' in xml
    assert 'Issues' in xml
    assert 'NOT_AVAILABLE' not in xml
    assert 'PASS_WITH_OBSERVATIONS' in xml
    assert 'Documente required' in xml
    assert 'Documente recommended' in xml
    assert xml.index('Documente required') < xml.index('Documente recommended')
    assert payload_after == payload_before
    assert payload_after['report']['data_quality']['status'] == 'WARNING'
    assert payload_after['report']['data_quality']['sources_found'] == 4
    assert payload_after['report']['data_quality']['source_count'] == 4
    assert payload_after['report']['data_quality']['error_count'] == 0
    assert payload_after['report']['data_quality']['warning_count'] == 8
    assert payload_after['report']['data_quality']['issue_count'] == 8



def test_audit_checklist_docx_data_quality_summary_has_no_forbidden_claims() -> None:
    report, data_quality = make_docx_report()

    xml = build_document_xml(report, data_quality_summary=data_quality)

    for forbidden in ('DONE', 'release', 'production-ready', 'daily-use'):
        assert forbidden not in xml
