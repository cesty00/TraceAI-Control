'''Checklist-aligned audit DOCX renderer.

This renderer consumes AuditChecklistReport, not raw TraceabilityCase tables. It
keeps the report audit-oriented: concise text, explicit sections and stable
WordprocessingML output.
'''

from __future__ import annotations

import argparse
import html
import re
import zipfile
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from src.audit.audit_checklist_report import (
    AuditChecklistReport,
    ChecklistDocumentRegisterLine,
    ChecklistLotFlow,
    ChecklistProductionConsumption,
    ChecklistUpstreamLine,
    build_audit_checklist_report,
    checklist_received_quantity,
)
from src.audit.audit_traceability_report import build_audit_traceability_report
from src.core.build_info import BuildInfo, build_info_table_rows, get_build_info
from src.report.audit_docx import (
    APP_XML,
    CONTENT_TYPES_XML,
    CORE_XML,
    DOCUMENT_RELS_XML,
    ROOT_RELS_XML,
    STYLES_XML,
    bullets,
    page_break,
    paragraph,
    wrap_document,
)
from src.report.docx_layout import (
    apply_cell_layout_properties,
    apply_table_layout_properties,
    compact_audit_table,
    table_row_properties_xml,
)
from src.rules.run_traceability_case import run_traceability_case

MISSING = 'FARA DATE IDENTIFICATE'
Q = chr(34)
DOCUMENT_REGISTER_CHECKBOX = '☐'
DOCUMENT_REGISTER_COLUMN_WIDTHS = [420, 900, 1550, 1800, 900, 900, 1200, 1900, 850]
QUICK_AUDITOR_GUIDE_ITEMS = [
    'Verifică întâi Rezumatul de conformare checklist.',
    'Confirmă bilanțul PRD vs WMS în 01_EXERCITIU.',
    'Verifică avalul în 03_TABEL_II_AVAL și documentele de livrare.',
    'Verifică amontele în 02_TABEL_I_AMONTE și documentele de recepție.',
    'Folosește registrul documentelor pentru pregătirea dosarului fizic.',
]
DOCX_DATA_QUALITY_KEYS = (
    'status',
    'source_count',
    'sources_found',
    'error_count',
    'warning_count',
    'issue_count',
    'issues',
)
MAX_DOCX_DATA_QUALITY_ISSUES = 5


