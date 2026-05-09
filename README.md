# TraceAI Control — Modul Trasabilitate

TraceAI Control generează raport DOCX auditabil pentru trasabilitatea unui articol și lot.

## Status curent

```text
stadiu: Strict Audit / Data Quality / Typed Errors / Packaging / Observability / Report Quality / Preflight
etapă produs validată oficial pe main: ERRORS-01_PR2_4_DONE
ultimul stage produs închis oficial pe main: ERRORS-01_PR2_4_DONE
ultimul stage REPORT-QUALITY închis pe main: REPORT-QUALITY-01E-3_DONE
etapă produs activă pe main: PREFLIGHT-UI-01
slice completat și merge-uit pe main: PREFLIGHT-UI-01B prin PR #129
status oficial de etapă pentru PREFLIGHT-UI-01: activ, fără DONE claim
micro-stage documentar curent: PREFLIGHT-UI-01B-STATUS-SYNC
claim production-ready: NU
claim daily-use release: NU
claim release finalized: NU
ultimul pilot real controlat consemnat: REAL-TEST-PILOT-01 = PASS_WITH_OBSERVATIONS
următorul pas de proiect: decizie separată pentru următorul micro-stage după acest sync docs-only
ultimul diagnostic produs oficial inspectat direct: run 25593679232, full diagnostics 179 passed in 1.94s
ultimul head validat oficial pentru acest sync limitat: 37b12def62ab70789cf03ba501ccf573bc495e39
ultimul PR merge-uit de produs pe main: #129
ultimul sync documentar relevant pe main se confirmă din CHECKPOINT.md și din istoricul PR-urilor merge-uite
PR-urile relevante pe main pentru acest context se urmăresc din CHECKPOINT.md și din istoricul PR-urilor merge-uite
```

Etapa activă și starea oficială se citesc din `CHECKPOINT.md`, `AGENTS.md` și `docs/robocop_operating_manual.md`.

Acest sync documentar consemnează că PR #129 a fost integrat tehnic pe `main` în commitul `37b12def62ab70789cf03ba501ccf573bc495e39` și validat post-merge prin TraceAI Diagnostics run `25593679232` pe cazul implicit `DS099903883 / 105.26`, cu `Tests and diagnostic report = success`, `179 passed in 1.94s`, `reference_comparison.md = PASS`, artifact `TraceAI-Diagnostics` generat, `real_audit_checklist_report.docx` generat și `real_audit_checklist_ui.json` generat.

În aceeași validare oficială post-merge, `PREFLIGHT-UI-01B` este consemnat limitat ca funcționalitate UI de control: generarea raportului DOCX este gate-uită de ultimul preflight relevant pentru combinația curentă `source_directory + code + lot`.

Limitare obligatorie pentru acest sync: aceasta este validare oficială de integrare pe `main`, nu release, nu production-ready, nu daily-use, nu product DONE extins, nu validare legală/comercială finală și nu închide automat `PREFLIGHT-UI-01`.

Starea oficială relevantă pentru acest sync se citește din:

```text
CHECKPOINT.md
README.md
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

`PREFLIGHT-UI-01B` este deja merge-uit pe `main` prin PR #129 și este tratat oficial în acest sync ca:

```text
merged
completed slice on main
validated post-merge on main with limited-scope official evidence
```

Acest slice adaugă limitat:

```text
gate pentru generarea DOCX pe baza ultimului preflight relevant pentru source_directory + code + lot
invalidarea gate-ului când source_directory / code / lot se schimbă
confirmare explicită la WARNING
blocare la BLOCKER sau fără preflight curent
Diagnostic ZIP rămâne în afara gate-ului DOCX
```

și păstrează limitele arhitecturale:

```text
fără business logic în UI
fără schimbare de DTO audit
fără schimbare de contract audit_checklist_ui.json
fără schimbare de renderer DOCX
```

Acest README sync nu marchează `PREFLIGHT-UI-01` ca `DONE`.

## Data Quality severity status

`DATA-QUALITY-SEVERITY-TRIAGE-02` rămâne integrat tehnic pe `main` prin PR #127.

Acest README păstrează limitat starea deja consemnată:

```text
integrare tehnică pe main prin PR #127
merge commit: 4651657bc8898bf1f2a06ee5a575c2b28da5a9e4
TraceAI Diagnostics run 25574554193 = success
validation case: DS099903883 / 105.26
pytest: 173 passed in 1.91s
reference_comparison.md = PASS
artifact TraceAI-Diagnostics generat
real_audit_checklist_report.docx și real_audit_checklist_ui.json generate
real_audit_checklist_ui.json confirmă lista textuală Data Quality issues în report.data_quality.issues
Sheet2 / nomenclator.xlsx este WARNING, nu ERROR, când sheet-ul principal valid există
report.data_quality.status = WARNING
error_count = 0
warning_count = 8
issue_count = 8
```

Acest README sync nu afirmă:

```text
release
production-ready
daily-use
product DONE extins
închidere automată PREFLIGHT-UI-01
validare legală/comercială finală
```

## PP03 DOCX status

`PP03-DOCX-ENRICHMENT-01B` rămâne integrat tehnic pe `main` prin PR #125.

Acest README păstrează limitat starea deja consemnată:

```text
integrare tehnică pe main prin PR #125
merge commit: d1adc08ed88844cca750b7e5fa761f61e00c5767
main diagnostics #257 = success
validation case: DS099903883 / 105.26
pytest: 172 passed
reference_comparison.md = PASS
real_audit_checklist_report.docx și real_audit_checklist_ui.json generate
real_audit_checklist_report.docx conține Cantitate recepționată
```

Acest README sync nu reinterpretă PP03 01B și nu afirmă:

```text
release
production-ready
daily-use
dedicated separate PP03 scenario validation
product DONE extins
```

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

PR #123 adaugă pe `main` o clarificare de prezentare pentru `PP03-DOCX-ENRICHMENT-01A`, iar PR #125 rămâne consemnat aici pentru `PP03-DOCX-ENRICHMENT-01B`, limitat la dovada oficială de integrare pe `main` și fără claim de validare PP03 dedicată separată.

## UI

UI-ul vizual este Tkinter și orchestrează fluxul validat fără business logic.

Funcții validate sau prezente pe `main`:

```text
Verifică surse
Previzualizează audit checklist
Generează Diagnostic ZIP
Generează raport DOCX
status operator-facing pentru preflight surse
gate DOCX bazat pe ultimul preflight relevant pentru source_directory + code + lot
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
ultimul artifact produs oficial inspectat direct: TraceAI-Diagnostics din run 25593679232
ultimul head validat oficial pentru acest sync limitat: 37b12def62ab70789cf03ba501ccf573bc495e39
pytest: 179 passed in 1.94s
reference_comparison.md = PASS
artifactul inspectat include real_audit_checklist_report.docx și real_audit_checklist_ui.json
funcționalitatea PREFLIGHT-UI-01B consemnată aici: gate DOCX după ultimul preflight relevant pentru source_directory + code + lot
aceasta este validare oficială generică pe main, nu release, nu production-ready și nu extinde produsul la DONE
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
