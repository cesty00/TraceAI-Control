# CHECKPOINT — TraceAI Control Modul Trasabilitate

Data checkpoint: 2026-04-29

## Status general

Proiectul a fost repornit curat în repo-ul:

```text
cesty00/TraceAI-Control
```

Repo-ul păstrează doar direcția curentă pentru modulul de trasabilitate și raportul DOCX auditabil.

Stadiul curent este:

```text
Faza 0 — Documentație și arhitectură inițială: finalizată
Faza 1 — Schelet repo: finalizată
Faza 2 — Core Engine: implementată tehnic v1
Faza 3 — Rules Engine: implementată tehnic v1
Faza 4 — TraceabilityCase: contract + report_tables + populare inițială + reguli clasificare implementate
Faza 5 — Report Engine DOCX: implementată tehnic v1 narativ + randare tabele
Faza 6 — UI profesional simplu: NU a început încă
```

## Decizie principală

Nu dezvoltăm aplicația direct în UI.

Ordinea proiectului este:

```text
Documentație
Core Engine
Rules Engine
TraceabilityCase
Teste automate
Report Engine DOCX
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
    SPECIFICATIE_FUNCTIONALA.md
    TESTE_VALIDATE.md
    RAPORT_DOCX_MODEL.md
    ARHITECTURA.md
    TRACEABILITY_CASE.md
    ROADMAP.md
    STRUCTURA_REPO.md
  src/
    core/
      source_inventory.py
      normalized_dataset.py
      dataset_validation.py
      record_selection.py
      run_pipeline.py
    rules/
      case_type_detection.py
      run_rules_pipeline.py
      traceability_case.py
      run_traceability_case.py
    report/
      docx_minimal.py
    ui/
  tests/
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
  samples/
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
rânduri wms selectate -> report_tables.wms_receipts
rânduri stock selectate -> report_tables.stock
rânduri care conțin ALISOL -> report_tables.auxiliaries_gas
rânduri cu indicii explicite de materie primă -> report_tables.raw_materials
rânduri cu indicii explicite de ambalaj -> report_tables.packaging
```

Reguli de clasificare implementate:

```text
ALISOL este tratat ca auxiliar / gaz tehnologic, nu ca materie primă alimentară.
Materiile prime și ambalajele sunt clasificate doar pe indicii explicite, fără deducții de trasabilitate.
```

Tabelele rămase nepopulate păstrează mesajele explicite când nu conțin rânduri.

## Report Engine DOCX narativ implementat

Faza 5 este implementată tehnic v1 narativ cu randare de tabele:

```text
TraceabilityCase -> docx_minimal
```

DOCX-ul include în prezent:

```text
antet raport
rezumat executiv
identificarea cazului
surse utilizate
interpretarea tipului de caz
dovezi folosite
observații tehnice
tabele operaționale din TraceabilityCase
secțiuni fără date
concluzie preliminară
recomandare operațională
documente de pregătit pentru audit
semnături
```

Reguli respectate:

```text
DOCX se generează din TraceabilityCase, nu direct din fișierele sursă.
Report Engine randează report_tables fără să citească surse operaționale.
Lipsurile sunt marcate explicit cu FARA DATE IDENTIFICATE sau cu mesajul tabelului.
Generatorul nu conține UI și nu schimbă regulile Core / Rules Engine.
```

## Limită curentă

TraceabilityCase are structurile de tabele, DOCX-ul le afișează, primele tabele sunt populate controlat din rândurile selectate de Core, iar ALISOL / materiile prime / ambalajele au reguli explicite de clasificare.

Nu există încă:

```text
trasabilitate amonte/aval calculată
bilanțuri detaliate
populare livrări produs finit
șablon vizual profesional
UI
installer
```

## Testare curentă

Testele unitare existente acoperă modulele Core, Rules, TraceabilityCase și Report Engine DOCX cu tabele:

```text
python -m pytest -q
29 passed
```

## Următorul pas la reluare

La reluarea proiectului, NU se începe cu UI.

Următorul pas corect este:

```text
popularea livrărilor produs finit din rânduri WMS relevante
```

Primul cod permis:

```text
src/rules/traceability_case.py
```

Primul obiectiv tehnic următor:

```text
adăugarea unei reguli prudente pentru:
- rânduri WMS cu indicii explicite de livrare / document comanda -> report_tables.finished_goods_deliveries
- păstrarea recepțiilor WMS în report_tables.wms_receipts când nu există indicii de livrare
```

Regulă importantă:

```text
TraceabilityCase poate fi extins din rezultatul Core/Rules, dar DOCX rămâne generat din TraceabilityCase, nu direct din fișierele sursă.
```

## Fraza de reluare recomandată

Când reluăm proiectul, mesajul corect este:

```text
Continuăm de la CHECKPOINT.md cu popularea livrărilor produs finit din rânduri WMS relevante.
```