@dataclass(frozen=True)
class AuditReportPolicy:
    '''Controls how much detail is visible in the audit DOCX.'''

    max_name_chars: int = 42
    max_observation_chars: int = 70
    max_receipt_chars: int = 120
    max_delivery_chars: int = 80
    max_register_reference_chars: int = 120
    max_visible_lot_flows: int = 12
    max_visible_document_register_rows: int = 18
    target_page_count: int = 6

    def short(self, value: object, max_length: int | None = None) -> str:
        limit = max_length or self.max_observation_chars
        text = str(value).strip() if value is not None else MISSING
        if not text:
            text = MISSING
        text = re.sub(r'\s+', ' ', text)
        if len(text) <= limit:
            return text
        return text[: limit - 1].rstrip() + '…'

    def name(self, value: object) -> str:
        return self.short(value, self.max_name_chars)

    def delivery(self, value: object) -> str:
        return self.short(value, self.max_delivery_chars)

    def stock(self, value: object) -> str:
        text = str(value).strip() if value is not None else MISSING
        if not text or text == MISSING:
            return MISSING
        return text.replace('locații:', 'loc.')

    def receipts(self, value: object) -> str:
        text = str(value).strip() if value is not None else MISSING
        if not text or text == MISSING:
            return MISSING
        parts = [part.strip() for part in text.split(';') if part.strip()]
        if len(parts) <= 2:
            return self.short(text, self.max_receipt_chars)
        return self.short(f'{parts[0]}; {parts[1]}; +{len(parts) - 2} alte', self.max_receipt_chars)

    def third_party(self, value: object) -> str:
        text = str(value).strip() if value is not None else MISSING
        if not text or text == MISSING:
            return MISSING
        if text.startswith('DA;'):
            return self.short(text, 85)
        if 'nu se aplic' in text.casefold():
            return 'Nu se aplică'
        return self.short(text, 85)

    def upstream_observation(self, value: object) -> str:
        text = str(value).strip() if value is not None else 'OK'
        if not text or text == 'OK':
            return 'OK'
        folded = text.casefold()
        if 'nu se aplic' in folded:
            return 'Nu se aplică'
        if 'nu apare în stoc' in folded or 'stoc' in folded:
            return 'Stoc nedisponibil în fișier'
        if 'livrări către terți' in folded:
            return 'Verificat livrări terți'
        if 'recep' in folded:
            return 'Verificare recepții'
        return self.short(text, self.max_observation_chars)

    def downstream_observation(self, value: object) -> str:
        text = str(value).strip() if value is not None else 'OK'
        if not text or text == MISSING:
            return 'OK'
        return 'Document WMS; data/adresa se completează dacă există în sursă'

    def third_party_note(self, line: ChecklistUpstreamLine) -> str:
        if line.third_party_delivery_status == 'NU':
            return 'Nu au fost identificate livrări directe în WMS.'
        if line.third_party_delivery_status == 'DA':
            return self.short(line.observation, 85)
        return self.short(line.observation, 85)

    def flow_status(self, value: object) -> str:
        text = str(value).strip() if value is not None else MISSING
        if 'parțial' in text:
            return 'documentat parțial'
        return self.short(text, 35)

    def flow_observation(self, value: object) -> str:
        text = str(value).strip() if value is not None else MISSING
        if not text or text == MISSING:
            return 'OK'
        folded = text.casefold()
        if 'nu se aplic' in folded:
            return 'Nu se aplică'
        if 'stoc' in folded:
            return 'Verificare stoc'
        if 'livrări' in folded:
            return 'Verificare livrări'
        return self.short(text, 60)

    def register_reference(self, value: object) -> str:
        text = str(value).strip() if value is not None else MISSING
        if not text or text == MISSING:
            return MISSING
        return self.receipts(text)

    def register_reason(self, value: object) -> str:
        text = str(value).strip() if value is not None else MISSING
        folded = text.casefold()
        if 'produc' in folded:
            return 'Confirmă producția și consumurile'
        if 'livrare' in folded:
            return 'Confirmă livrarea aval'
        if 'intrarea' in folded or 'recep' in folded:
            return 'Confirmă intrarea lotului sursă'
        return self.short(text, 55)

    def select_lot_flows(self, rows: Sequence[ChecklistLotFlow]) -> list[ChecklistLotFlow]:
        important: list[ChecklistLotFlow] = []
        secondary: list[ChecklistLotFlow] = []
        for row in rows:
            text = f'{row.material_type} {row.third_party_deliveries} {row.stock_at_moment} {row.observation}'.casefold()
            if row.material_type in {'Materie primă', 'Material auxiliar / gaz'} or 'da' in text or 'fara date' not in text:
                important.append(row)
            else:
                secondary.append(row)
        return (important + secondary)[: self.max_visible_lot_flows]

    def select_document_register(self, rows: Sequence[ChecklistDocumentRegisterLine]) -> list[ChecklistDocumentRegisterLine]:
        priority = {'PRD': 0, 'WMS': 1, 'NIR': 2}
        return sorted(rows, key=lambda row: (priority.get(row.area, 9), row.related_code, row.related_lot, row.document_reference))[: self.max_visible_document_register_rows]

    def overflow_note(self, total: int, visible: int, label: str) -> str | None:
        if total <= visible:
            return None
        return f'+{total - visible} {label} suplimentare sunt păstrate în datele tehnice ale cazului.'


DEFAULT_POLICY = AuditReportPolicy()


def table(headers: list[str], rows: list[list[object]]) -> str:
    '''Render major audit checklist tables using the compact visual design renderer.'''

    return compact_audit_table(headers, rows)


def primary_production_order(report: AuditChecklistReport) -> ChecklistProductionConsumption | None:
    for row in report.production_consumption:
        return row
    return None


def sync_docx_data_quality_from_source(report: AuditChecklistReport, data_quality: dict[str, Any] | None) -> AuditChecklistReport:
    '''Copy existing Data Quality display fields into the DOCX report instance.'''

    if not isinstance(data_quality, dict):
        return report
    for key in DOCX_DATA_QUALITY_KEYS:
        if key in data_quality:
            report.data_quality[key] = data_quality[key]
    return report


def data_quality_text(value: object, default: str = '0') -> str:
    text = str(value).strip() if value is not None else default
    return text or default


def data_quality_count(summary: dict[str, Any], key: str) -> str:
    return data_quality_text(summary.get(key, 0), '0')


def data_quality_sources(summary: dict[str, Any]) -> str:
    source_count = data_quality_count(summary, 'source_count')
    sources_found = data_quality_text(summary.get('sources_found', source_count), source_count)
    return f'{sources_found}/{source_count}'


def data_quality_issue_value(issue: dict[str, Any], key: str) -> str:
    value = issue.get(key)
    text = str(value).strip() if value is not None else ''
    return text or MISSING


def data_quality_issue_location(issue: dict[str, Any]) -> str:
    parts = [
        data_quality_issue_value(issue, 'sheet_name'),
        data_quality_issue_value(issue, 'column_name'),
    ]
    meaningful = [part for part in parts if part != MISSING]
    return ' / '.join(meaningful) if meaningful else MISSING


