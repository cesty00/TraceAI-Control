from __future__ import annotations

import argparse
import html
import re
import zipfile
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
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
NOT_AVAILABLE = 'NOT_AVAILABLE'
Q = chr(34)
DOCUMENT_REGISTER_CHECKBOX = '☐'
DOCUMENT_REGISTER_COLUMN_WIDTHS = [420, 850, 900, 1550, 1800, 900, 900, 1200, 1900]
QUICK_AUDITOR_GUIDE_ITEMS = [
    '1. Citește Card verdict și Sumar Data Quality.',
    '2. Verifică Rezumat conformare checklist.',
    '3. Citește AMONTE pentru produs finit, bilanț și livrări.',
    '4. Citește AVAL pentru materii prime, ambalaje, auxiliare și loturi sursă.',
    '5. Confirmă comenzi, fluxuri, registru documente și build.',
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
AUDIT_DATE_TOKEN_RE = re.compile(
    r'\b\d{4}-\d{1,2}-\d{1,2}(?:[T ]\d{1,2}:\d{2}(?::\d{2})?)?\b'
    r'|\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}(?:[ T]\d{1,2}:\d{2}(?::\d{2})?)?\b'
)


@dataclass(frozen=True)
class AuditReportPolicy:
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

    def audit_dates(self, value: object) -> str:
        text = str(value).strip() if value is not None else MISSING
        if not text or text == MISSING:
            return MISSING
        parsed_dates = [
            parsed for parsed in (self._parse_audit_date_token(match.group(0)) for match in AUDIT_DATE_TOKEN_RE.finditer(text)) if parsed is not None
        ]
        if not parsed_dates:
            return text
        unique_dates = []
        seen = set()
        for parsed in parsed_dates:
            if parsed in seen:
                continue
            seen.add(parsed)
            unique_dates.append(parsed)
        if len(unique_dates) == 1:
            label = unique_dates[0].strftime('%d/%m/%Y')
            if len(parsed_dates) > 1:
                return f'{label} ({len(parsed_dates)} mișcări)'
            return label
        return '; '.join(item.strftime('%d/%m/%Y') for item in unique_dates)

    def _parse_audit_date_token(self, token: str):
        normalized = token.replace('T', ' ').strip().split(' ', 1)[0]
        for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%d-%m-%Y', '%d/%m/%Y', '%d.%m.%y', '%d-%m-%y', '%d/%m/%y'):
            try:
                return datetime.strptime(normalized, fmt).date()
            except ValueError:
                continue
        return None

    def delivery_document(self, document_type: object, document_number: object) -> str:
        left = str(document_type).strip() if document_type is not None else ''
        right = str(document_number).strip() if document_number is not None else ''
        if not left and not right:
            return MISSING
        if left and right:
            return self.short(f'{left} / {right}', 90)
        return self.short(left or right, 90)

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
        return 'Document WMS; detaliile se verifică în sursa fizică.'

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
        important = []
        secondary = []
        for row in rows:
            text = f'{row.material_type} {row.third_party_deliveries} {row.stock_at_moment} {row.observation}'.casefold()
            if row.material_type in {'Materie primă', 'Material auxiliar / gaz'} or 'da' in text or 'fara date' not in text:
                important.append(row)
            else:
                secondary.append(row)
        return (important + secondary)[: self.max_visible_lot_flows]

    def select_document_register(self, rows: Sequence[ChecklistDocumentRegisterLine]) -> list[ChecklistDocumentRegisterLine]:
        status_priority = {'required': 0, 'recommended': 1}
        area_priority = {'PRD': 0, 'WMS': 1, 'NIR': 2}
        return sorted(
            rows,
            key=lambda row: (
                status_priority.get(row.status, 9),
                area_priority.get(row.area, 9),
                row.related_code,
                row.related_lot,
                row.document_reference,
            ),
        )[: self.max_visible_document_register_rows]

    def overflow_note(self, total: int, visible: int, label: str) -> str | None:
        if total <= visible:
            return None
        return f'+{total - visible} {label} suplimentare sunt păstrate în datele tehnice ale cazului.'


DEFAULT_POLICY = AuditReportPolicy()


def table(headers: list[str], rows: list[list[object]]) -> str:
    return compact_audit_table(headers, rows)


def primary_production_order(report: AuditChecklistReport) -> ChecklistProductionConsumption | None:
    for row in report.production_consumption:
        return row
    return None


def normalize_docx_data_quality_summary(data_quality: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(data_quality, dict):
        return {}
    return {key: data_quality[key] for key in DOCX_DATA_QUALITY_KEYS if key in data_quality}


def data_quality_text(value: object, default: str = '0') -> str:
    text = str(value).strip() if value is not None else default
    return text or default


def data_quality_count(summary: dict[str, Any], key: str) -> str:
    return data_quality_text(summary.get(key, 0), '0')


def data_quality_sources(summary: dict[str, Any]) -> str:
    source_count = data_quality_count(summary, 'source_count')
    if 'sources_found' not in summary:
        return NOT_AVAILABLE
    sources_found = data_quality_text(summary.get('sources_found'), NOT_AVAILABLE)
    return f'{sources_found}/{source_count}'


def data_quality_compact_summary(summary: dict[str, Any]) -> str:
    return ' / '.join([
        data_quality_text(summary.get('status'), NOT_AVAILABLE),
        data_quality_sources(summary),
        data_quality_count(summary, 'error_count'),
        data_quality_count(summary, 'warning_count'),
        data_quality_count(summary, 'issue_count'),
    ])


def data_quality_issue_value(issue: dict[str, Any], key: str) -> str:
    value = issue.get(key)
    text = str(value).strip() if value is not None else ''
    return text or MISSING


def data_quality_issue_location(issue: dict[str, Any]) -> str:
    parts = [data_quality_issue_value(issue, 'sheet_name'), data_quality_issue_value(issue, 'column_name')]
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


def build_data_quality_summary_section(report: AuditChecklistReport, data_quality_summary: dict[str, Any] | None, policy: AuditReportPolicy) -> list[str]:
    summary = normalize_docx_data_quality_summary(data_quality_summary)
    parts = [
        paragraph('Sumar Data Quality', style='Heading1'),
        literal_paragraph(
            'Secțiunea arată dacă sursele necesare au fost găsite și cât de complete sunt datele extrase. Dacă apare FARA DATE IDENTIFICATE, informația nu a fost găsită clar în sursele disponibile și trebuie verificată în documentele fizice.',
            spacing_after=50,
        ),
        table(
            ['Indicator', 'Valoare'],
            [
                ['Status Data Quality', data_quality_text(summary.get('status'), NOT_AVAILABLE)],
                ['Surse găsite', data_quality_sources(summary)],
                ['Erori', data_quality_count(summary, 'error_count')],
                ['Warning-uri', data_quality_count(summary, 'warning_count')],
                ['Issues', data_quality_count(summary, 'issue_count')],
                ['Verdict raport', report.conclusion_status],
            ],
        ),
        literal_paragraph(f'Rezumat compact: {data_quality_compact_summary(summary)}', spacing_after=50),
    ]
    issue_rows = data_quality_issue_rows(summary, policy)
    if issue_rows:
        parts.extend([
            paragraph('Observații Data Quality', style='Heading2'),
            table(['Severitate', 'Sursă', 'Loc', 'Observație'], issue_rows),
        ])
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


def generate_audit_checklist_docx_report(report: AuditChecklistReport, output_path: str | Path, policy: AuditReportPolicy = DEFAULT_POLICY, build_info: BuildInfo | None = None, data_quality_summary: dict[str, Any] | None = None) -> Path:
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
        package.writestr('word/document.xml', build_document_xml(report, policy, metadata, data_quality_summary=data_quality_summary))
    return output


def build_document_xml(report: AuditChecklistReport, policy: AuditReportPolicy = DEFAULT_POLICY, build_info: BuildInfo | None = None, data_quality_summary: dict[str, Any] | None = None) -> str:
    metadata = build_info or get_build_info()
    body = []
    body.extend(build_title_block(report, metadata))
    body.extend(build_auditor_verdict_card_section(report, policy))
    body.extend(build_data_quality_summary_section(report, data_quality_summary, policy))
    body.extend(build_conformity_section(report, policy))
    body.extend(build_amonte_section(report, policy))
    body.append(page_break())
    body.extend(build_aval_section(report, policy))
    body.append(page_break())
    body.extend(build_production_consumption_section(report, policy))
    body.append(page_break())
    body.extend(build_lot_flow_section(report, policy))
    body.extend(build_document_register_section(report, policy))
    body.extend(build_conclusion_section())
    body.extend(build_build_info_section(metadata))
    return wrap_document(''.join(body))


def build_title_block(report: AuditChecklistReport, build_info: BuildInfo) -> list[str]:
    return [
        paragraph('TEST DE TRASABILITATE PENTRU AUDIT', style='Title'),
        literal_paragraph(f'{report.exercise.code} / {report.exercise.lot} — {report.exercise.product_name}', bold=True, align='center', spacing_after=40),
        literal_paragraph('Raportul reunește datele identificate în sursele disponibile pentru codul și lotul analizat. El ajută auditorul să urmărească produsul finit, loturile sursă și documentele fizice care trebuie verificate.', align='center', spacing_after=40),
        literal_paragraph(f'Build raport: {build_info.app_version} / commit {build_info.short_commit} / generat {build_info.generated_at}', align='center', spacing_after=100),
    ]


def build_auditor_verdict_card_section(report: AuditChecklistReport, policy: AuditReportPolicy) -> list[str]:
    main_order = primary_production_order(report)
    return [
        paragraph('Card verdict auditor', style='Heading1'),
        literal_paragraph('Cardul verdict sintetizează cazul de audit și indică zonele principale care trebuie citite înaintea verificării documentelor fizice.', spacing_after=50),
        table(
            ['Indicator audit', 'Status / valoare'],
            [
                ['Verdict audit', report.conclusion_status],
                ['Cod produs finit', report.exercise.code],
                ['Lot produs finit', report.exercise.lot],
                ['Denumire produs finit', policy.name(report.exercise.product_name)],
                ['Dată producție principală', policy.audit_dates(main_order.production_date if main_order else MISSING)],
                ['Cantitate produsă PRD', report.balance.prd_produced],
                ['Stoc produs finit / DSD', policy.stock(report.balance.stock_at_moment)],
                ['Bilanț PRD vs WMS', f'{report.balance.status} — {policy.short(report.balance.observation, 90)}'],
                ['AMONTE / produs finit și livrări', f'{len(report.downstream)} livrări identificate' if report.downstream else MISSING],
                ['AVAL / loturi sursă', f'{len(report.upstream)} linii loturi sursă identificate' if report.upstream else MISSING],
                ['Documente fizice', f'{len(report.document_register)} documente de pregătit' if report.document_register else MISSING],
            ],
        ),
        paragraph('Ghid rapid PP-03', style='Heading2'),
        literal_paragraph('Ghid rapid PP-03: Card verdict, Sumar Data Quality, Rezumat conformare, AMONTE, AVAL, Comenzi producție și consumuri, Fluxuri loturi și documente, Registru documente fizice și Informații build.', spacing_after=50),
        *bullets(QUICK_AUDITOR_GUIDE_ITEMS),
    ]


def build_conformity_section(report: AuditChecklistReport, policy: AuditReportPolicy) -> list[str]:
    rows = [[item.requirement, item.status, policy.short(item.evidence, 95), policy.short(item.observation, 95)] for item in report.conformity]
    return [
        paragraph('Rezumat conformare checklist', style='Heading1'),
        literal_paragraph('Rezumatul de conformare arată dacă raportul conține informațiile necesare pentru verificarea trasabilității. Observațiile explică limitele datelor sau verificările care trebuie completate manual.', spacing_after=50),
        table(['Cerință', 'Status în test', 'Dovezi', 'Observații'], rows),
    ]


def build_amonte_section(report: AuditChecklistReport, policy: AuditReportPolicy) -> list[str]:
    exercise = report.exercise
    balance = report.balance
    main_order = primary_production_order(report)
    downstream_rows = [
        [
            d.client,
            d.address,
            policy.audit_dates(d.delivery_date),
            policy.delivery_document(d.delivery_document_type, d.delivery_document_number),
            d.wms_order,
            d.delivered_quantity,
            policy.downstream_observation(d.observation),
        ]
        for d in report.downstream
    ]
    if not downstream_rows:
        downstream_rows = [[MISSING] * 7]
    return [
        paragraph('AMONTE — Produs finit, producție și livrări', style='Heading1'),
        literal_paragraph('Secțiunea urmărește produsul finit: ce s-a produs, ce s-a livrat și ce documente trebuie verificate pentru confirmare.', spacing_after=50),
        paragraph('Fișa principală a exercițiului', style='Heading2'),
        paragraph('Fișa principală fixează produsul finit și lotul analizat. Această secțiune este punctul de plecare al verificării pentru produsul finit și pentru livrările identificate în sursele oficiale.'),
        table(['Indicator', 'Valoare'], [
            ['Cod produs finit', exercise.code],
            ['Lot produs finit', exercise.lot],
            ['Denumire produs finit', exercise.product_name],
            ['Status verificare', exercise.result],
        ]),
        paragraph('Repere rapide produs finit', style='Heading2'),
        paragraph('Reperele rapide regrupează denumirea produsului, data de producție, cantitatea produsă și stocul produsului finit, pentru o citire rapidă înainte de bilanț și livrări.'),
        table(['Indicator', 'Valoare'], [
            ['Denumire produs finit', exercise.product_name],
            ['Dată producție principală', policy.audit_dates(main_order.production_date if main_order else MISSING)],
            ['Cantitate produsă PRD', balance.prd_produced],
            ['Stoc produs finit / DSD', policy.stock(balance.stock_at_moment)],
        ]),
        paragraph('Bilanț produs finit', style='Heading2'),
        paragraph('Bilanțul compară cantitatea produsă în PRD cu intrările și ieșirile lotului în WMS. Scopul este să confirme că lotul produs poate fi urmărit până la livrările către clienți sau până la stocul rămas.'),
        table(['Indicator', 'Cantitate / status', 'Observație'], [
            ['Cantitate produsă PRD', balance.prd_produced, 'Sursă PRD'],
            ['Intrare WMS produs finit', balance.wms_production_out, 'Intrare produs finit WMS'],
            ['Cantitate livrată WMS', balance.wms_delivered, 'Valoare semnată WMS'],
            ['Stoc produs finit / DSD', policy.stock(balance.stock_at_moment), 'Dacă există în stoc'],
            ['Status bilanț', balance.status, policy.short(balance.observation, 90)],
        ]),
        paragraph('Livrări produs finit', style='Heading2'),
        paragraph('Tabelul arată livrările identificate pentru lotul de produs finit. Auditorul verifică documentul de livrare, clientul, data și cantitatea livrată.'),
        table(['Client', 'Destinație', 'Dată livrare', 'Document livrare', 'Comandă WMS', 'Cantitate livrată', 'Observații'], downstream_rows),
    ]


def build_aval_section(report: AuditChecklistReport, policy: AuditReportPolicy) -> list[str]:
    rows = [
        [
            line.material_type,
            line.code,
            line.lot,
            policy.name(line.name),
            line.document_type,
            line.document_number,
            policy.audit_dates(line.document_date),
            policy.audit_dates(line.receipt_date),
            policy.name(line.supplier),
            checklist_received_quantity(line),
            line.consumed_quantity,
            policy.stock(line.stock_at_moment),
            policy.upstream_observation(line.observation),
        ]
        for line in report.upstream
    ]
    if not rows:
        rows = [[MISSING] * 13]
    return [
        paragraph('AVAL — Materii prime, ambalaje, auxiliare și loturi sursă', style='Heading1'),
        literal_paragraph('Secțiunea arată loturile sursă care intră în produsul finit și documentele prin care ele pot fi urmărite înapoi.', spacing_after=50),
        paragraph('Recepții loturi sursă', style='Heading2'),
        paragraph('Tabelul prezintă recepțiile identificate pentru loturile sursă. Auditorul verifică documentul de recepție, furnizorul, datele documentare, cantitatea și lotul.'),
        table(['Tip material', 'Cod intern', 'Lot sursă', 'Materie primă / ambalaj', 'Tip document', 'Număr document', 'Dată document', 'Dată recepție', 'Furnizor', 'Cantitate recepționată', 'Cantitate consumată', 'Stoc lot sursă', 'Observații'], rows),
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
        paragraph('Comenzi producție și consumuri', style='Heading1'),
        paragraph('Această secțiune leagă comenzile de producție de cantitatea de produs finit obținută și de materialele consumate. Ea ajută auditorul să verifice, pe fiecare comandă, din ce loturi s-a produs lotul finit analizat.'),
        paragraph('Comenzi producție', style='Heading2'),
        paragraph('Tabelul de comenzi sintetizează data de producție, cantitatea produsă și asocierea cu intrarea WMS PRODUCTION-OUT și cu livrarea produsului finit, atunci când aceasta poate fi legată de cantitate și document.'),
        table(['Comandă producție', 'Dată producție', 'Cantitate produsă PRD', 'WMS production-out', 'Livrare PF asociată'], production_order_summary_rows(report.production_consumption, policy)),
        paragraph('Consumuri pe comenzi — tabel operațional', style='Heading2'),
        paragraph('Tabelul operațional detaliază materiile prime și ambalajele deja prezente în model, cu accent pe codul intern, lotul consumat și cantitatea consumată pentru lotul finit analizat.'),
        table(['Comandă', 'Tip material', 'Cod intern consum', 'Lot consum', 'Materie primă / ambalaj', 'Cantitate consumată'], production_consumption_rows(report.production_consumption, policy)),
    ]


def production_order_summary_rows(rows: list[ChecklistProductionConsumption], policy: AuditReportPolicy) -> list[list[str]]:
    summary = OrderedDict()
    for row in rows:
        summary.setdefault(row.production_order, row)
    if not summary:
        return [[MISSING] * 5]
    return [[row.production_order, policy.audit_dates(row.production_date), row.finished_product_quantity, row.wms_production_out, policy.delivery(row.associated_delivery)] for row in summary.values()]


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
        paragraph('Fluxuri loturi și documente', style='Heading1'),
        paragraph('Fluxurile de loturi reunesc informațiile esențiale despre recepții, consumul în lotul auditat, eventualele livrări către terți și stocul rămas. Tabelul este o privire de ansamblu asupra mișcărilor relevante pentru fiecare lot sursă.'),
        table(['Tip', 'Cod', 'Lot', 'Denumire', 'Recepții', 'Consum auditat', 'Livrări terți', 'Stoc', 'Status', 'Observații'], rows),
    ]
    note = policy.overflow_note(len(report.lot_flows), len(selected), 'fluxuri')
    if note:
        parts.append(paragraph(note))
    return parts


def build_document_register_section(report: AuditChecklistReport, policy: AuditReportPolicy) -> list[str]:
    selected = policy.select_document_register(report.document_register)
    headers = ['Bifat', 'Status', 'Sursă', 'Tip document', 'Referință document', 'Cod relevant', 'Lot relevant', 'Comandă relevantă', 'Motiv audit']

    def register_rows(lines: Sequence[ChecklistDocumentRegisterLine]) -> list[list[object]]:
        return [
            [DOCUMENT_REGISTER_CHECKBOX, line.status, line.area, line.document_type, policy.register_reference(line.document_reference), line.related_code, line.related_lot, policy.delivery(line.related_order), policy.register_reason(line.why_needed)]
            for line in lines
        ]

    def register_group(title: str, lines: Sequence[ChecklistDocumentRegisterLine]) -> list[str]:
        if not lines:
            return []
        return [paragraph(title, style='Heading2'), literal_table(headers, register_rows(lines), column_widths=DOCUMENT_REGISTER_COLUMN_WIDTHS)]

    required_lines = [line for line in selected if line.status == 'required']
    recommended_lines = [line for line in selected if line.status == 'recommended']
    other_lines = [line for line in selected if line.status not in {'required', 'recommended'}]

    parts = [
        paragraph('Registru documente fizice', style='Heading1'),
        literal_paragraph('Secțiunea arată documentele fizice care trebuie căutate pentru verificarea auditului, pe baza datelor identificate în sursele disponibile.', spacing_after=50),
    ]
    if not selected:
        parts.append(literal_table(headers, [[MISSING] * len(headers)], column_widths=DOCUMENT_REGISTER_COLUMN_WIDTHS))
    else:
        parts.extend(register_group('Documente required', required_lines))
        parts.extend(register_group('Documente recommended', recommended_lines))
        parts.extend(register_group('Documente cu status neschimbat', other_lines))
    note = policy.overflow_note(len(report.document_register), len(selected), 'documente')
    if note:
        parts.append(paragraph(note))
    return parts


def build_conclusion_section() -> list[str]:
    return [
        paragraph('Concluzie audit intern', style='Heading1'),
        literal_paragraph('Raportul sintetizează datele identificate și documentele care trebuie verificate. El nu completează date lipsă și nu înlocuiește controlul documentelor fizice.', spacing_after=50),
    ]


def build_build_info_section(build_info: BuildInfo) -> list[str]:
    return [
        paragraph('Informații build', style='Heading1'),
        paragraph('Această secțiune identifică versiunea aplicației folosită la generarea raportului, pentru corelare cu diagnosticele GitHub și build-urile instalate local.'),
        literal_table(['Câmp', 'Valoare'], build_info_table_rows(build_info)),
    ]


def xml_attrs(pairs: Iterable[tuple[str, object]]) -> str:
    return ''.join(f' {name}={Q}{html.escape(str(value), quote=False)}{Q}' for name, value in pairs if value is not None)


def literal_paragraph(text: object, style: str | None = None, bold: bool = False, align: str | None = None, spacing_before: int | None = None, spacing_after: int | None = None) -> str:
    style_attrs = xml_attrs([('w:val', style)]) if style else ''
    style_xml = f'<w:pStyle{style_attrs}/>' if style else ''
    align_attrs = xml_attrs([('w:val', align)]) if align else ''
    align_xml = f'<w:jc{align_attrs}/>' if align else ''
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
    border_attrs = xml_attrs([('w:val', 'single'), ('w:sz', 4), ('w:space', 0), ('w:color', '808080')])
    borders = (
        f'<w:tblBorders><w:top{border_attrs}/>'
        f'<w:left{border_attrs}/>'
        f'<w:bottom{border_attrs}/>'
        f'<w:right{border_attrs}/>'
        f'<w:insideH{border_attrs}/>'
        f'<w:insideV{border_attrs}/></w:tblBorders>'
    )
    table_style_attrs = xml_attrs([('w:val', 'TraceAITable')])
    table_properties = apply_table_layout_properties(f'<w:tblStyle{table_style_attrs}/>')
    return f'<w:tbl><w:tblPr>{table_properties}{borders}</w:tblPr>{"".join(xml_rows)}</w:tbl>'


def literal_table_row(values: Iterable[object], is_header: bool = False, column_widths: Sequence[int] | None = None) -> str:
    cells = []
    for index, value in enumerate(values):
        width = column_widths[index] if column_widths and index < len(column_widths) else None
        cells.append(literal_table_cell(value, is_header=is_header, width=width))
    return f'<w:tr>{table_row_properties_xml(is_header)}{"".join(cells)}</w:tr>'


def literal_table_cell(value: object, is_header: bool = False, width: int | None = None) -> str:
    shading_attrs = xml_attrs([('w:fill', 'EDEDED')]) if is_header else ''
    shading_xml = f'<w:shd{shading_attrs}/>' if is_header else ''
    bold_xml = '<w:b/>' if is_header else ''
    size = '15' if is_header else '14'
    text = str(value).strip() if value is not None else MISSING
    width_attrs = xml_attrs([('w:w', width), ('w:type', 'dxa')]) if width is not None else ''
    width_xml = f'<w:tcW{width_attrs}/>' if width is not None else ''
    margin_top_attrs = xml_attrs([('w:w', 40), ('w:type', 'dxa')])
    margin_left_attrs = xml_attrs([('w:w', 40), ('w:type', 'dxa')])
    margin_bottom_attrs = xml_attrs([('w:w', 40), ('w:type', 'dxa')])
    margin_right_attrs = xml_attrs([('w:w', 40), ('w:type', 'dxa')])
    cell_properties = apply_cell_layout_properties(f'{width_xml}{shading_xml}<w:tcMar><w:top{margin_top_attrs}/><w:left{margin_left_attrs}/><w:bottom{margin_bottom_attrs}/><w:right{margin_right_attrs}/></w:tcMar>')
    safe_text = html.escape(text or MISSING, quote=False)
    spacing_attrs = xml_attrs([('w:after', 0)])
    size_attrs = xml_attrs([('w:val', size)])
    font_attrs = xml_attrs([('w:ascii', 'Arial'), ('w:hAnsi', 'Arial')])
    return f'<w:tc><w:tcPr>{cell_properties}</w:tcPr><w:p><w:pPr><w:spacing{spacing_attrs}/></w:pPr><w:r><w:rPr>{bold_xml}<w:sz{size_attrs}/><w:rFonts{font_attrs}/></w:rPr><w:t>{safe_text}</w:t></w:r></w:p></w:tc>'


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
    generate_audit_checklist_docx_report(checklist_report, args.output, data_quality_summary=traceability_case.sections.get('data_quality'))
    return 0 if checklist_report.conclusion_status != 'INCOMPLETE' else 1


if __name__ == '__main__':
    raise SystemExit(main())
