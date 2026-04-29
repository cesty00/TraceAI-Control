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
Faza 4 — TraceabilityCase: schelet + runner implementate
Faza 5 — Report Engine DOCX: NU a început încă
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

TraceAI Control — Modul Trasabilitate va genera un raport DOCX auditabil pentru un articol și lot.

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

Aplicația va folosi doar:

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

Aplicația trebuie să detecteze automat:

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
  samples/
```

## Documente existente

- `README.md` — prezentare proiect.
- `docs/SPECIFICATIE_FUNCTIONALA.md` — specificație funcțională.
- `docs/TESTE_VALIDATE.md` — cele 7 teste virtuale acceptate.
- `docs/RAPORT_DOCX_MODEL.md` — structura și stilul raportului DOCX.
- `docs/ARHITECTURA.md` — arhitectura pe componente.
- `docs/TRACEABILITY_CASE.md` — contractul obiectului intern TraceabilityCase.
- `docs/ROADMAP.md` — ordinea de dezvoltare.
- `docs/STRUCTURA_REPO.md` — structura repo-ului.
- `src/core/README.md` — utilizarea modulelor Core Engine.
- `src/rules/README.md` — utilizarea modulelor Rules Engine și TraceabilityCase.

## Core Engine v1 implementat

Faza 2 a fost implementată tehnic în pași mici:

```text
source_inventory -> normalized_dataset -> dataset_validation -> record_selection -> run_pipeline
```

Livrabile Core:

- `source_inventory.py` inventariază sursele oficiale;
- `normalized_dataset.py` construiește `NormalizedDataSet`;
- `dataset_validation.py` validează structural datasetul;
- `record_selection.py` selectează rândurile pentru cod + lot;
- `run_pipeline.py` orchestrează fluxul Core Faza 2.

## Rules Engine v1 implementat

Faza 3 a fost implementată tehnic în pași mici:

```text
case_type_detection -> run_rules_pipeline
```

Livrabile Rules:

- `case_type_detection.py` detectează `case_type` din rezultatul Core Engine;
- `run_rules_pipeline.py` rulează Core Pipeline și adaugă detectarea `case_type`.

Tipuri detectate:

```text
FINISHED_PRODUCT
RAW_MATERIAL
WMS_ONLY_PRODUCT
UNKNOWN
```

## TraceabilityCase v1 implementat

Faza 4 a început și are schelet funcțional:

```text
traceability_case -> run_traceability_case
```

Livrabile TraceabilityCase:

- `traceability_case.py` definește contractul intern minimal;
- `run_traceability_case.py` produce `TraceabilityCase` minimal din folderul de surse + cod + lot.

Obiectul intern conține în prezent:

```text
subject: code, lot, case_type
evidence: sursă, sheet, rând, mesaj
observations: observații Rules Engine
sections: metadate tehnice minimale Core Engine
```

## Limită curentă

Aplicația nu generează încă DOCX.

TraceabilityCase este încă minimal și nu conține încă secțiuni narative finale pentru raport.

Nu există încă:

```text
Report Engine DOCX
șablon DOCX generat automat
UI
installer
```

## Testare curentă

Testele unitare existente acoperă modulele Core, Rules și TraceabilityCase v1:

```text
python -m pytest -q
21 passed
```

## Următorul pas la reluare

La reluarea proiectului, NU se începe cu UI.

Următorul pas corect este:

```text
Faza 5 — Report Engine DOCX minimal
```

Primul cod permis:

```text
src/report/
```

Primul obiectiv tehnic Faza 5:

```text
generarea unui DOCX narativ minimal din TraceabilityCase, cu secțiuni explicite:
- subiectul raportului
- tipul cazului
- dovezi folosite
- observații
- secțiuni fără date marcate explicit
```

Regulă importantă:

```text
DOCX se generează din TraceabilityCase, nu direct din fișierele sursă.
```

## Fraza de reluare recomandată

Când reluăm proiectul, mesajul corect este:

```text
Continuăm de la CHECKPOINT.md cu Faza 5 — Report Engine DOCX minimal din TraceabilityCase.
```