def data_quality_issue_rows(summary: dict[str, Any], policy: AuditReportPolicy) -> list[list[str]]:
    issues = summary.get('issues')
    if not isinstance(issues, list):
        return []
    normalized = [issue for issue in issues if isinstance(issue, dict)]
    rows = [
        [
            data_quality_issue_value(issue, 'severity'),
            policy.short(data_quality_issue_value(issue, 'source_name'), 46),
            policy.short(data_quality_issue_location(issue), 54),
            policy.short(data_quality_issue_value(issue, 'message'), 120),
        ]
        for issue in normalized[:MAX_DOCX_DATA_QUALITY_ISSUES]
    ]
    if len(normalized) > len(rows):
        rows.append(['...', '...', '...', f'+{len(normalized) - len(rows)} observații suplimentare sunt păstrate în datele cazului.'])
    return rows


def build_data_quality_summary_section(report: AuditChecklistReport, policy: AuditReportPolicy) -> list[str]:
    summary = report.data_quality if isinstance(report.data_quality, dict) else {}
    parts = [
        paragraph('Sumar Data Quality', style='Heading1'),
        literal_paragraph(
            'Sumarul Data Quality este preluat din modelul audit existent. El nu schimbă verdictul raportului și nu înlocuiește verificarea documentelor fizice.',
            spacing_after=50,
        ),
        table(
            ['Indicator', 'Valoare'],
            [
                ['Status Data Quality', data_quality_text(summary.get('status'), 'NOT_AVAILABLE')],
                ['Surse găsite', data_quality_sources(summary)],
                ['Erori', data_quality_count(summary, 'error_count')],
                ['Warning-uri', data_quality_count(summary, 'warning_count')],
                ['Issues', data_quality_count(summary, 'issue_count')],
                ['Verdict raport', report.conclusion_status],
            ],
        ),
    ]
    issue_rows = data_quality_issue_rows(summary, policy)
    if issue_rows:
        parts.extend(
            [
                paragraph('Observații Data Quality', style='Heading2'),
                table(['Severitate', 'Sursă', 'Loc', 'Observație'], issue_rows),
            ]
        )
    return parts


def build_checklist_header_xml(report: AuditChecklistReport, build_info: BuildInfo) -> str:
    code = _header_footer_text(report.exercise.code)
    lot = _header_footer_text(report.exercise.lot)
    product_name = _header_footer_text(report.exercise.product_name)
    return (
        f'<?xml version={Q}1.0{Q} encoding={Q}UTF-8{Q} standalone={Q}yes{Q}?>\n'
        f'<w:hdr xmlns:w={Q}http://schemas.openxmlformats.org/wordprocessingml/2006/main{Q}>'
        f'<w:p><w:pPr><w:spacing w:after={Q}0{Q}/></w:pPr>'
        f'<w:r><w:rPr><w:b/><w:sz w:val={Q}15{Q}/><w:rFonts w:ascii={Q}Arial{Q} w:hAnsi={Q}Arial{Q}/></w:rPr><w:t>TraceAI Control — Test de trasabilitate pentru audit</w:t></w:r>'
        f'<w:r><w:rPr><w:sz w:val={Q}15{Q}/><w:rFonts w:ascii={Q}Arial{Q} w:hAnsi={Q}Arial{Q}/></w:rPr><w:t> | Cod {code} | Lot {lot}</w:t></w:r>'
        f'</w:p><w:p><w:pPr><w:spacing w:after={Q}0{Q}/></w:pPr>'
        f'<w:r><w:rPr><w:sz w:val={Q}13{Q}/><w:rFonts w:ascii={Q}Arial{Q} w:hAnsi={Q}Arial{Q}/></w:rPr><w:t>{product_name}</w:t></w:r>'
        f'</w:p></w:hdr>'
    )


def build_checklist_footer_xml(report: AuditChecklistReport, build_info: BuildInfo) -> str:
    version = _header_footer_text(build_info.app_version)
    commit = _header_footer_text(build_info.short_commit)
    channel = _header_footer_text(build_info.build_channel)
    generated_at = _header_footer_text(build_info.generated_at)
    return (
        f'<?xml version={Q}1.0{Q} encoding={Q}UTF-8{Q} standalone={Q}yes{Q}?>\n'
        f'<w:ftr xmlns:w={Q}http://schemas.openxmlformats.org/wordprocessingml/2006/main{Q}>'
        f'<w:p><w:pPr><w:spacing w:after={Q}0{Q}/><w:jc w:val={Q}center{Q}/></w:pPr>'
        f'<w:r><w:rPr><w:sz w:val={Q}13{Q}/><w:rFonts w:ascii={Q}Arial{Q} w:hAnsi={Q}Arial{Q}/></w:rPr><w:t>TraceAI Control {version} | commit {commit} | canal {channel} | generat {generated_at} | pagina </w:t></w:r>'
        f'<w:fldSimple w:instr={Q}PAGE{Q}><w:r><w:rPr><w:sz w:val={Q}13{Q}/><w:rFonts w:ascii={Q}Arial{Q} w:hAnsi={Q}Arial{Q}/></w:rPr><w:t>1</w:t></w:r></w:fldSimple>'
        f'</w:p></w:ftr>'
    )


