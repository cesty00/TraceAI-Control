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

## Limită intenționată

Core Engine, în această etapă, nu calculează trasabilitate, nu clasifică tipuri de caz, nu construiește `TraceabilityCase` și nu generează DOCX.
