# TraceAI Control — Modul Trasabilitate

TraceAI Control generează raport DOCX auditabil pentru trasabilitatea unui articol și lot.

## Status curent

```text
stadiu: Strict Audit / Data Quality / Typed Errors / Packaging / Observability / Report Quality
etapă curentă: REPORT-QUALITY-01E-2_DONE
următorul pas recomandat: selectarea explicită a următorului micro-stage
alternativă imediată: un nou pas ERRORS-01 pentru maparea altor erori de nivel mai jos
ultimul checkpoint oficial: CHECKPOINT.md
ultimul diagnostic oficial inspectat direct: 160 passed, reference_comparison PASS
ultimul commit validat oficial pentru 01E-2: 4949314982b55d36ef254300d352147938178add
ultimul PR merge-uit de produs: #81
```

Etapa activă și starea oficială se citesc din `CHECKPOINT.md`, `AGENTS.md` și `docs/robocop_operating_manual.md`.

## Robocop operating role

Robocop este agentul de software engineering, arhitectură, implementare, validare și project-control pentru `TraceAI-Control`.

Regulile operaționale persistente sunt definite în:

```text
AGENTS.md
docs/robocop_operating_manual.md
```

Robocop trebuie să acționeze ca developer atunci când etapa cere programare: inspectează codul, propune designul minim sigur, implementează, adaugă teste, pregătește validarea GitHub și nu marchează `DONE` fără TraceAI Diagnostics verde și artifact inspectat.

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
Validarea oficială pentru DONE este doar GitHub Actions / TraceAI Diagnostics cu artifact inspectat.
PP-03 este în afara fluxului curent Report Quality.
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

Liniile `REPORT-QUALITY-01E-1` și `REPORT-QUALITY-01E-2` sunt validate oficial prin TraceAI Diagnostics. Checklist DOCX-ul generat conține atât textul aprobat din `Card verdict auditor`, cât și textul aprobat din introducerea `Ghid rapid pentru auditor`.

## UI

UI-ul vizual este Tkinter și orchestrează fluxul validat fără business logic.

Funcții validate:

```text
Verifică surse
Previzualizează audit checklist
Generează Diagnostic ZIP
Generează raport DOCX
```

Mesajele UI pot returna acum:

```text
mesaj pentru utilizator
detaliu tehnic separat
acțiune recomandată
```

prin `TraceAIError`, fără stack trace brut în fluxul normal.

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
ultimul artifact oficial inspectat direct: 160 passed, reference_comparison.md = PASS
ultimul commit validat oficial pentru 01E-2: 4949314982b55d36ef254300d352147938178add
real_audit_checklist_report.docx și real_audit_checklist_ui.json generate în fluxul de diagnostic
textul aprobat pentru Ghid rapid este prezent în DOCX-ul oficial generat
AGENTS.md stabilește explicit că testele locale sunt doar investigație, nu validare oficială pentru DONE
```

## Checkpoint

Starea completă și următorul pas se află în:

```text
CHECKPOINT.md
```

Regulă: `CHECKPOINT.md` și `README.md` se actualizează împreună după fiecare PR merge-uit, diagnostic verde important, validare Windows sau schimbare de etapă.
