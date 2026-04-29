# Core Engine — Faza 2

Acest folder conține primul modul tehnic permis de `CHECKPOINT.md`.

## Scop curent

Modulul `source_inventory.py` inventariază cele patru surse oficiale:

```text
trasabilitate_wms.csv
rapoarte productie.csv
nomenclator.xlsx
stoc la moment original.xlsx
```

Raportul intern conține:

- fișiere găsite sau lipsă;
- tip fișier;
- coloane detectate pentru CSV;
- sheet-uri detectate pentru XLSX;
- coloane detectate pe fiecare sheet XLSX;
- număr de rânduri;
- probleme structurale timpurii.

## Limită intenționată

Acest modul nu calculează trasabilitate, nu clasifică tipuri de caz, nu construiește `TraceabilityCase` și nu generează DOCX.

## Utilizare

```bash
python -m src.core.source_inventory "cale/catre/folder/date" --output inventory_report.json
```
