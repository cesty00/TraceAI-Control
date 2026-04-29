# CHECKPOINT — TraceAI Control Modul Trasabilitate

Data checkpoint: 2026-04-29

## Status general

Proiectul este în repo-ul:

```text
cesty00/TraceAI-Control
```

Stadiul curent este:

```text
Faza 0 — Documentație și arhitectură inițială: finalizată
Faza 1 — Schelet repo: finalizată
Faza 2 — Core Engine: implementată tehnic v1
Faza 3 — Rules Engine: implementată tehnic v1
Faza 4 — TraceabilityCase: contract + report_tables + populare controlată + reguli clasificare + bilanț preliminar conservator implementate
Faza 5 — Report Engine DOCX: implementată tehnic v1 narativ + tabele Word reale + șablon profesional minimal + bilanț preliminar randat
Faza 5.1 — Flux E2E controlat DOCX: implementat tehnic
Faza 5.2 — Runner demonstrativ DOCX controlat: implementat tehnic + test automat dedicat + documentație de utilizare
Faza 5.3 — README principal sincronizat cu statusul curent și runnerul demonstrativ
Faza 6.0 — Contract minim UI -> engine: definit și documentat
Faza 6.1 — Funcție UI de orchestrare testabilă: implementată tehnic + documentată
Faza 6 — UI profesional simplu: NU este implementat vizual încă
```

## Decizie principală

Nu dezvoltăm aplicația direct în UI vizual complex.

Ordinea proiectului este:

```text
Documentație
Core Engine
Rules Engine
TraceabilityCase
Teste automate
Report Engine DOCX
Flux E2E controlat
Runner demonstrativ DOCX
Documentație runner demonstrativ
README principal sincronizat
Contract UI -> engine
Funcție UI de orchestrare testabilă
Documentație funcție UI de orchestrare
UI/CLI shell minimal
UI profesional simplu
Installer Windows
```

## Scop aplicație

TraceAI Control — Modul Trasabilitate generează un raport DOCX auditabil pentru un articol și lot.

Input utilizator:

```text
Cod articol
Lot
```

Output principal:

```text
Raport DOCX de trasabilitate
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

Nu se folosesc:

```text
WME / fișă magazie
patch-uri vechi
fișiere auxiliare fără rol în fluxul curent
PP-03
OperatorView
fișiere debug
```

Regulă documente:

```text
Document intrare = din WMS
Numar comanda = din WMS
Document comanda = din WMS
```

## Tipuri de cazuri definite

Aplicația detectează automat:

```text
FINISHED_PRODUCT
RAW_MATERIAL
WMS_ONLY_PRODUCT
UNKNOWN
```

Detectarea acestor tipuri aparține Rules Engine.

## Reguli critice validate

1. Gazul ALISOL este auxiliar / consumabil tehnologic.
2. Gazul nu intră niciodată la materii prime alimentare.
3. Unitățile de măsură nu se convertesc automat.
4. Dacă o secțiune nu are date, raportul trebuie să spună explicit acest lucru.
5. Raportul DOCX trebuie să fie narativ și auditabil, nu un Excel copiat în Word.
6. DOCX-ul se generează din TraceabilityCase, nu direct din fișiere.
7. UI-ul nu conține logică de business.
8. Bilanțul preliminar este conservator și nu deduce fluxuri lipsă.
9. Fluxul E2E controlat folosește date sintetice de test, nu UI și nu fișiere operaționale reale.
10. Runnerul demonstrativ folosește dataset sintetic controlat și nu schimbă regulile de business.
11. Documentația runnerului explică explicit că demo-ul nu citește surse operaționale reale.
12. README.md principal reflectă statusul tehnic curent și nu mai conține status vechi de pre-cod.
13. Contractul UI -> engine limitează UI-ul la colectare input, apel engine și afișare succes/eroare.
14. Funcția UI de orchestrare nu citește direct sursele și nu conține logică de business.
15. Documentația UI explică explicit `UiGenerationRequest`, `UiGenerationResult` și `generate_report_from_ui_request()`.

## Teste virtuale acceptate

| Test | Cod / Lot | Tip caz | Verdict |
|---|---|---|---|
| 1 | DS099903883 / 105.26 | FINISHED_PRODUCT | Acceptat |
| 2 | DS099904006 / 091.26 | FINISHED_PRODUCT | Acceptat |
| 3 | DS099904181 / 092.26 | FINISHED_PRODUCT | Acceptat |
| 4 | DS099904127 / 098.26 | FINISHED_PRODUCT | Acceptat |
| 5 | DS099904015 / 105.26 | FINISHED_PRODUCT | Acceptat |
| 6 | DS099904130 / 90994-082 | RAW_MATERIAL | Acceptat |
| 7 | DS099903913 / 896 | WMS_ONLY_PRODUCT | Acceptat |

## Structura repo la checkpoint

```text
TraceAI-Control/
  README.md
  CHECKPOINT.md
  docs/
    UI_ENGINE_CONTRACT.md
  src/
    core/
    rules/
    report/
    ui/
      README.md
      __init__.py
      orchestrator.py
  tests/
    README.md
    test_source_inventory.py
    test_normalized_dataset.py
    test_dataset_validation.py
    test_record_selection.py
    test_run_pipeline.py
    test_case_type_detection.py
    test_run_rules_pipeline.py
    test_traceability_case.py
    test_run_traceability_case.py
    test_docx_minimal.py
    test_e2e_docx_controlled_flow.py
    test_demo_docx_runner.py
    test_ui_orchestrator.py
  samples/
    README.md
    demo_docx_runner.py
