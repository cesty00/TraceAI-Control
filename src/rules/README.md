# Rules Engine — Faza 3+

Acest folder conține regulile de business aplicate peste rezultatul Core Engine și contractul intern `TraceabilityCase` folosit de Report Engine.

## `case_type_detection.py`

Detectează tipul cazului:

```text
FINISHED_PRODUCT
RAW_MATERIAL
WMS_ONLY_PRODUCT
UNKNOWN
```

Input:

- `NormalizedDataSet`
- rezultatul `record_selection`
- cod articol/produs
- lot

Output:

- `case_type` detectat;
- dovezi sursă;
- observații dacă datele sunt insuficiente.

Utilizare:

```bash
python -m src.rules.case_type_detection "cale/catre/folder/date" --code DS099903883 --lot 105.26 --output case_type.json
```

## `run_rules_pipeline.py`

Rulează Core Engine și adaugă rezultatul Rules Engine disponibil în această etapă:

```text
core_pipeline -> case_type_detection
```

Output:

- rezultatul complet Core Engine;
- detectarea `case_type`;
- dovezi și observații.

Utilizare:

```bash
python -m src.rules.run_rules_pipeline "cale/catre/folder/date" --code DS099903883 --lot 105.26 --output rules_pipeline.json
```

## `traceability_case.py`

Definește obiectul intern `TraceabilityCase`, care alimentează raportul DOCX.

Obiectul conține:

- subiectul cazului: cod, lot, `case_type`;
- dovezi provenite din Rules Engine;
- observații;
- metadate tehnice minimale din Core Engine;
- structuri de tabele raportabile pentru:
  - producție;
  - livrări produs finit;
  - materii prime alimentare;
  - ambalaje;
  - materiale auxiliare / gaz;
  - recepții WMS;
  - consumuri PRD;
  - stoc la moment.

Tabelele sunt introduse ca structură de contract și au mesaje explicite când nu conțin rânduri.

## `run_traceability_case.py`

Rulează pipeline-ul Rules Engine și produce direct `TraceabilityCase`.

Utilizare:

```bash
python -m src.rules.run_traceability_case "cale/catre/folder/date" --code DS099903883 --lot 105.26 --output traceability_case.json
```

## Limită intenționată

Rules Engine, în această etapă, nu calculează încă trasabilitate amonte/aval detaliată și nu aplică bilanțuri detaliate. Report Engine generează DOCX din `TraceabilityCase`, nu direct din fișierele sursă.