def _header_footer_text(value: object) -> str:
    text = str(value).strip() if value is not None else MISSING
    return html.escape(text or MISSING, quote=False)


def generate_audit_checklist_docx_report(
    report: AuditChecklistReport,
    output_path: str | Path,
    policy: AuditReportPolicy = DEFAULT_POLICY,
    build_info: BuildInfo | None = None,
) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    metadata = build_info or get_build_info()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as package:
        package.writestr('[Content_Types].xml', CONTENT_TYPES_XML)
        package.writestr('_rels/.rels', ROOT_RELS_XML)
        package.writestr('docProps/app.xml', APP_XML)
        package.writestr('docProps/core.xml', CORE_XML)
        package.writestr('word/_rels/document.xml.rels', DOCUMENT_RELS_XML)
        package.writestr('word/styles.xml', STYLES_XML)
        package.writestr('word/header1.xml', build_checklist_header_xml(report, metadata))
        package.writestr('word/footer1.xml', build_checklist_footer_xml(report, metadata))
        package.writestr('word/document.xml', build_document_xml(report, policy, metadata))
    return output


def build_document_xml(
    report: AuditChecklistReport,
    policy: AuditReportPolicy = DEFAULT_POLICY,
    build_info: BuildInfo | None = None,
) -> str:
    metadata = build_info or get_build_info()
    body: list[str] = []
    body.extend(build_title_block(report, metadata))
    body.extend(build_auditor_verdict_card_section(report, policy))
    body.extend(build_quick_auditor_guide_section())
    body.extend(build_data_quality_summary_section(report, policy))
    body.extend(build_conformity_section(report, policy))
    body.extend(build_exercise_section(report, policy))
    body.extend(build_downstream_section(report, policy))
    body.append(page_break())
    body.extend(build_upstream_section(report, policy))
    body.append(page_break())
    body.extend(build_production_consumption_section(report, policy))
    body.append(page_break())
    body.extend(build_lot_flow_section(report, policy))
    body.extend(build_document_register_section(report, policy))
    body.extend(build_conclusion_section(report, policy))
    body.extend(build_build_info_section(metadata))
    return wrap_document(''.join(body))


def build_title_block(report: AuditChecklistReport, build_info: BuildInfo) -> list[str]:
    return [
        paragraph('TEST DE TRASABILITATE PENTRU AUDIT', style='Title'),
        literal_paragraph(
            f'{report.exercise.code} / {report.exercise.lot} — {report.exercise.product_name}',
            bold=True,
            align='center',
            spacing_after=40,
        ),
        literal_paragraph(
            'Raport completat din fișierele sursă disponibile: WMS trasabilitate, raport producție, stoc la moment și nomenclator.',
            align='center',
            spacing_after=40,
        ),
        literal_paragraph(
            f'Build raport: {build_info.app_version} / commit {build_info.short_commit} / generat {build_info.generated_at}',
            align='center',
            spacing_after=100,
        ),
    ]


def build_auditor_verdict_card_section(report: AuditChecklistReport, policy: AuditReportPolicy) -> list[str]:
    main_order = primary_production_order(report)
    return [
        paragraph('Card verdict auditor', style='Heading1'),
        literal_paragraph(
            'Cardul verdict sintetizează cazul de audit și indică zonele principale care trebuie citite înaintea verificării documentelor fizice.',
            spacing_after=50,
        ),
        table(
            ['Indicator audit', 'Status / valoare'],
            [
                ['Verdict audit', report.conclusion_status],
                ['Cod produs finit', report.exercise.code],
                ['Lot produs finit', report.exercise.lot],
                ['Denumire produs finit', policy.name(report.exercise.product_name)],
                ['Dată producție principală', main_order.production_date if main_order else MISSING],
                ['Cantitate produsă PRD', report.balance.prd_produced],
                ['Stoc produs finit / DSD', policy.stock(report.balance.stock_at_moment)],
                ['Bilanț PRD vs WMS', f'{report.balance.status} — {policy.short(report.balance.observation, 90)}'],
                ['Aval / livrări', f'{len(report.downstream)} livrări identificate' if report.downstream else MISSING],
                ['Amonte / loturi sursă', f'{len(report.upstream)} linii amonte identificate' if report.upstream else MISSING],
                ['Documente fizice', f'{len(report.document_register)} documente de pregătit' if report.document_register else MISSING],
            ],
        ),
    ]


