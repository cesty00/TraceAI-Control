# CHECKPOINT — TraceAI Control Modul Trasabilitate

Data checkpoint: 2026-04-28

## Status general

Proiectul a fost repornit curat în repo-ul:

```text
cesty00/TraceAI-Control
```

Repo-ul nu mai conține variante vechi, patch-uri FAST, PP-03 sau OperatorView.

Stadiul curent este:

```text
Faza 0 — Documentație și arhitectură inițială: finalizată
Faza 1 — Schelet repo: finalizată
Faza 2 — Core Engine: NU a început încă
```

## Decizie principală

Nu dezvoltăm aplicația direct în UI.

Ordinea proiectului este:

```text
Documentație
Core Engine
Rules Engine
TraceabilityCase
Teste automate
Report Engine DOCX
UI profesional simplu
Installer Windows
```

## Scop aplicație

TraceAI Control — Modul Trasabilitate va genera un raport DOCX auditabil pentru un articol și lot.

Input utilizator:

```text
Cod articol
Lot
```

Output principal:

```text
Raport DOCX de trasabilitate
```

## Surse oficiale

Aplicația va folosi doar:

```text
trasabilitate_wms.csv
rapoarte productie.csv
nomenclator.xlsx
stoc la moment original.xlsx
```

## Surse excluse

Nu se folosesc:

```text
WME / fișă magazie
PP-03
OperatorView
patch-uri vechi
fișiere debug
```

Regulă documente:

```text
Document intrare = din WMS
Numar comanda = din WMS
Document comanda = din WMS
```

## Tipuri de cazuri definite

Aplicația trebuie să detecteze automat:

```text
FINISHED_PRODUCT
RAW_MATERIAL
WMS_ONLY_PRODUCT
UNKNOWN
```

## Reguli critice validate

1. Gazul ALISOL este auxiliar / consumabil tehnologic.
2. Gazul nu intră niciodată la materii prime alimentare.
3. Unitățile de măsură nu se convertesc automat.
4. Dacă o secțiune nu are date, raportul trebuie să spună explicit acest lucru.
5. Raportul DOCX trebuie să fie narativ și auditabil, nu un Excel copiat în Word.
6. DOCX-ul se generează din TraceabilityCase, nu direct din fișiere.
7. UI-ul nu conține logică de business.

## Teste virtuale acceptate

| Test | Cod / Lot | Tip caz | Verdict |
|---|---|---|---|
| 1 | DS099903883 / 105.26 | FINISHED_PRODUCT | Acceptat |
| 2 | DS099904006 / 091.26 | FINISHED_PRODUCT | Acceptat |
| 3 | DS099904181 / 092.26 | FINISHED_PRODUCT | Acceptat |
| 4 | DS099904127 / 098.26 | FINISHED_PRODUCT | Acceptat |
| 5 | DS099904015 / 105.26 | FINISHED_PRODUCT | Acceptat |
| 6 | DS099904130 / 90994-082 | RAW_MATERIAL | Acceptat |
| 7 | DS099903913 / 896 | WMS_ONLY_PRODUCT | Acceptat |

## Structura repo la checkpoint

```text
TraceAI-Control/
  README.md
  CHECKPOINT.md
  docs/
    SPECIFICATIE_FUNCTIONALA.md
    TESTE_VALIDATE.md
    RAPORT_DOCX_MODEL.md
    ARHITECTURA.md
    TRACEABILITY_CASE.md
    ROADMAP.md
    STRUCTURA_REPO.md
  src/
    core/
    rules/
    report/
    ui/
  tests/
  samples/
```

## Documente existente

- `README.md` — prezentare proiect.
- `docs/SPECIFICATIE_FUNCTIONALA.md` — specificație funcțională.
- `docs/TESTE_VALIDATE.md` — cele 7 teste virtuale acceptate.
- `docs/RAPORT_DOCX_MODEL.md` — structura și stilul raportului DOCX.
- `docs/ARHITECTURA.md` — arhitectura pe componente.
- `docs/TRACEABILITY_CASE.md` — contractul obiectului intern TraceabilityCase.
- `docs/ROADMAP.md` — ordinea de dezvoltare.
- `docs/STRUCTURA_REPO.md` — structura repo-ului.

## Următorul pas la reluare

La reluarea proiectului, NU se începe cu UI și NU se începe cu DOCX.

Următorul pas corect este:

```text
Faza 2 — Core Engine
```

Primul cod permis:

```text
src/core/
```

Primul obiectiv tehnic:

```text
citirea și inventarierea coloanelor din cele 4 surse:
- trasabilitate_wms.csv
- rapoarte productie.csv
- nomenclator.xlsx
- stoc la moment original.xlsx
```

Nu se calculează trasabilitate încă.

Primul livrabil tehnic la reluare:

```text
un modul care citește fișierele și produce un raport intern cu:
- fișiere găsite
- sheet-uri găsite pentru XLSX
- coloane detectate
- număr de rânduri
- primele probleme de structură
```

## Fraza de reluare recomandată

Când reluăm proiectul, mesajul corect este:

```text
Continuăm de la CHECKPOINT.md cu Faza 2 — Core Engine: citirea și inventarierea celor 4 surse.
```
