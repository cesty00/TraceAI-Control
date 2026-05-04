# TraceAI Control — Roadmap tehnic următoarea etapă

## Obiectiv general

Transformăm TraceAI Control dintr-un generator validat de raport audit checklist într-un **motor robust de trasabilitate auditabilă**, cu model intern clar, explicații, verificări de calitate date și output-uri reproductibile.

Arhitectura țintă:

```text
Source files
-> Data Quality Gate
-> Normalized Dataset
-> Traceability Graph
-> Rules / Reconciliation Engine
-> TraceabilityCase
-> Audit Checklist UI / DOCX / JSON / Audit Pack
```

## Principii de lucru

- PR-uri mici, verificabile.
- Fiecare PR trebuie să aibă teste.
- UI-ul rămâne strat de orchestrare și prezentare, fără logică de business.
- DOCX-ul nu citește direct fișiere sursă.
- Orice decizie de clasificare trebuie să fie explicabilă prin dovezi.
- Nicio deducție critică fără sursă și confidence score.
- După fiecare etapă importantă se actualizează `CHECKPOINT.md` și/sau `README.md`.

---

# Epic 1 — Data Quality Gate

## Scop

Înainte de generarea raportului, aplicația trebuie să verifice sursele încărcate și să raporteze problemele de calitate a datelor.

## Deliverable

Un modul nou:

```text
src/quality/
  data_quality_gate.py
  models.py
```

Output:

```text
DataQualityReport
```

## Verificări minime

- fișiere lipsă;
- fișiere găsite;
- dimensiune fișiere;
- număr rânduri;
- coloane obligatorii lipsă;
- coloane necunoscute;
- valori goale în cod / lot / cantitate;
- cantități nenumerice;
- date invalide;
- duplicate suspecte;
- UM lipsă;
- coduri care nu există în nomenclator;
- loturi cu spații / formate suspecte.

## Acceptance criteria

- `run_traceability_case()` include sumar Data Quality în `TraceabilityCase.sections`;
- există teste unitare pentru fișier lipsă, coloană lipsă, cantitate invalidă;
- UI poate afișa status clar: `OK`, `WARNING`, `ERROR`;
- raportul DOCX include sumarul Data Quality.

## PR-uri propuse

### PR 1.1 — Add DataQualityReport model

- adaugă dataclass-uri pentru `DataQualityReport`, `DataQualityIssue`, `DataQualityStatus`;
- fără integrare în pipeline încă.

### PR 1.2 — Implement source file checks

- verifică existența fișierelor așteptate;
- verifică număr rânduri și coloane;
- teste pe fixture-uri mici.

### PR 1.3 — Integrate Data Quality into TraceabilityCase

- adaugă sumar în `TraceabilityCase.sections`;
- fără să blocheze încă generarea raportului.

### PR 1.4 — Display Data Quality in DOCX and UI JSON

- secțiune nouă în audit checklist;
- status vizibil pentru auditor.

---

# Epic 2 — Typed Errors și mesaje clare în UI

## Scop

Înlocuim erorile generice cu erori explicite și acționabile.

## Probleme actuale

UI-ul prinde orice excepție și returnează `str(exc)`. Pentru utilizator final, asta nu e suficient.

## Deliverable

Modul nou:

```text
src/errors.py
```

Clase propuse:

```python
TraceAIError
MissingSourceFileError
MissingRequiredColumnError
InvalidInputError
NoMatchingRecordsError
AmbiguousCaseTypeError
ReportGenerationError
DataQualityBlockingError
```

## Acceptance criteria

- `generate_report_from_ui_request()` returnează mesaje clare;
- test pentru fiecare categorie importantă;
- UI nu afișează stack trace brut;
- mesajele includ acțiune recomandată.

## Exemplu mesaj dorit

```text
Nu pot genera raportul: lipsește coloana "Lot" din trasabilitate_wms.csv.

Fișier detectat: trasabilitate_wms.csv
Coloane găsite: Data, Cod articol, Denumire articol, Cantitate
Acțiune recomandată: exportă WMS cu layout-ul standard.
```

## PR-uri propuse

### PR 2.1 — Add typed TraceAI errors

- definește clasele;
- fără schimbare de comportament.

### PR 2.2 — Convert core validation failures to typed errors

- mapare erori existente către clase explicite.

### PR 2.3 — Improve UI orchestrator error handling

- mesaj utilizator + detalii tehnice separate;
- teste pentru UI.

---

# Epic 3 — Traceability Graph Engine

## Scop

Introducem un model intern explicit pentru lanțul de trasabilitate, nu doar tabele raportabile.