def build_quick_auditor_guide_section() -> list[str]:
    return [
        paragraph('Ghid rapid pentru auditor', style='Heading1'),
        literal_paragraph(
            'Ghidul rapid indică ordinea recomandată de citire: verdict, bilanț, aval, amonte, consumuri și registrul documentelor fizice.',
            spacing_after=50,
        ),
        *bullets(QUICK_AUDITOR_GUIDE_ITEMS),
    ]


def build_conformity_section(report: AuditChecklistReport, policy: AuditReportPolicy) -> list[str]:
    rows = [[item.requirement, item.status, policy.short(item.evidence, 95), policy.short(item.observation, 95)] for item in report.conformity]
    return [
        paragraph('Rezumat de conformare checklist', style='Heading1'),
        literal_paragraph(
            'Rezumatul de conformare arată dacă raportul conține informațiile necesare pentru verificarea trasabilității. Observațiile explică limitele datelor sau verificările care trebuie completate manual.',
            spacing_after=50,
        ),
        table(['Cerință', 'Status în test', 'Dovezi', 'Observații'], rows),
    ]


def build_exercise_section(report: AuditChecklistReport, policy: AuditReportPolicy) -> list[str]:
    exercise = report.exercise
    balance = report.balance
    main_order = primary_production_order(report)
    return [
        paragraph('01_EXERCITIU — Fișa principală a exercițiului', style='Heading1'),
        paragraph('Fișa principală fixează produsul finit și lotul analizat. Această secțiune este punctul de plecare al verificării și trebuie citită împreună cu Tabelul I pentru amonte și Tabelul II pentru aval.'),
        table(['Indicator', 'Valoare'], [['Cod produs finit', exercise.code], ['Lot produs finit', exercise.lot], ['Denumire produs finit', exercise.product_name], ['Status verificare', exercise.result]]),
        paragraph('Repere rapide produs finit', style='Heading2'),
        paragraph('Reperele rapide regrupează denumirea produsului, data de producție, cantitatea produsă și stocul produsului finit, pentru o citire rapidă înainte de tabelele operaționale.'),
        table(['Indicator', 'Valoare'], [['Denumire produs finit', exercise.product_name], ['Dată producție principală', main_order.production_date if main_order else MISSING], ['Cantitate produsă PRD', balance.prd_produced], ['Stoc produs finit / DSD', policy.stock(balance.stock_at_moment)]]),
        paragraph('Bilanț produs finit', style='Heading2'),
        paragraph('Bilanțul compară cantitatea produsă în PRD cu intrările și ieșirile lotului în WMS. Scopul este să confirme că lotul produs poate fi urmărit până la livrările către clienți sau până la stocul rămas.'),
        table(['Indicator', 'Cantitate / status', 'Observație'], [['Cantitate produsă PRD', balance.prd_produced, 'Sursă PRD'], ['Intrare WMS produs finit', balance.wms_production_out, 'Intrare produs finit WMS'], ['Cantitate livrată WMS', balance.wms_delivered, 'Valoare semnată WMS'], ['Stoc produs finit / DSD', policy.stock(balance.stock_at_moment), 'Dacă există în stoc'], ['Status bilanț', balance.status, policy.short(balance.observation, 90)]]),
    ]


def build_downstream_section(report: AuditChecklistReport, policy: AuditReportPolicy) -> list[str]:
    rows = [[d.client, d.address, d.delivery_date, d.delivered_quantity, d.delivery_document_type, d.delivery_document_number, d.wms_order, policy.downstream_observation(d.observation)] for d in report.downstream]
    if not rows:
        rows = [[MISSING] * 8]
    return [
        paragraph('03_TABEL_II_AVAL — Livrări produs finit', style='Heading1'),
        paragraph('Tabelul II prezintă traseul lotului de produs finit către clienți. Pentru fiecare livrare sunt afișate clientul, adresa sau depozitul identificat, data livrării, cantitatea livrată și documentul WMS care susține ieșirea din gestiune.'),
        paragraph('În această secțiune, clientul, data livrării și cantitatea livrată sunt grupate explicit pentru citirea rapidă a avalului produsului finit.'),
        paragraph('Auditorul trebuie să compare aceste rânduri cu documentele fizice de livrare și cu documentele WMS indicate.'),
        table(['Client', 'Adresă', 'Dată livrare', 'Cantitate livrată', 'Tip document', 'Număr document', 'Comandă WMS', 'Observații'], rows),
    ]


