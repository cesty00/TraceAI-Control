# Core Engine — Faza 2

Acest folder conține primele module tehnice permise de `CHECKPOINT.md`.

## Surse oficiale

```text
trasabilitate_wms.csv
rapoarte productie.csv
nomenclator.xlsx
stoc la moment original.xlsx
```

## `source_inventory.py`

Inventariază sursele oficiale și produce un raport intern cu:

- fișiere găsite sau lipsă;
- tip fișier;
- coloane detectate pentru CSV;
- sheet-uri detectate pentru XLSX;
- coloane detectate pe fiecare sheet XLSX;
- număr de rânduri;
- probleme structurale timpurii.

Utilizare:

```bash
python -m src.core.source_inventory "cale/catre/folder/date" --output inventory_report.json
```

## `normalized_dataset.py`

Construiește `NormalizedDataSet`, output-ul de Faza 2 definit în roadmap.

Ce face:

- citește sursele oficiale;
- normalizează numele coloanelor în chei tehnice stabile;
- păstrează valorile originale;
- păstrează unitățile de măsură exact cum apar în surse;
- normalizează numeric doar cantitățile parsabile, separat de valoarea originală;
- expune indicii simple cod + lot pentru pașii următori.

Utilizare:

```bash
python -m src.core.normalized_dataset "cale/catre/folder/date" --output normalized_dataset.json
```

## `dataset_validation.py`

Validează structural `NormalizedDataSet` înainte de pașii următori.

Ce verifică:

- existența tabelelor normalizate;
- existența coloanelor;
- prezența probabilă a coloanelor cod + lot;
- probleme de parsare pe rânduri;
- erori globale de surse lipsă.

Utilizare:

```bash
python -m src.core.dataset_validation "cale/catre/folder/date" --output validation_report.json
```

## `record_selection.py`

Selectează rândurile din `NormalizedDataSet` pentru codul și lotul introduse de operator.

Ce face:

- caută potriviri exacte normalizate pentru cod + lot;
- păstrează contextul sursei, sheet-ului și rândului;
- returnează valorile originale, valorile normalizate și cantitățile parsate.

Utilizare:

```bash
python -m src.core.record_selection "cale/catre/folder/date" --code DS099903883 --lot 105.26 --output selected_records.json
```

## `run_pipeline.py`

Rulează într-un singur flux pașii Core Engine Faza 2:

```text
source_inventory -> normalized_dataset -> dataset_validation -> record_selection
```

Utilizare:

```bash
python -m src.core.run_pipeline "cale/catre/folder/date" --code DS099903883 --lot 105.26 --output core_pipeline.json
```

## Limită intenționată

Core Engine, în această etapă, nu calculează trasabilitate, nu clasifică tipuri de caz, nu construiește `TraceabilityCase` și nu generează DOCX.
