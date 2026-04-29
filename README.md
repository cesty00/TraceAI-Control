# TraceAI Control — Modul Trasabilitate

TraceAI Control — Modul Trasabilitate generează un raport DOCX auditabil pentru trasabilitatea unui articol și lot.

Utilizatorul introduce:

```text
Cod articol
Lot
```

Livrabilul principal este:

```text
Raport DOCX de trasabilitate
```

Raportul este narativ, auditabil și construit din `TraceabilityCase`, nu prin citirea directă a fișierelor în Report Engine.

## Status curent

Stadiul tehnic curent:

```text
Core Engine v1: integrat
Rules Engine v1: integrat
TraceabilityCase + report_tables: integrat
Bilanț preliminar conservator: integrat
Report Engine DOCX cu tabele Word reale: integrat
Șablon DOCX profesional minimal: integrat
Randare bilanț preliminar în DOCX: integrată
Flux E2E controlat DOCX: integrat
Runner demonstrativ DOCX controlat: integrat, testat și documentat
Contract UI -> engine: integrat
Funcție UI de orchestrare: integrată și testată
CLI/UI shell minimal peste orchestrator: integrat și testat
UI vizual minimal peste orchestrator: integrat și testat
Pregătire installer Windows: script PyInstaller + documentație integrate
Verificare build Windows: script PowerShell integrat
Installer Windows complet: nu este finalizat încă
```

## Surse oficiale

Aplicația folosește doar:

```text
trasabilitate_wms.csv
rapoarte productie.csv
nomenclator.xlsx
stoc la moment original.xlsx
```

## Surse excluse

Aplicația nu folosește:

```text
WME / fișă magazie
PP-03
OperatorView
patch-uri vechi
fișiere debug
```

## Tipuri de cazuri suportate

Rules Engine detectează automat tipul cazului:

```text
FINISHED_PRODUCT
RAW_MATERIAL
WMS_ONLY_PRODUCT
UNKNOWN
```

## Reguli importante

- WMS este sursa pentru mișcări, documente, parteneri, loturi, cantități și documente comerciale.
- PRD este sursa pentru producție, comenzi și consumuri.
- Document intrare, Numar comanda și Document comanda se iau din WMS.
- GAZ ALIMENTAR ALISOL este material auxiliar / consumabil tehnologic.
- Gazul nu este materie primă alimentară.
- Unitățile de măsură se păstrează așa cum apar în surse.
- Nu se fac conversii automate de unități de măsură.
- Dacă nu există date într-o secțiune, raportul spune explicit acest lucru.
- UI-ul nu conține logică de business.

## Arhitectură curentă

Fluxul tehnic curent este:

```text
Core Engine
-> Rules Engine
-> TraceabilityCase
-> Report Engine DOCX
```

Stratul UI/CLI/visual este doar orchestration-only:

```text
UI/CLI/visual shell
-> UiGenerationRequest
-> generate_report_from_ui_request()
-> engine existent
```

Module principale:

```text
src/core/
src/rules/
src/report/
src/ui/
samples/
tests/
installer/windows/
```

`TraceabilityCase` conține:

```text
subject
evidence
observations
sections
report_tables
preliminary_balance
```

## Raport DOCX

Raportul DOCX include:

```text
antet raport
secțiune metadate raport
rezumat executiv
identificarea cazului
surse utilizate
interpretarea tipului de caz
dovezi folosite
observații tehnice
tabele operaționale din TraceabilityCase
bilanț preliminar
secțiuni fără date
concluzie preliminară
recomandare operațională
documente de pregătit pentru audit
semnături
```

DOCX-ul include tabele Word reale, stiluri, antet, subsol și o secțiune de bilanț preliminar.

## Runner demonstrativ DOCX

Runnerul demonstrativ generează un raport DOCX dintr-un dataset sintetic controlat.

Fișier:

```text
samples/demo_docx_runner.py
```

Rulare:

```bash
python samples/demo_docx_runner.py --output samples/output/demo_traceability_report.docx
```

Output așteptat:

```text
samples/output/demo_traceability_report.docx
```

Documentația runnerului este în:

```text
samples/README.md
```

## CLI/UI shell minimal

CLI-ul minimal apelează funcția UI de orchestrare și nu conține logică de business.

Fișier:

```text
src/ui/cli.py
```

Rulare:

```bash
python -m src.ui.cli "cale/catre/date" --code DS099903883 --lot 105.26 --output raport_trasabilitate.docx
```

## UI vizual minimal

UI-ul vizual minimal este implementat cu Tkinter și apelează același orchestrator.

Fișier:

```text
src/ui/visual.py
```

Rulare:

```bash
python -m src.ui.visual
```

UI-ul vizual minimal include:

```text
câmp folder surse oficiale
câmp cod articol
câmp lot
câmp raport DOCX output
buton generare raport DOCX
mesaj succes / eroare
```

Limitări UI/CLI/visual:

```text
nu citește direct surse operaționale
nu clasifică tipuri de caz
nu calculează bilanțuri
nu generează DOCX direct din CSV/XLSX
nu conține logică de business
```

Documentație UI:

```text
docs/UI_ENGINE_CONTRACT.md
src/ui/README.md
```

## Pregătire installer Windows

Pregătirea pentru executabil Windows este în:

```text
installer/windows/
```

Fișiere:

```text
installer/windows/README.md
installer/windows/build_windows.ps1
installer/windows/verify_windows_build.ps1
```

Build local pe Windows, din rădăcina repo-ului:

```powershell
powershell -ExecutionPolicy Bypass -File .\installer\windows\build_windows.ps1
```

Verificare build după generarea executabilului:

```powershell
powershell -ExecutionPolicy Bypass -File .\installer\windows\verify_windows_build.ps1
```

Output așteptat:

```text
dist/TraceAI-Control/TraceAI-Control.exe
```

Scriptul de build rulează testele înainte de build, cu excepția cazului în care este folosit parametrul `-SkipTests`.

Scriptul de verificare confirmă existența executabilului și afișează pașii manuali de smoke test. Nu pornește automat UI-ul și nu apelează engine-ul.

Limitări curente installer:

```text
nu există încă MSI/NSIS/Inno Setup
nu există semnare executabil
nu există icon final
nu există pipeline CI Windows
```

## Testare

Rulare test suite:

```bash
python -m pytest -q
```

Status curent:

```text
39 passed
```

Testele acoperă:

```text
Core Engine
Rules Engine
TraceabilityCase
bilanț preliminar conservator
Report Engine DOCX
flux E2E controlat
runner demonstrativ DOCX
funcție UI de orchestrare
CLI/UI shell minimal
UI vizual minimal
```

## Limitări curente

Nu există încă:

```text
trasabilitate amonte/aval calculată
bilanțuri detaliate / reconciliere operațională completă
branding complet / logo / paginare avansată / cuprins automat
installer Windows complet
```

## Checkpoint

Starea completă de lucru este păstrată în:

```text
CHECKPOINT.md
```

La reluarea proiectului, se continuă de la `CHECKPOINT.md`, nu de la presupuneri vechi.
