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
UI vizual profesional simplu: nu a început încă
Installer Windows: nu a început încă
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

Stratul UI/CLI minimal este doar orchestration-only:

```text
UI/CLI shell
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

Limitări intenționate ale runnerului demonstrativ:

```text
nu folosește UI
nu citește fișiere operaționale reale
nu citește sursele oficiale CSV/XLSX
nu schimbă Core Engine
nu schimbă Rules Engine
nu schimbă Report Engine
nu deduce trasabilitate amonte/aval
nu convertește automat unități de măsură
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

CLI-ul minimal:

```text
parsează argumente
construiește UiGenerationRequest
apelează generate_report_from_ui_request()
afișează mesajul rezultatului
returnează cod 0 la succes
returnează cod 1 la eroare
```

Limitări:

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

## Testare

Rulare test suite:

```bash
python -m pytest -q
```

Status curent:

```text
38 passed
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
```

## Limitări curente

Nu există încă:

```text
trasabilitate amonte/aval calculată
bilanțuri detaliate / reconciliere operațională completă
branding complet / logo / paginare avansată / cuprins automat
UI vizual profesional simplu
installer
```

## Checkpoint

Starea completă de lucru este păstrată în:

```text
CHECKPOINT.md
```

La reluarea proiectului, se continuă de la `CHECKPOINT.md`, nu de la presupuneri vechi.
