# Report Engine — Faza 5

Acest folder conține generarea raportului DOCX.

## `docx_minimal.py`

Generează un DOCX narativ din `TraceabilityCase`, mai apropiat de modelul definit în `docs/RAPORT_DOCX_MODEL.md`.

Input:

- `TraceabilityCase`

Output:

- raport `.docx`

Utilizare CLI:

```bash
python -m src.report.docx_minimal "cale/catre/folder/date" --code DS099903883 --lot 105.26 --output raport_trasabilitate.docx
```

## Structură generată

Raportul include:

- antet raport;
- rezumat executiv;
- identificarea cazului;
- surse utilizate;
- interpretarea tipului de caz;
- dovezi folosite;
- observații tehnice;
- secțiuni fără date;
- concluzie preliminară;
- recomandare operațională;
- documente de pregătit pentru audit;
- semnături.

## Reguli

- DOCX se generează din `TraceabilityCase`, nu direct din fișierele sursă.
- Secțiunile fără date sunt marcate explicit cu `FARA DATE IDENTIFICATE`.
- Raportul este narativ și auditabil, nu un dump de date brute.
- Generatorul nu conține UI și nu modifică regulile Core / Rules Engine.

## Limită intenționată

Raportul nu are încă șablon vizual profesional și nu conține încă tabele detaliate pentru toate cazurile. Acestea vor fi adăugate după extinderea `TraceabilityCase` cu date operaționale detaliate.