```

## Core Engine v1 implementat

```text
source_inventory -> normalized_dataset -> dataset_validation -> record_selection -> run_pipeline
```

## Rules Engine v1 implementat

```text
case_type_detection -> run_rules_pipeline
```

Tipuri detectate:

```text
FINISHED_PRODUCT
RAW_MATERIAL
WMS_ONLY_PRODUCT
UNKNOWN
```

## TraceabilityCase implementat

```text
traceability_case -> run_traceability_case
```

Obiectul intern conține în prezent:

```text
subject: code, lot, case_type
evidence: sursă, sheet, rând, mesaj
observations: observații Rules Engine
sections: metadate tehnice minimale Core Engine
report_tables: tabele raportabile pentru DOCX
preliminary_balance: bilanț preliminar conservator
```

Tabele definite în `TraceabilityCase.report_tables`:

```text
production
finished_goods_deliveries
raw_materials
packaging
auxiliaries_gas
wms_receipts
prd_consumptions
stock
```

Populare controlată implementată:

```text
rânduri production selectate -> report_tables.production
rânduri wms cu indicii explicite de livrare / document comandă / client -> report_tables.finished_goods_deliveries
rânduri wms fără indicii explicite de livrare -> report_tables.wms_receipts
rânduri stock selectate -> report_tables.stock
rânduri care conțin ALISOL -> report_tables.auxiliaries_gas
rânduri cu indicii explicite de materie primă -> report_tables.raw_materials
rânduri cu indicii explicite de ambalaj -> report_tables.packaging
```

Reguli de clasificare implementate:

```text
ALISOL este tratat ca auxiliar / gaz tehnologic, nu ca materie primă alimentară.
Materiile prime și ambalajele sunt clasificate doar pe indicii explicite, fără deducții de trasabilitate.
Livrările produs finit din WMS sunt clasificate doar pe indicii explicite de livrare / document comandă / client.
```

Bilanț preliminar conservator implementat:

```text
TraceabilityBalanceLine
TraceabilityPreliminaryBalance
TraceabilityCase.preliminary_balance
build_preliminary_balance()
```

Reguli bilanț preliminar:

```text
calculează doar din TraceabilityCase.report_tables
folosește doar valori numerice clare
grupează totalurile pe UM
nu convertește unități de măsură
ignoră și raportează rândurile cu valori/UM neclare
respinge valori cu separatori amestecați
nu deduce trasabilitate amonte/aval
nu deduce fluxuri lipsă
```

## Report Engine DOCX narativ implementat

Faza 5 este implementată tehnic v1 narativ cu tabele Word reale, șablon profesional minimal și bilanț preliminar randat:

```text
TraceabilityCase -> docx_minimal
```

DOCX-ul include în prezent:

```text
antet raport
secțiune metadate raport
rezumat executiv
identificarea cazului
surse utilizate
interpretarea tipului de caz
dovezi folosite
observații tehnice
tabele operaționale din TraceabilityCase ca tabele WordprocessingML reale
bilanț preliminar din TraceabilityCase.preliminary_balance
secțiuni fără date
concluzie preliminară
recomandare operațională
documente de pregătit pentru audit
semnături
```

Secțiunea DOCX de bilanț preliminar include:

```text
mesaje generale ale bilanțului
tabel Word pentru liniile de bilanț
coloane: Tabel, Coloană, UM, Total, Rânduri sursă, Rânduri ignorate, Mesaj
mesaj explicit când nu există linii de bilanț
```

Reguli respectate:

```text
DOCX se generează din TraceabilityCase, nu direct din fișierele sursă.
Report Engine randează report_tables fără să citească surse operaționale.
Report Engine afișează preliminary_balance fără să recalculeze bilanțul.
Lipsurile sunt marcate explicit cu FARA DATE IDENTIFICATE sau cu mesajul tabelului.
Generatorul nu conține UI și nu schimbă regulile Core / Rules Engine.
```

## Flux E2E controlat implementat

Fluxul E2E controlat este implementat în:

```text
tests/test_e2e_docx_controlled_flow.py
tests/README.md
```

Flux validat:

```text
NormalizedDataSet sintetic
-> record_selection
-> case_type_detection
-> build_traceability_case
-> verificare report_tables
-> verificare preliminary_balance
-> generate_minimal_docx_report
-> verificare word/document.xml
```

Scop:

```text
validarea integrării tehnice dintre Rules Engine, TraceabilityCase și Report Engine,
fără UI și fără citirea directă a surselor operaționale reale în Report Engine.
```

## Runner demonstrativ DOCX implementat, testat și documentat

Runnerul demonstrativ este implementat în:

```text
samples/demo_docx_runner.py
```

Documentație de utilizare:

```text
samples/README.md
```

Test automat dedicat:

```text
tests/test_demo_docx_runner.py
```

Flux runner:

```text
NormalizedDataSet sintetic controlat
-> record_selection
-> case_type_detection
-> build_traceability_case
-> generate_minimal_docx_report
-> output DOCX demonstrativ
```

Rulare:

```bash
python samples/demo_docx_runner.py --output samples/output/demo_traceability_report.docx
```

Reguli runner:

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

## README principal sincronizat

README.md principal conține acum:

```text
statusul modulelor integrate
arhitectura curentă
sursele oficiale
regulile importante
structura TraceabilityCase
ce include raportul DOCX
runnerul demonstrativ DOCX
comanda de rulare demo
comanda de testare
limitările curente
trimitere către CHECKPOINT.md
```

Comenzi documentate în README.md:

```bash
python samples/demo_docx_runner.py --output samples/output/demo_traceability_report.docx
python -m pytest -q
```

## Contract minim UI -> engine definit

Contractul este documentat în:

```text
docs/UI_ENGINE_CONTRACT.md
src/ui/README.md
```

Input UI minim:

```text
source_directory
code
lot
output_docx_path
```

Apel engine permis:

```text
run_traceability_case(source_directory, code, lot)
-> generate_minimal_docx_report(traceability_case, output_docx_path)
```

UI-ul are voie doar să:

```text
colecteze inputul minim
apeleze engine-ul existent
afișeze progres simplu
afișeze succes/eroare
```

UI-ul nu are voie să:

```text
citească direct CSV/XLSX pentru logică de business
clasifice tipuri de caz
calculeze bilanțuri
modifice TraceabilityCase
recalculeze tabele raportabile
genereze DOCX direct din surse operaționale
convertească unități de măsură
deducă trasabilitate amonte/aval
```

## Funcție UI de orchestrare testabilă implementată și documentată

Implementare:

```text
src/ui/orchestrator.py
src/ui/__init__.py
```

Documentație:

```text
src/ui/README.md
```

Test dedicat:

```text
tests/test_ui_orchestrator.py
```

Funcție principală:

```text
generate_report_from_ui_request()
```

Input controlat:

```text
UiGenerationRequest:
- source_directory
- code
- lot
- output_docx_path
```

Output controlat:

```text
UiGenerationResult:
- success
- output_path
- message
- error
```

Documentația UI explică:

```text
rolul orchestration-only al UI-ului
inputul și outputul funcției
exemplu de utilizare Python
comportamentul pentru câmpuri lipsă
comportamentul pentru eroare engine
interdicția logicii de business în UI
```

Testele verifică:

```text
orchestrare corectă către engine
validare câmpuri lipsă
fără apel engine când inputul e invalid
capturare eroare engine
raportare câmpuri obligatorii lipsă
```

Reguli funcție UI:

```text
nu există UI vizual
nu citește direct CSV/XLSX
nu conține logică de business
nu clasifică tipuri de caz
nu calculează bilanțuri
nu modifică TraceabilityCase
nu generează DOCX direct din surse
```

## Limită curentă

TraceabilityCase are structurile de tabele, bilanț preliminar conservator, raport DOCX cu tabele Word reale, stiluri, antet, subsol, metadate, bilanț preliminar randat, runner demonstrativ controlat, test automat dedicat pentru runner, documentație de utilizare pentru demo, README principal sincronizat, contract UI -> engine definit și funcție UI de orchestrare testabilă documentată.

Nu există încă:

```text
trasabilitate amonte/aval calculată
bilanțuri detaliate / reconciliere operațională completă
branding complet / logo / paginare avansată / cuprins automat
UI/CLI shell minimal
UI vizual
installer
```

## Testare curentă

Testele unitare și E2E controlate acoperă modulele Core, Rules, TraceabilityCase, bilanț preliminar conservator, Report Engine DOCX, fluxul controlat TraceabilityCase -> DOCX, runnerul demonstrativ și funcția UI de orchestrare:

```text
python -m pytest -q
37 passed
```

Runner demonstrativ integrat, testat și documentat:

```text
samples/demo_docx_runner.py
samples/README.md
tests/test_demo_docx_runner.py
README.md
```

Contract UI -> engine integrat:

```text
docs/UI_ENGINE_CONTRACT.md
src/ui/README.md
```

Funcție UI de orchestrare integrată și documentată:

```text
src/ui/orchestrator.py
src/ui/__init__.py
src/ui/README.md
tests/test_ui_orchestrator.py
```

## Următorul pas la reluare

La reluarea proiectului, NU se începe cu UI vizual complex.

Următorul pas corect este:

```text
pregătirea unui CLI/UI shell minimal peste orchestrator
```

Primul cod permis:

```text
src/ui/
tests/
README.md
```

Primul obiectiv tehnic posibil:

```text
adăugarea unui shell minimal care:
- primește source_directory, code, lot, output_docx_path
- construiește UiGenerationRequest
- apelează generate_report_from_ui_request()
- afișează mesajul rezultatului
- nu citește direct surse operaționale
- nu conține logică de business
```

Regulă importantă:

```text
Nu se începe cu UI vizual complex.
Shell-ul UI/CLI minimal nu citește direct surse operaționale.
Shell-ul UI/CLI minimal nu conține logică de business.
Funcția UI de orchestrare rămâne singurul punct de legătură UI -> engine.
DOCX rămâne generat din TraceabilityCase, nu direct din fișierele sursă.
Bilanțul preliminar rămâne conservator și nu convertește unități de măsură automat.
```

## Fraza de reluare recomandată

Când reluăm proiectul, mesajul corect este:

```text
Continuăm de la CHECKPOINT.md cu un CLI/UI shell minimal peste orchestrator, fără UI vizual complex.
```
