# Report Engine — Faza 5

Acest folder conține generarea raportului DOCX.

## `docx_minimal.py`

Generează un DOCX narativ minimal din `TraceabilityCase`.

Input:

- `TraceabilityCase`

Output:

- raport `.docx`

Utilizare CLI:

```bash
python -m src.report.docx_minimal "cale/catre/folder/date" --code DS099903883 --lot 105.26 --output raport_trasabilitate.docx
```

## Reguli

- DOCX se generează din `TraceabilityCase`, nu direct din fișierele sursă.
- Secțiunile fără date sunt marcate explicit cu `FARA DATE IDENTIFICATE`.
- Generatorul minimal nu aplică încă layout final, template vizual sau stiluri profesionale.

## Limită intenționată

Acest modul nu conține UI, nu citește surse operaționale direct și nu modifică regulile Core / Rules Engine.