def build_upstream_section(report: AuditChecklistReport, policy: AuditReportPolicy) -> list[str]:
    rows = [[line.material_type, line.code, line.lot, policy.name(line.name), line.consumed_quantity, checklist_received_quantity(line), line.receipt_date, policy.name(line.supplier), line.document_type, line.document_number, line.document_date, policy.stock(line.stock_at_moment), line.third_party_delivery_status, policy.upstream_observation(line.observation)] for line in report.upstream]
    if not rows:
        rows = [[MISSING] * 14]
    return [
        paragraph('02_TABEL_I_AMONTE — Materii prime, ambalaje și materiale auxiliare', style='Heading1'),
        paragraph('Tabelul I urmărește loturile care au intrat în produsul finit: materii prime, ambalaje și materiale auxiliare, inclusiv gazul atunci când este folosit. Pentru fiecare lot sunt afișate clar materia primă sau ambalajul, cantitatea consumată, cantitatea recepționată și stocul lotului sursă, împreună cu contextul documentar deja prezent în model.'),
        table(['Tip material', 'Cod intern', 'Lot sursă', 'Materie primă / ambalaj', 'Cantitate consumată', 'Cantitate recepționată', 'Dată recepție', 'Furnizor', 'Tip document', 'Număr document', 'Dată document', 'Stoc lot sursă', 'Livrări terți', 'Observații'], rows),
        *build_third_party_section(report, policy),
    ]


def build_third_party_section(report: AuditChecklistReport, policy: AuditReportPolicy) -> list[str]:
    raw_lines = [line for line in report.upstream if line.material_type == 'Materie primă']
    if not raw_lines:
        return []
    rows = [[line.code, line.lot, policy.name(line.name), line.consumed_quantity, line.third_party_delivery_status, policy.third_party_note(line)] for line in raw_lines]
    return [
        paragraph('Verificare specială — materii prime livrate către terți', style='Heading2'),
        paragraph('Această verificare evidențiază dacă loturile de materie primă folosite în produsul auditat au avut și livrări directe către terți. Informația este importantă pentru separarea consumului intern de alte ieșiri ale aceluiași lot sursă.'),
        table(['Cod MP', 'Lot MP', 'Materie primă', 'Cantitate consumată', 'Livrări MP către terți', 'Detalii'], rows),
    ]


def build_production_consumption_section(report: AuditChecklistReport, policy: AuditReportPolicy) -> list[str]:
    return [
        paragraph('04_PRODUCTIE_CONSUM — Detaliere pe comenzi de producție', style='Heading1'),
        paragraph('Această secțiune leagă comenzile de producție de cantitatea de produs finit obținută și de materialele consumate. Ea ajută auditorul să verifice, pe fiecare comandă, din ce loturi s-a produs lotul finit analizat.'),
        paragraph('Comenzi producție', style='Heading2'),
        paragraph('Tabelul de comenzi sintetizează data de producție, cantitatea produsă și asocierea cu intrarea WMS PRODUCTION-OUT și cu livrarea produsului finit, atunci când aceasta poate fi legată de cantitate și document.'),
        table(['Comandă producție', 'Dată producție', 'Cantitate produsă PRD', 'WMS production-out', 'Livrare PF asociată'], production_order_summary_rows(report.production_consumption, policy)),
        paragraph('Consumuri pe comenzi — tabel operațional', style='Heading2'),
        paragraph('Tabelul operațional detaliază materiile prime și ambalajele deja prezente în model, cu accent pe codul intern, lotul consumat și cantitatea consumată pentru lotul finit analizat.'),
        table(['Comandă', 'Tip material', 'Cod intern consum', 'Lot consum', 'Materie primă / ambalaj', 'Cantitate consumată'], production_consumption_rows(report.production_consumption, policy)),
    ]


def production_order_summary_rows(rows: list[ChecklistProductionConsumption], policy: AuditReportPolicy) -> list[list[str]]:
    summary: OrderedDict[str, ChecklistProductionConsumption] = OrderedDict()
    for row in rows:
        summary.setdefault(row.production_order, row)
    if not summary:
        return [[MISSING] * 5]
    return [[row.production_order, row.production_date, row.finished_product_quantity, row.wms_production_out, policy.delivery(row.associated_delivery)] for row in summary.values()]


def production_consumption_rows(rows: list[ChecklistProductionConsumption], policy: AuditReportPolicy) -> list[list[str]]:
    if not rows:
        return [[MISSING] * 6]
    return [[row.production_order, row.material_type, row.consumed_code, row.consumed_lot, policy.name(row.consumed_name), row.consumed_quantity] for row in rows]


def build_lot_flow_section(report: AuditChecklistReport, policy: AuditReportPolicy) -> list[str]:
    selected = policy.select_lot_flows(report.lot_flows)
    rows = [[flow.material_type, flow.code, flow.lot, policy.name(flow.name), policy.receipts(flow.receipts), flow.consumed_in_audited_lot, policy.third_party(flow.third_party_deliveries), policy.stock(flow.stock_at_moment), policy.flow_status(flow.status), policy.flow_observation(flow.observation)] for flow in selected]
    if not rows:
        rows = [[MISSING] * 10]
    parts = [
        paragraph('05_FLUX_LOTURI_SI_DOCUMENTE — Fluxuri loturi și documente', style='Heading1'),
        paragraph('Fluxurile de loturi reunesc informațiile esențiale despre recepții, consumul în lotul auditat, eventualele livrări către terți și stocul rămas. Tabelul este o privire de ansamblu asupra mișcărilor relevante pentru fiecare lot sursă.'),
        table(['Tip', 'Cod', 'Lot', 'Denumire', 'Recepții', 'Consum auditat', 'Livrări terți', 'Stoc', 'Status', 'Observații'], rows),
    ]
    note = policy.overflow_note(len(report.lot_flows), len(selected), 'fluxuri')
    if note:
        parts.append(paragraph(note))
    return parts


