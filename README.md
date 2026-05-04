# TraceAI Control — Modul Trasabilitate

TraceAI Control generează raport DOCX auditabil pentru trasabilitatea unui articol și lot.

## Status curent

```text
stadiu: Audit Checklist / UI / Packaging / Observability / Report Quality
etapă curentă: REPORT-QUALITY-01D-4_DONE
următoarea etapă recomandată: REPORT-QUALITY-01D-5 sau REPORT-QUALITY-01E
ultimul diagnostic validat: 140 passed, reference_comparison PASS, audit checklist DOCX header/footer verificat
checkpoint oficial: CHECKPOINT.md
```

Etapa activă este documentată în `CHECKPOINT.md`. La reluarea proiectului se citește întâi `CHECKPOINT.md`, nu această pagină.

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
registru documente fizice cu checkbox tipărit
header cu titlu raport, cod produs, lot și denumire produs
footer cu versiune aplicație, commit, canal build, dată generare și număr pagină
```

## UI

UI-ul vizual este Tkinter și orchestrează fluxul validat fără business logic.

Funcții validate:

```text
Verifică surse
Previzualizează audit checklist
Generează Diagnostic ZIP
Generează raport DOCX
```

Diagnostic ZIP tratează raportul DOCX ca atașament opțional: dacă fișierul există, îl include; dacă lipsește, afișează o notă clară și generează ZIP-ul fără DOCX.

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
140 passed
reference_comparison.md = PASS
real_audit_checklist_report.docx = generat cu header/footer dinamic verificat
```

## Checkpoint

Starea completă și următorul pas se află în:

```text
CHECKPOINT.md
```

Regulă: `CHECKPOINT.md` și `README.md` se actualizează după fiecare PR merge-uit, diagnostic verde important, validare locală sau schimbare de etapă.
