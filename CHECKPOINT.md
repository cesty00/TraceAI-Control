# CHECKPOINT — TraceAI Control / Audit Checklist Report & UI JSON

Data checkpoint: 2026-04-30

## Repo

```text
cesty00/TraceAI-Control
```

## Starea curentă pe scurt

Am trecut de la raportul DOCX tehnic la un flux audit checklist coerent, testat și pregătit pentru UI:

```text
surse reale
 -> TraceabilityCase
 -> AuditTraceabilityReport
 -> AuditChecklistReport
 -> DOCX audit checklist
 -> JSON UI audit checklist
```

Decizia critică validată: **DOCX-ul și interfața trebuie să consume același model audit (`AuditChecklistReport`)**, nu să reconstruiască separat datele.

## Ultimul commit creat înainte de pauză

```text
da1ecc2dfbeeb91c00e49b46cc1edf2d4ea438ae
Upload audit checklist UI JSON in diagnostics
```

Acest commit leagă JSON-ul UI în workflow-ul `TraceAI Diagnostics` ca artifact separat:

```text
diagnostics/real_audit_checklist_ui.json
diagnostics/real-audit-checklist-ui-json-output.txt
```

## Ultimul diagnostic verde confirmat

Commit verificat:

```text
a2b7f514e01be75c3b65dba4d6acc09f708accd5
Fix audit checklist UI JSON expected fixture sources
```

Rezultat:

```text
66 passed in 0.72s
reference_comparison.md = PASS
```

Comparator independent pentru `DS099903883 / 105.26`:

```text
Status: PASS
production_order_count: PASS
raw_material_count: PASS
packaging_count: PASS
auxiliary_count: PASS
delivery_count: PASS
production_totals: PASS
raw_material_totals: PASS
packaging_totals: PASS
auxiliary_totals: PASS
delivery_totals: PASS
```

Surse detectate corect în diagnostic:

```text
WMS: trasabilitate_wms.csv extras din trasabilitate_wms.zip
PRD: raport_productie.csv
Nomenclator: nomenclator.xlsx
Stock: stoc_la_moment_original.xlsx
```

## Diagnostic care trebuie rulat la reluare

Primul lucru după pauză:

```text
Rulează TraceAI Diagnostics pe commitul:
da1ecc2dfbeeb91c00e49b46cc1edf2d4ea438ae
```

Așteptare:

```text
66 passed
reference_comparison.md = PASS
artifact nou: real_audit_checklist_ui.json
```

Dacă acest diagnostic este verde, se poate începe `UI-AUDIT-02`.

## Milestone-uri finalizate în sesiunea curentă

### 1. AuditChecklistReport stabilizat

Modelul `AuditChecklistReport` a fost creat și testat ca structură finală pentru raportul audit.

Acoperă:

```text
conformity
exercise
balance
downstream
upstream
production_consumption
lot_flows
document_register
conclusion
```

Fișiere relevante:

```text
src/audit/audit_checklist_report.py
tests/test_audit_checklist_report.py
```

### 2. Renderer DOCX checklist audit

A fost creat rendererul separat:

```text
src/report/audit_checklist_docx.py
```

Artifact generat în workflow:

```text
diagnostics/real_audit_checklist_report.docx
```

Status:

```text
Raportul are structura checklist:
- TEST DE TRASABILITATE PENTRU AUDIT
- Rezumat de conformare checklist
- 01_EXERCITIU
- Bilanț produs finit
- 03_TABEL_II_AVAL
- 02_TABEL_I_AMONTE
- 04_PRODUCTIE_CONSUM
- 05_FLUX_LOTURI_SI_DOCUMENTE
- Registru documente fizice
- Concluzie audit intern
```

Au fost eliminate formulările de dezvoltare:

```text
NU mai apare „test local”
NU mai apare „prototip”
NU mai apare „politică audit”
```

Au fost adăugate explicații formale, dar prietenoase, înaintea tabelelor.

Fișiere relevante:

```text
src/report/audit_checklist_docx.py
tests/test_audit_checklist_docx.py
```

### 3. Politică de raportare audit

A fost introdusă:

```text
AuditReportPolicy
```

Rol:

```text
- compactare controlată a numelor / observațiilor / recepțiilor
- selecție inteligentă a fluxurilor relevante
- prioritizare documente în registru
- păstrarea raportului auditabil, nu dump tehnic
```

Important: politica afectează randarea raportului, nu datele brute din motor.

### 4. Date completate parțial din surse

Implementări făcute:

```text
src/rules/prd_table_mapping.py
```

Adăugat:

```text
- Data livrare în livrările WMS
- Data document în livrările WMS
- Data recepție în recepțiile WMS
- Data document în recepțiile WMS
- Data producției / DDM pregătite pentru PRD dacă apar în surse
```

Atenție: o regresie a fost reparată.

Problemă apărută:

```text
Data livrare fusese inclusă în cheia de grupare WMS și a spart 3 livrări în 7.
```

Fix:

```text
02c7ad2ccef1628c1387aba133b419f32f468a72
Keep WMS delivery dates without splitting delivery groups
```

Rezultat confirmat ulterior:

```text
delivery_count: PASS
expected: 3
actual: 3
```

### 5. Adresă/depozit pentru livrări aval

În `audit_checklist_report.py` s-a adăugat separarea client / depozit din câmpul WMS `Partener`.

Exemplu:

```text
REWE (ROMANIA) SRL_-DEPOZIT TURDA
```

devine:

