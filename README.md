# TraceAI Control — Modul Trasabilitate

TraceAI Control generează raport DOCX auditabil pentru trasabilitatea unui articol și lot.

## Status curent

```text
stadiu: Strict Audit / Data Quality / Typed Errors / Packaging / Observability / Report Quality
etapă curentă: ERRORS-01_PR2_2_DONE
implementare prezentă pe main, în așteptarea validării: REPORT-QUALITY-01E-1_IMPLEMENTED_PENDING_VALIDATION
următoarea etapă recomandată: confirmarea validării pentru REPORT-QUALITY-01E-1, apoi promovare la DONE
alternativă după validare: REPORT-QUALITY-01E-2 sau un nou pas ERRORS-01 pentru maparea altor erori de nivel mai jos
ultimul checkpoint oficial: CHECKPOINT.md
ultimul diagnostic inspectat direct în sesiunea curentă: 152 passed, reference_comparison PASS
ultimul PR merge-uit cu validare direct inspectată: #76
ultimul commit implementat pentru 01E-1 pe main: 3a65409547d683fc7be5d8633ac88212c3a2fe4a
```

Etapa activă și starea oficială se citesc din `CHECKPOINT.md`.

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

Implementarea curentă 01E-1 a introdus primul text block aprobat în `Card verdict auditor`, fără schimbare de business logic, UI JSON sau calcule. Validarea GitHub pentru acest pas nu este încă confirmată în sesiunea curentă.

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
ultimul artifact inspectat direct: 152 passed, reference_comparison.md = PASS
ultimul PR merge-uit cu validare inspectată direct: #76
real_audit_checklist_report.docx și real_audit_checklist_ui.json generate în fluxul de diagnostic
pentru commitul 01E-1 implementat pe main, validarea GitHub nu este încă vizibilă în interogările disponibile din sesiunea curentă
```

## Checkpoint

Starea completă și următorul pas se află în:

```text
CHECKPOINT.md
```

Regulă: `CHECKPOINT.md` și `README.md` se actualizează după fiecare PR merge-uit, diagnostic verde important, validare locală sau schimbare de etapă.