def build_document_register_section(report: AuditChecklistReport, policy: AuditReportPolicy) -> list[str]:
    selected = policy.select_document_register(report.document_register)
    rows = [[DOCUMENT_REGISTER_CHECKBOX, line.area, line.document_type, policy.register_reference(line.document_reference), line.related_code, line.related_lot, policy.delivery(line.related_order), policy.register_reason(line.why_needed), line.status] for line in selected]
    if not rows:
        rows = [[MISSING] * 9]
    parts = [
        paragraph('Registru documente fizice de pregătit pentru auditor', style='Heading2'),
        literal_paragraph(
            'Registrul indică documentele care trebuie pregătite în dosarul de audit. Coloana Bifat permite folosirea tabelului ca listă de verificare tipărită pentru documentele fizice.',
            spacing_after=50,
        ),
        literal_table(
            ['Bifat', 'Zona', 'Tip document', 'Referință', 'Cod', 'Lot', 'Comandă', 'Motiv', 'Status'],
            rows,
            column_widths=DOCUMENT_REGISTER_COLUMN_WIDTHS,
        ),
    ]
    note = policy.overflow_note(len(report.document_register), len(selected), 'documente')
    if note:
        parts.append(paragraph(note))
    return parts


def build_conclusion_section(report: AuditChecklistReport, policy: AuditReportPolicy) -> list[str]:
    return [
        paragraph('Concluzie audit intern', style='Heading1'),
        paragraph(f'Pentru produsul {report.exercise.code} / lot {report.exercise.lot}, raportul audit confirmă trasabilitatea produsului finit în aval și în amonte pe baza surselor WMS și PRD disponibile.'),
        paragraph('Concluzia sintetizează rezultatul verificării pe baza datelor WMS și PRD disponibile. Ea nu înlocuiește verificarea documentelor fizice, ci indică ce a fost identificat și ce trebuie atașat dosarului de audit.'),
        paragraph(f'Bilanț PRD vs WMS: {report.balance.status}. {policy.short(report.balance.observation, 120)}'),
        *bullets(compact_conclusion_observations(report, policy)),
    ]


def compact_conclusion_observations(report: AuditChecklistReport, policy: AuditReportPolicy) -> list[str]:
    raw_materials = [line for line in report.upstream if line.material_type == 'Materie primă']
    packaging = [line for line in report.upstream if line.material_type == 'Ambalaj']
    gases = [line for line in report.upstream if 'gaz' in line.material_type.casefold()]
    return [
        f'S-au identificat {len(raw_materials)} materii prime, {len(packaging)} ambalaje și {len(gases)} linii auxiliare/gaz în amonte.',
        'Recepțiile WMS disponibile și stocurile la moment sunt afișate în Tabelul I și în fluxurile de loturi.',
        'Raportul poate fi folosit ca bază pentru pregătirea dosarului de audit, împreună cu documentele fizice menționate în registru.',
    ]


def build_build_info_section(build_info: BuildInfo) -> list[str]:
    return [
        paragraph('Informații build raport', style='Heading1'),
        paragraph('Această secțiune identifică versiunea aplicației folosită la generarea raportului, pentru corelare cu diagnosticele GitHub și build-urile instalate local.'),
        literal_table(['Câmp', 'Valoare'], build_info_table_rows(build_info)),
    ]


def xml_attrs(pairs: Iterable[tuple[str, object]]) -> str:
    return ''.join(f' {name}={Q}{html.escape(str(value), quote=False)}{Q}' for name, value in pairs if value is not None)


def literal_paragraph(
    text: object,
    style: str | None = None,
    bold: bool = False,
    align: str | None = None,
    spacing_before: int | None = None,
    spacing_after: int | None = None,
) -> str:
    style_xml = f'<w:pStyle{xml_attrs([("w:val", style)])}/>' if style else ''
    align_xml = f'<w:jc{xml_attrs([("w:val", align)])}/>' if align else ''
    spacing_pairs = []
    if spacing_before is not None:
        spacing_pairs.append(('w:before', spacing_before))
    if spacing_after is not None:
        spacing_pairs.append(('w:after', spacing_after))
    spacing_xml = f'<w:spacing{xml_attrs(spacing_pairs)}/>' if spacing_pairs else ''
    bold_xml = '<w:b/>' if bold else ''
    safe_text = html.escape(str(text), quote=False)
    return f'<w:p><w:pPr>{style_xml}{align_xml}{spacing_xml}</w:pPr><w:r><w:rPr>{bold_xml}</w:rPr><w:t>{safe_text}</w:t></w:r></w:p>'


