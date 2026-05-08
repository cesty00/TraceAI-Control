# TraceAI Control — Modul Trasabilitate

TraceAI Control generează raport DOCX auditabil pentru trasabilitatea unui articol și lot.

## Status curent

```text
stadiu: Strict Audit / Data Quality / Typed Errors / Packaging / Observability / Report Quality / Preflight
etapă produs validată oficial pe main: ERRORS-01_PR2_4_DONE
ultimul stage produs închis oficial pe main: ERRORS-01_PR2_4_DONE
ultimul stage REPORT-QUALITY închis pe main: REPORT-QUALITY-01E-3_DONE
etapă produs activă pe main: PREFLIGHT-UI-01
slice completat și merge-uit pe main: PREFLIGHT-UI-01A prin PR #113
status oficial de etapă pentru PREFLIGHT-UI-01: activ, fără DONE claim
micro-stage documentar curent: PP03-DOCX-ENRICHMENT-01A-STATUS-SYNC
claim production-ready: NU
claim daily-use release: NU
claim release finalized: NU
ultimul pilot real controlat consemnat: REAL-TEST-PILOT-01 = PASS_WITH_OBSERVATIONS
următorul pas de proiect: decizie între PREFLIGHT-UI-01B / FULL-DIAGNOSTICS-MAIN-01 / REAL-CASE-VALIDATION-04_MATRIX_EXECUTION
ultimul diagnostic produs oficial inspectat direct: run #220, smoke pytest 164 passed
ultimul head validat oficial pentru ERRORS-01_PR2_4: d9fef1be26fb1b3f3ace527d4bc521891f58ccd6
ultimul PR merge-uit de produs pe main: #123
ultimul PR documentar / procedural merge-uit pe main: #122
ultimele PR-uri relevante deja pe main: #121, #122, #123
```

Etapa activă și starea oficială se citesc din `CHECKPOINT.md`, `AGENTS.md` și `docs/robocop_operating_manual.md`.

Acest sync documentar consemnează că `PP03-DOCX-ENRICHMENT-01A` a fost integrat tehnic pe `main` prin PR #123, dar nu afirmă validare oficială verde post-merge pentru acel PR și nu promovează nicio etapă la `DONE`.

Documentul oficial relevant pentru această linie de lucru este:

```text
docs/pp03_data_gap_analysis_01.md
```

## Robocop operating role

Robocop este agentul de software engineering, arhitectură, implementare, validare și project-control pentru `TraceAI-Control`.

Regulile operaționale persistente sunt definite în:

```text
AGENTS.md
docs/robocop_operating_manual.md
docs/robocop_preflight_roles_and_skills.md
docs/robocop_full_project_operating_system.md
docs/real_test_pilot_01.md
docs/real_test_pilot_01_operator_checklist.md
docs/real_test_pilot_01_execution_record.md
docs/pp03_data_gap_analysis_01.md
```

Robocop trebuie să acționeze ca developer atunci când etapa cere programare: inspectează codul, propune designul minim sigur, implementează, adaugă teste, pregătește validarea GitHub și nu marchează `DONE` fără TraceAI Diagnostics verde și artifact inspectat.

Actualizările recente de orchestrare și operare au adăugat reguli pentru autonomie controlată, roluri preflight/pilot, fallback manual pentru diagnostic și limite explicite pentru mutații. Aceste schimbări documentare nu promovează singure produsul la o etapă nouă validată.

## PREFLIGHT-UI status

`PREFLIGHT-UI-01A` este deja merge-uit pe `main` prin PR #113 și este tratat oficial în acest sync ca:

```text
merged
completed
```

Acest slice adaugă:

```text
operator-facing source status mapping
operator-facing overall guidance pentru continue / continue with attention / stop before generation
```

și păstrează limitele arhitecturale:

```text
fără business logic în UI
fără schimbare de DTO audit
fără schimbare de contract audit_checklist_ui.json
fără schimbare de renderer DOCX
```

Acest README sync nu afirmă validare oficială nouă pentru `PREFLIGHT-UI-01A` și nu marchează `PREFLIGHT-UI-01` ca `DONE`.

## PP03 DOCX status

`PP03-DOCX-ENRICHMENT-01A` este acum integrat tehnic pe `main` prin PR #123.

Acest merge consemnează doar:

```text
clarificare de prezentare în DOCX pentru câmpuri PP03 clasificate strict B și deja prezente în modelul curent
regrupare / relabeling / wording / placement în checklist-ul DOCX existent
fără folosirea PP-03 ca sursă de input
fără schimbare de DTO sau JSON
fără schimbare de calcule sau verdict rules
fără schimbare de extraction logic, source mappings sau unit handling
```

Acest README sync nu afirmă validare oficială verde post-merge pentru PR #123 și nu pornește `PP03-DOCX-ENRICHMENT-01B`.

## REAL-TEST-PILOT-01 status

`REAL-TEST-PILOT-01` este acum documentat prin definiție, checklist scurt și execution record dedicat.

Rezultatul documentat pentru pilot este:

```text
case: DS099903883 / 105.26
commit: bc6d3d79b17f3b5e5c379e43f6ed3109f622031a
build channel: github-actions-installer
sources found: 4/4
preflight: WARNING
blockers: none
Data Quality: ERROR explicit
result: PASS_WITH_OBSERVATIONS
artifacts retained: yes
```

Acest rezultat nu declară:

```text
production-ready
daily-use internal release
release finalized
etapă produs DONE
```

## Diagnostics orchestration

TraceAI Diagnostics are o cale controlată de dispatch pentru orchestrare manuală / agentică.

Status:

