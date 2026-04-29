# Rules Engine — Faza 3

Acest folder conține regulile de business aplicate peste rezultatul Core Engine.

## `case_type_detection.py`

Primul pas Faza 3 detectează tipul cazului:

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

## Limită intenționată

Acest modul nu calculează trasabilitate, nu aplică bilanțuri, nu construiește `TraceabilityCase` și nu generează DOCX.
