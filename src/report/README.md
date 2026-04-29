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
- secțiune de metadate raport;
- rezumat executiv;
- identificarea cazului;
- surse utilizate;
- interpretarea tipului de caz;
- dovezi folosite;
- observații tehnice;
- tabele operaționale din `TraceabilityCase`;
- secțiuni fără date;
- concluzie preliminară;
- recomandare operațională;
- documente de pregătit pentru audit;
- semnături.

## Șablon DOCX profesional minimal

Generatorul include acum piese DOCX dedicate pentru:

- `word/styles.xml`;
- `word/header1.xml`;
- `word/footer1.xml`;
- relații Word pentru stiluri, antet și subsol;
- referințe de antet/subsol în `sectPr`;
- stil de tabel `TraceAITable`.

## Tabele operaționale

Generatorul randează tabelele existente în `TraceabilityCase.report_tables`:

- producție;
- livrări produs finit;
- materii prime alimentare;
- ambalaje;
- materiale auxiliare / gaz;
- recepții WMS;
- consumuri PRD;
- stoc la moment.

Pentru fiecare tabel, raportul afișează ca tabel Word real:

- titlul tabelului;
- header cu coloanele definite în `TraceabilityCase`;
- rândurile disponibile;
- contextul sursă pentru fiecare rând;
- mesajul explicit de lipsă date când tabelul este gol.

## Reguli

- DOCX se generează din `TraceabilityCase`, nu direct din fișierele sursă.
- Secțiunile fără date sunt marcate explicit cu `FARA DATE IDENTIFICATE` sau cu mesajul dedicat tabelului.
- Raportul este narativ și auditabil, nu un dump de date brute.
- Generatorul nu conține UI și nu modifică regulile Core / Rules Engine.

## Limită intenționată

Raportul are șablon profesional minimal cu stiluri, antet, subsol, metadate și tabele Word reale. Nu include încă branding complet, logo, paginare avansată, cuprins automat sau anexare de documente suport.