```text
PR #110: ci: add controlled diagnostics dispatch trigger
scope: workflow-only
production code changed: no
tests changed: no
release claim: no
product DONE claim: no
```

Această cale ajută Robocop să declanșeze sau să coordoneze validarea în mod controlat, dar nu înlocuiește regula de validare oficială: `DONE` pentru produs cere workflow verde și artifact inspectat.

## Flux validat

```text
surse reale
-> TraceabilityCase
-> AuditTraceabilityReport
-> AuditChecklistReport
-> Audit Checklist DOCX
-> audit-checklist-ui.v1 JSON
```

## Surse oficiale

Aplicația caută și normalizează aliasuri pentru:

```text
trasabilitate_wms.csv / trasabilitate_wms.zip
raport_productie.csv / rapoarte productie.csv / rapoarte_productie.csv
nomenclator.xlsx
stoc_la_moment_original.xlsx / stoc la moment original.xlsx
```

## Reguli importante

```text
UI nu conține logică de business.
UI nu citește direct CSV/XLSX.
UI nu parsează DOCX.
DOCX și UI folosesc aceeași sursă de adevăr audit.
Unitățile de măsură nu se convertesc automat.
Gazul / ALISOL rămâne auxiliar / consumabil tehnologic.
Valorile lipsă rămân explicite: FARA DATE IDENTIFICATE.
Rapoartele FINISHED_PRODUCT cu dovezi esențiale lipsă se marchează explicit INCOMPLETE.
Erorile blocante uzuale sunt clasificate în engine ca typed errors înainte de a ajunge în UI.
Cazurile cu date selectate dar clasificare ambiguă rămân blocate în engine prin `AmbiguousCaseTypeError`.
Sursele oficiale prezente dar ilizibile/corupte sunt blocate prin `DataQualityBlockingError` înainte de fallback generic.
Validarea oficială pentru DONE este doar GitHub Actions / TraceAI Diagnostics cu artifact inspectat.
Smoke-only validation nu înlocuiește full diagnostics când full diagnostics sunt necesare.
PP-03 rămâne output reference, nu input source.
```

## Raport DOCX audit

Raportul DOCX este orientat către audit tipărit:

```text
landscape
card verdict auditor pe prima pagină
ghid rapid auditor
secțiuni numerotate
tabele compacte cu header repetabil
rezumat de conformare checklist
sumar Data Quality în conformitate
registru documente fizice cu checkbox tipărit
header cu titlu raport, cod produs, lot și denumire produs
footer cu versiune aplicație, commit, canal build, dată generare și număr pagină
marcare explicită a cazurilor incomplete pentru audit strict
```

Liniile `REPORT-QUALITY-01E-1`, `REPORT-QUALITY-01E-2` și `REPORT-QUALITY-01E-3` sunt validate oficial prin TraceAI Diagnostics.

Checklist DOCX-ul generat conține textul aprobat din `Card verdict auditor`, textul aprobat din introducerea `Ghid rapid pentru auditor` și textul aprobat din `Rezumat de conformare checklist`.

PR #123 adaugă pe `main` o clarificare de prezentare pentru `PP03-DOCX-ENRICHMENT-01A`, limitată la câmpuri deja existente în modelul curent și fără schimbare de logică sau de contracte.

## UI

UI-ul vizual este Tkinter și orchestrează fluxul validat fără business logic.

Funcții validate sau prezente pe `main`:

```text
Verifică surse
Previzualizează audit checklist
Generează Diagnostic ZIP
Generează raport DOCX
status operator-facing pentru preflight surse
```

Mesajele UI pot returna acum:

```text
mesaj pentru utilizator
detaliu tehnic separat
acțiune recomandată
```

prin `TraceAIError`, fără stack trace brut în fluxul normal.

Secțiunea UI JSON pentru conformitate folosește același text aprobat `01E-3` ca și checklist DOCX.

## Diagnostic local

Generatorul local de diagnostic ZIP este disponibil din CLI și din UI:

```powershell
python -m src.support.diagnostic_bundle <sources> --code <code> --lot <lot> --output <zip>
```

Output best-effort:

```text
build_info.json
source_inventory.json
preflight.json
audit_checklist_ui.json sau error JSON
manifest.json
README.txt
opțional reports/*.docx
```

Important: diagnosticul local este util pentru investigație și suport, dar nu înlocuiește validarea oficială GitHub necesară pentru promovarea unei etape la `DONE`.

## Build Windows

Workflow-ul GitHub Actions pentru artifact Windows este disponibil:

```text
.github/workflows/windows-app-build.yml
```

Scop:

```text
construiește artifact Windows
injectează traceai_build_info.json
verifică build_commit == GITHUB_SHA
urcă artifact ZIP descărcabil
```

## Testare

```text
ultimul artifact produs oficial inspectat direct: TraceAI-Diagnostics-Smoke din run #220
ultimul head validat oficial pentru ERRORS-01_PR2_4: d9fef1be26fb1b3f3ace527d4bc521891f58ccd6
smoke pytest: 164 passed in 0.94s
artifactul smoke conține pytest-output.txt și diagnostic-summary.md
reference_comparison.md nu se aplică pe acest smoke-only path
AGENTS.md stabilește explicit că testele locale sunt doar investigație, nu validare oficială pentru DONE
```

## Release readiness

Starea curentă susține doar evaluare controlată:

```text
pre-release internal candidate / controlled internal pilot
```

Nu există claim pentru:

```text
production-ready
daily-use internal release
release finalized
```

## Checkpoint

Starea completă și următorul pas se află în:

```text
CHECKPOINT.md
```

Regulă: `CHECKPOINT.md` și `README.md` se actualizează împreună după fiecare PR merge-uit, diagnostic verde important, validare Windows sau schimbare de etapă.