## Deliverable

Modul nou:

```text
src/graph/
  models.py
  builder.py
  query.py
  explain.py
```

## Model propus

Noduri:

```text
Article
Lot
ProductionOrder
PrdOutput
PrdConsumption
WmsMovement
StockSnapshot
DeliveryDocument
ReceiptDocument
Customer
Supplier
```

Muchii:

```text
PRODUCED_BY
CONSUMED_IN
MOVED_BY
DELIVERED_TO
RECEIVED_FROM
HAS_DOCUMENT
HAS_STOCK
```

## Acceptance criteria

- pentru un cod+lot se poate construi un `TraceabilityGraph`;
- fiecare nod are `source_key`, `source_name`, `row_number`;
- fiecare muchie are motiv / evidență;
- `TraceabilityCase` poate include sumar graph;
- există teste pentru produs finit, materie primă, WMS-only.

## PR-uri propuse

### PR 3.1 — Add graph data model

- dataclass-uri pentru node, edge, graph;
- serializare JSON;
- teste simple.

### PR 3.2 — Build graph from selected records

- mapare inițială din `result.core.selection.records`;
- fără schimbare DOCX.

### PR 3.3 — Add graph explanation layer

- funcție `explain_traceability_path()`;
- output textual pentru UI și raport.

### PR 3.4 — Add graph summary to TraceabilityCase

- număr noduri;
- număr muchii;
- path-uri găsite;
- path-uri lipsă.

---

# Epic 4 — Rule Engine declarativ

## Scop

Mutăm clasificările fragile din cod hardcodat în reguli declarative testabile.

## Problemă

Acum clasificarea folosește hint-uri text precum `ALISOL`, `ambalaj`, `materie prima`, `livrare`. Asta funcționează pe cazuri cunoscute, dar poate eșua când apar denumiri noi.

## Deliverable

Folder nou:

```text
config/rules/
  classification_rules.yaml
```

Modul:

```text
src/rules/declarative/
  loader.py
  evaluator.py
  models.py
```

## Exemplu regulă

```yaml
classification_rules:
  auxiliary_gas:
    priority: 100
    conditions:
      - field: Denumire
        contains_any:
          - ALISOL
          - gaz
    result:
      category: AUXILIARY_GAS
      confidence: 0.95

  packaging:
    priority: 80
    conditions:
      - field: Denumire
        contains_any:
          - ambalaj
          - cutie
          - folie
          - etichetă
          - capac
    result:
      category: PACKAGING
      confidence: 0.85
```

## Acceptance criteria

- clasificarea returnează `category`, `confidence`, `matched_rules`;
- vechile hint-uri sunt păstrate temporar ca fallback;
- raportul poate afișa motivul clasificării;
- teste pentru ALISOL, ambalaje, materii prime, livrări.

## PR-uri propuse

### PR 4.1 — Add declarative rule model and loader

### PR 4.2 — Add evaluator with matched rule evidence

### PR 4.3 — Integrate declarative rules into TraceabilityCase mapping

### PR 4.4 — Deprecate hardcoded classification hints

---

# Epic 5 — Reconciliation Engine

## Scop

Calculăm diferențe explicite între PRD, WMS, livrări, consumuri și stoc.

## Deliverable

Modul nou:

```text
src/reconciliation/
  models.py
  engine.py
```

## Verificări propuse

- cantitate produs finit PRD vs WMS production-out;
- produs finit produs vs livrat;
- produs finit produs vs stoc rămas;
- consumuri PRD vs loturi identificate;
- UM mixte fără conversie;
- cantități negative;
- documente lipsă;
- livrări fără client;
- recepții fără furnizor.

## Output

```text
ReconciliationReport
  status: PASS | PASS_WITH_OBSERVATIONS | FAIL | INCONCLUSIVE
  checks: list[ReconciliationCheck]
```

## Acceptance criteria

- fiecare check are status, mesaj și dovezi;
- diferențele numerice sunt explicite;
- nu se fac conversii automate de UM;
- raportul DOCX include sumarul reconcilierii.

## PR-uri propuse

### PR 5.1 — Add reconciliation model

### PR 5.2 — Implement PRD vs WMS quantity check

### PR 5.3 — Implement delivery and stock checks

### PR 5.4 — Add reconciliation section to audit checklist

---

# Epic 6 — Audit Pack Export

## Scop

La final, aplicația trebuie să genereze nu doar DOCX, ci un pachet complet de audit.

## Deliverable

Output ZIP:

```text
AuditPack_<code>_<lot>_<timestamp>.zip
  audit_report.docx
  traceability_case.json
  data_quality_report.json
  reconciliation_report.json
  source_manifest.json
  audit_checklist_ui.json
  documents_to_check.tsv
```

## Acceptance criteria

- ZIP-ul se generează din UI;
- toate fișierele sunt reproductibile;
- include metadata build: versiune, commit, dată generare;
- teste pentru conținut ZIP.

## PR-uri propuse

### PR 6.1 — Add source manifest export

### PR 6.2 — Add audit pack builder

### PR 6.3 — Add UI action for audit pack export

---

# Epic 7 — Performance și cache local

## Scop

Aplicația trebuie să rămână rapidă pe fișiere mari WMS.

## Deliverable

Cache local:

```text
.traceai_cache/
  manifest.json
  wms.parquet
  production.parquet
  stock.parquet
  indexes.sqlite
```

## Acceptance criteria

- prima rulare indexează sursele;
- rulările următoare detectează dacă fișierele nu s-au schimbat;
- căutarea cod+lot este semnificativ mai rapidă;
- cache-ul poate fi invalidat din UI.

## PR-uri propuse

### PR 7.1 — Add source fingerprinting

### PR 7.2 — Add local cache manifest

### PR 7.3 — Add indexed lookup by code and lot

### PR 7.4 — Add UI cache status

---

# Epic 8 — Batch Mode

## Scop

Rulează trasabilitate pentru mai multe perechi cod+lot.

## Input

CSV:

```csv
code,lot
DS099903883,105.26
DS0001,L001
```

## Output

```text
batch_summary.xlsx
audit_packs/
  case_1/
  case_2/
```

## Acceptance criteria

- rulează N cazuri;
- continuă chiar dacă un caz eșuează;
- produce sumar cu status per caz;
- exportă pachete individuale opțional.

## PR-uri propuse

### PR 8.1 — Add batch input parser

### PR 8.2 — Add batch runner

### PR 8.3 — Add batch summary export

---

# Ordinea recomandată

## Faza 1 — Stabilitate

```text
Epic 1 — Data Quality Gate
Epic 2 — Typed Errors
```

## Faza 2 — Motor real de trasabilitate

```text
Epic 3 — Traceability Graph
Epic 4 — Rule Engine declarativ
Epic 5 — Reconciliation Engine
```

## Faza 3 — Produs utilizabil

```text
Epic 6 — Audit Pack
Epic 7 — Cache local
Epic 8 — Batch Mode
```

---

# Primul issue recomandat

## Title

```text
EPIC: Add Data Quality Gate before traceability report generation
```

## Body

```markdown
## Goal

Add a Data Quality Gate that validates source files before traceability report generation.

## Why

TraceAI Control currently generates audit reports from normalized operational sources. Before report generation, the system should explicitly verify source completeness, required columns, row counts, invalid quantities, missing lots, and other data quality risks.

This will make the audit output more reliable and easier to explain.

## Scope

Add:

- `src/quality/models.py`
- `src/quality/data_quality_gate.py`
- `DataQualityReport`
- `DataQualityIssue`
- `DataQualityStatus`

The first version should validate:

- required files exist;
- required columns exist;
- row counts are reported;
- invalid quantity values are detected.

## Out of scope

- Traceability graph.
- Reconciliation engine.
- Batch mode.
- UI redesign.

## Acceptance criteria

- Data Quality Report can be generated from the same source directory used by `run_traceability_case`.
- `TraceabilityCase.sections` includes a data quality summary.
- Tests cover:
  - missing source file;
  - missing required column;
  - invalid quantity;
  - valid minimal dataset.
- Existing tests continue to pass.
- `CHECKPOINT.md` is updated after validation.

## Suggested implementation steps

1. Add data quality dataclasses.
2. Add source profile definitions for WMS, production, stock, nomenclator.
3. Implement file existence checks.
4. Implement required column checks.
5. Implement simple row-level checks.
6. Integrate summary into `TraceabilityCase.sections`.
7. Add tests.
8. Run diagnostics.
9. Update checkpoint.

## Expected output example

```json
{
  "status": "WARNING",
  "source_count": 4,
  "issues": [
    {
      "severity": "WARNING",
      "source_key": "wms",
      "message": "2 rows have empty lot values",
      "row_count": 2
    }
  ]
}
```
```

---

# Recomandare de start

Începe cu **Epic 1 / PR 1.1 + PR 1.2**, nu cu graph-ul. Data Quality Gate oferă fundația corectă și va prinde multe buguri înainte de complicarea motorului.