```text
client = REWE (ROMANIA) SRL
adresă/depozit = DEPOZIT TURDA
```

Confirmat în DOCX:

```text
DEPOZIT TURDA
DEPOZIT FILIASI
DEPOZIT STEFANESTI
```

### 6. Parser recepții WMS pregătit pentru date

În `audit_checklist_report.py`, parserul recepțiilor poate interpreta:

```text
document/furnizor: cantitate
document/furnizor/data: cantitate
document/furnizor | data data: cantitate
```

Câmpuri pregătite pentru Tabel I:

```text
dată recepție
furnizor
tip document
număr document
dată document
```

### 7. JSON UI audit checklist

A fost creat modulul:

```text
src/ui/audit_checklist_json.py
```

Contract:

```text
schema_version = audit-checklist-ui.v1
```

Payload:

```text
{
  "schema_version": "audit-checklist-ui.v1",
  "subject": {
    "code": "...",
    "lot": "...",
    "product_name": "...",
    "case_type": "...",
    "result": "..."
  },
  "sections": [... ordine UI ...],
  "report": { ... AuditChecklistReport complet ... }
}
```

Ordine secțiuni UI blocată prin teste:

```text
conformity
exercise
balance
downstream
upstream
production_consumption
lot_flows
document_register
conclusion
```

Teste relevante:

```text
tests/test_audit_checklist_ui_json.py
```

## Commituri importante recente

```text
02c7ad2ccef1628c1387aba133b419f32f468a72
Keep WMS delivery dates without splitting delivery groups

9f21fa4d75f1e80c30d8ae72f56bc652e1c13978
Expose audit checklist report as UI JSON

d825c642dc63417e1426a799059c9fbb22f0267f
Add audit checklist UI JSON contract tests

26f5217fb6294845bc4fcb8bb45fec693825ca6c
Fix audit checklist UI JSON expected product name

a2b7f514e01be75c3b65dba4d6acc09f708accd5
Fix audit checklist UI JSON expected fixture sources

da1ecc2dfbeeb91c00e49b46cc1edf2d4ea438ae
Upload audit checklist UI JSON in diagnostics
```

## Reguli de arhitectură care rămân obligatorii

```text
1. UI-ul nu conține logică de business.
2. UI-ul trebuie să consume AuditChecklistReport / audit-checklist-ui.v1.
3. DOCX-ul și UI-ul trebuie să aibă aceeași sursă de adevăr.
4. Nu se parsează din DOCX pentru UI.
5. Nu se reconstruiesc tabelele în UI din TraceabilityCase brut dacă există AuditChecklistReport.
6. Unitățile de măsură nu se convertesc automat.
7. Gazul / ALISOL rămâne auxiliar / gaz, nu materie primă alimentară.
8. Dacă o informație nu există în surse, rămâne explicit FARA DATE IDENTIFICATE.
9. Comparatorul independent trebuie să rămână PASS pe cazul default DS099903883 / 105.26.
10. Testele trebuie rulate pe mai multe cazuri, nu doar pe DS099903883.
```

## Ce NU este încă finalizat

```text
1. UI-AUDIT-02 nu este început încă.
2. Interfața vizuală nu consumă încă audit-checklist-ui.v1.
3. real_audit_checklist_ui.json este legat în workflow, dar trebuie verificat prin diagnostic pe da1ecc2.
4. Datele de livrare / recepție sunt expuse parțial, dar legarea completă în toate tabelele trebuie urmărită în continuare.
5. Data producției și DDM sunt pregătite în mapping, dar trebuie validate în raport pe sursele reale.
6. Raportul DOCX checklist nu este încă exportul implicit final al aplicației; este artifact separat de diagnostic.
```

## Următorul pas după pauză

### Pas 1 — Diagnostic

Rulează `TraceAI Diagnostics` pe:

```text
da1ecc2dfbeeb91c00e49b46cc1edf2d4ea438ae
```

Verifică:

```text
66 passed
reference_comparison.md = PASS
real_audit_checklist_ui.json există în artifact
real-audit-checklist-ui-json-output.txt există sau este acceptabil dacă este gol
```

### Pas 2 — UI-AUDIT-02

Dacă diagnosticul este verde:

```text
UI-AUDIT-02 — Map interface sections to AuditChecklistReport / audit-checklist-ui.v1
```

Obiectiv:

```text
Interfața aplicației să afișeze secțiunile din payload["sections"], nu din logica veche.
```

Ordinea afișării:

```text
1. Rezumat de conformare checklist
2. 01_EXERCITIU — Fișa principală
3. Bilanț produs finit
4. 03_TABEL_II_AVAL — Livrări produs finit
5. 02_TABEL_I_AMONTE — Materii prime, ambalaje și auxiliare
6. 04_PRODUCTIE_CONSUM — Detaliere pe comenzi
7. 05_FLUX_LOTURI_SI_DOCUMENTE — Fluxuri loturi
8. Registru documente fizice
9. Concluzie audit intern
```

### Pas 3 — UI-AUDIT-03

După UI-AUDIT-02:

```text
Add regression test: JSON-ul folosit de UI conține aceleași valori ca DOCX-ul / AuditChecklistReport.
```

## Fraza recomandată de reluare

```text
Continuăm de la CHECKPOINT.md actualizat: ultimul diagnostic verde este a2b7f514 cu 66 passed și PASS comparator; primul pas este să verificăm da1ecc2 pentru artifactul real_audit_checklist_ui.json, apoi începem UI-AUDIT-02 ca interfața să consume audit-checklist-ui.v1.
```
