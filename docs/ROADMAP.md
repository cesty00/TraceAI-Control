# Roadmap — TraceAI Control Modul Trasabilitate

Acest roadmap stabilește ordinea de dezvoltare.

Regulă de proiect:

```text
Nu construim UI înainte de motor.
Nu construim installer înainte de teste.
Nu generăm DOCX înainte de TraceabilityCase.
```

## Faza 0 — Documentație

Status: în curs

Livrabile:

```text
README.md
docs/SPECIFICATIE_FUNCTIONALA.md
docs/TESTE_VALIDATE.md
docs/RAPORT_DOCX_MODEL.md
docs/ARHITECTURA.md
docs/TRACEABILITY_CASE.md
docs/ROADMAP.md
```

Scop:

- stabilirea regulilor;
- stabilirea tipurilor de cazuri;
- stabilirea raportului DOCX;
- stabilirea obiectului intern;
- stabilirea testelor validate.

## Faza 1 — Schelet proiect

Livrabile:

```text
src/
  core/
  rules/
  report/
  ui/
tests/
samples/
```

Nu se implementează încă UI final.

## Faza 2 — Core Engine

Scop:

- citire WMS CSV;
- citire PRD CSV;
- citire nomenclator XLSX;
- citire stoc XLSX;
- normalizare coloane;
- normalizare cantități;
- păstrare UM;
- identificare cod + lot.

Output:

```text
NormalizedDataSet
```

## Faza 3 — Rules Engine

Scop:

- detectare case_type;
- clasificare componente;
- regulă gaz;
- bilanț produs finit;
- bilanț materie primă;
- WMS-only flow;
- AVAL MP;
- observații tehnice.

Output:

```text
TraceabilityCase
```

## Faza 4 — Teste automate pe cele 7 cazuri

Test matrix:

```text
DS099903883 / 105.26
DS099904006 / 091.26
DS099904181 / 092.26
DS099904127 / 098.26
DS099904015 / 105.26
DS099904130 / 90994-082
DS099903913 / 896
```

Fiecare test validează:

- `case_type`;
- bilanț;
- clasificare componente;
- gaz separat;
- AVAL MP;
- stoc;
- observații;
- concluzie.

## Faza 5 — Report Engine DOCX

Scop:

- generare raport DOCX din TraceabilityCase;
- structură adaptată pe case_type;
- tabele scurte;
- anexe pentru AVAL MP extins;
- concluzie și recomandare;
- semnături.

Regulă:

```text
Report Engine nu citește direct fișierele sursă.
```

## Faza 6 — UI simplu profesional

Scop:

- selectare fișiere sursă;
- introducere cod + lot;
- validare fișiere;
- generare raport;
- status vizibil;
- deschidere folder rapoarte.

Principii design:

```text
simplu
curat
profesional
fără taburi inutile
fără termeni tehnici inutili
```

## Faza 7 — Installer Windows

Scop:

- aplicație instalabilă;
- shortcut desktop;
- folder rapoarte;
- logging;
- update controlat.

## Faza 8 — Extensii viitoare

Posibile extensii:

- export PDF;
- export anexă Excel;
- istoric rapoarte;
- template DOCX configurabil;
- validare multi-lot;
- integrare directă ERP/WMS.

## Criteriu pentru a trece la cod

Se poate începe codul doar după ce sunt acceptate:

```text
SPECIFICATIE_FUNCTIONALA.md
TESTE_VALIDATE.md
RAPORT_DOCX_MODEL.md
ARHITECTURA.md
TRACEABILITY_CASE.md
ROADMAP.md
```
