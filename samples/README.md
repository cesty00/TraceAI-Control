# Samples TraceAI Control

Acest folder conține exemple controlate pentru validarea manuală a generării raportului DOCX.

## Runner demonstrativ DOCX

Fișier:

```text
samples/demo_docx_runner.py
```

Scop:

```text
Generează un raport DOCX demonstrativ dintr-un dataset sintetic controlat.
```

Runnerul este util pentru verificare rapidă a fluxului:

```text
NormalizedDataSet sintetic
-> record_selection
-> case_type_detection
-> build_traceability_case
-> generate_minimal_docx_report
-> DOCX demonstrativ
```

## Rulare

Din rădăcina repo-ului:

```bash
python samples/demo_docx_runner.py --output samples/output/demo_traceability_report.docx
```

Output așteptat:

```text
samples/output/demo_traceability_report.docx
```

Folderul de output este creat automat dacă nu există.

## Ce conține raportul demonstrativ

Raportul generat include date sintetice pentru:

- produs verificat;
- producție;
- livrare produs finit;
- materie primă alimentară;
- ambalaj;
- stoc la moment;
- bilanț preliminar;
- secțiuni fără date marcate explicit.

## Limitări intenționate

Runnerul demonstrativ:

- nu folosește UI;
- nu citește fișiere operaționale reale;
- nu citește `trasabilitate_wms.csv`, `rapoarte productie.csv`, `nomenclator.xlsx` sau `stoc la moment original.xlsx`;
- nu schimbă Core Engine;
- nu schimbă Rules Engine;
- nu schimbă Report Engine;
- nu deduce trasabilitate amonte/aval;
- nu convertește automat unități de măsură.

## Validare automată

Runnerul este verificat prin:

```text
tests/test_demo_docx_runner.py
```

Rulare test suite:

```bash
python -m pytest -q
```
