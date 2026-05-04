# TraceAI Control — Modul Trasabilitate

TraceAI Control generează raport DOCX auditabil pentru trasabilitatea unui articol și lot.

## Status curent

```text
main: 40d0c09a65e5e114781be1a9b996a9191cb9e834
stadiu: Audit Checklist / UI / Packaging / Observability
ultimul diagnostic validat: 126 passed, reference_comparison PASS
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
```

## UI

UI-ul vizual este Tkinter și orchestrează fluxul validat fără business logic.

Funcții validate:

```text
Verifică surse
Previzualizează audit checklist
Generează raport DOCX
```

Următorul pas activ este urmărit în `CHECKPOINT.md`.

## Diagnostic local

Generatorul local de diagnostic ZIP este disponibil:

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

Rulare locală:

```bash
python -m pytest -q
```

Ultimul diagnostic confirmat în checkpoint:

```text
126 passed
reference_comparison.md = PASS
real_audit_checklist_ui.json = valid
```

## Checkpoint

Starea completă și următorul pas se află în:

```text
CHECKPOINT.md
```

Regulă: `CHECKPOINT.md` și `README.md` se actualizează după fiecare PR merge-uit, diagnostic verde important sau schimbare de etapă.