def literal_table(headers: list[str], rows: list[list[object]], column_widths: Sequence[int] | None = None) -> str:
    xml_rows = [literal_table_row(headers, is_header=True, column_widths=column_widths)]
    xml_rows.extend(literal_table_row(row, column_widths=column_widths) for row in rows)
    borders = (
        f'<w:tblBorders><w:top{xml_attrs([("w:val", "single"), ("w:sz", 4), ("w:space", 0), ("w:color", "808080")])}/>'
        f'<w:left{xml_attrs([("w:val", "single"), ("w:sz", 4), ("w:space", 0), ("w:color", "808080")])}/>'
        f'<w:bottom{xml_attrs([("w:val", "single"), ("w:sz", 4), ("w:space", 0), ("w:color", "808080")])}/>'
        f'<w:right{xml_attrs([("w:val", "single"), ("w:sz", 4), ("w:space", 0), ("w:color", "808080")])}/>'
        f'<w:insideH{xml_attrs([("w:val", "single"), ("w:sz", 4), ("w:space", 0), ("w:color", "808080")])}/>'
        f'<w:insideV{xml_attrs([("w:val", "single"), ("w:sz", 4), ("w:space", 0), ("w:color", "808080")])}/></w:tblBorders>'
    )
    table_properties = apply_table_layout_properties(f'<w:tblStyle{xml_attrs([("w:val", "TraceAITable")])}/>')
    return f'<w:tbl><w:tblPr>{table_properties}{borders}</w:tblPr>{"".join(xml_rows)}</w:tbl>'


def literal_table_row(values: Iterable[object], is_header: bool = False, column_widths: Sequence[int] | None = None) -> str:
    cells = []
    for index, value in enumerate(values):
        width = column_widths[index] if column_widths and index < len(column_widths) else None
        cells.append(literal_table_cell(value, is_header=is_header, width=width))
    return f'<w:tr>{table_row_properties_xml(is_header)}{"".join(cells)}</w:tr>'


def literal_table_cell(value: object, is_header: bool = False, width: int | None = None) -> str:
    shading_xml = f'<w:shd{xml_attrs([("w:fill", "EDEDED")])}/>' if is_header else ''
    bold_xml = '<w:b/>' if is_header else ''
    size = '15' if is_header else '14'
    text = str(value).strip() if value is not None else MISSING
    width_xml = f'<w:tcW{xml_attrs([("w:w", width), ("w:type", "dxa")])}/>' if width is not None else ''
    cell_properties = apply_cell_layout_properties(
        f'{width_xml}{shading_xml}<w:tcMar><w:top{xml_attrs([("w:w", 40), ("w:type", "dxa")])}/><w:left{xml_attrs([("w:w", 40), ("w:type", "dxa")])}/><w:bottom{xml_attrs([("w:w", 40), ("w:type", "dxa")])}/><w:right{xml_attrs([("w:w", 40), ("w:type", "dxa")])}/></w:tcMar>'
    )
    safe_text = html.escape(text or MISSING, quote=False)
    return f'<w:tc><w:tcPr>{cell_properties}</w:tcPr><w:p><w:pPr><w:spacing{xml_attrs([("w:after", 0)])}/></w:pPr><w:r><w:rPr>{bold_xml}<w:sz{xml_attrs([("w:val", size)])}/><w:rFonts{xml_attrs([("w:ascii", "Arial"), ("w:hAnsi", "Arial")])}/></w:rPr><w:t>{safe_text}</w:t></w:r></w:p></w:tc>'


def extract_document_text_from_xml(document_xml: str) -> str:
    return document_xml.replace('<w:t>', '\n').replace('</w:t>', '\n')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Genereaza raport audit DOCX aliniat la checklist.')
    parser.add_argument('source_directory', help='Folderul cu sursele oficiale.')
    parser.add_argument('--code', required=True, help='Cod articol/produs cautat.')
    parser.add_argument('--lot', required=True, help='Lot cautat.')
    parser.add_argument('--output', '-o', required=True, help='Cale output DOCX.')
    args = parser.parse_args(argv)
    traceability_case = run_traceability_case(args.source_directory, args.code, args.lot)
    audit_report = build_audit_traceability_report(traceability_case)
    checklist_report = build_audit_checklist_report(audit_report)
    sync_docx_data_quality_from_source(checklist_report, traceability_case.sections.get('data_quality'))
    generate_audit_checklist_docx_report(checklist_report, args.output)
    return 0 if checklist_report.conclusion_status != 'INCOMPLETE' else 1


if __name__ == '__main__':
    raise SystemExit(main())
