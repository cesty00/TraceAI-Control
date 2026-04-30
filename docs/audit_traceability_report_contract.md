# TraceAI audit traceability report contract

Status: accepted functional model for implementation
Reference case: `DS099904011 / 103.26`
Reference product: `PF-REFRIGERAT-FD CREVETI PREFIERTI 20/30 500G ATM LIDL`

## 1. Purpose

This document translates the validated audit-style report into a technical contract for TraceAI Control. Future report generation must follow this contract instead of the earlier generic table dump layout.

The report must answer, in audit language:

- what lot is being checked;
- what finished product quantity was produced;
- what was delivered downstream;
- what raw materials, packaging and auxiliary materials entered the production;
- whether consumed raw-material lots were also delivered to third parties;
- what physical documents must be prepared for the auditor.

## 2. Functional references

### Manual v2.1

The report follows `Manual_verificare_trasabilitate_audit_v2.1.docx`:

- `01_EXERCITIU` = main exercise sheet / report identity and conclusion;
- `02_TABEL_I_AMONTE` = upstream traceability for raw materials, packaging and auxiliaries;
- `03_TABEL_II_AVAL` = downstream traceability for finished product deliveries;
- `04_PRODUCTIE_CONSUM` = production orders and consumption by order;
- `05_FLUX_LOTURI_SI_DOCUMENTE` = lot flow and physical document register.

### Visual audit reference

The scanned audit example `TEST DE TRASABILITATE PENTRU AUDIT` shows the desired audit language:

- page 1: exercise identity, product balance, downstream deliveries;
- page 2: upstream table for raw materials, packaging and auxiliary material;
- pages 3-6: production orders split separately, each with finished product, raw materials, packaging and gas;
- page 7: lot/document flow, physical document register and internal audit conclusion.

## 3. Required output sections

The DOCX report must be rendered in this order:

1. `01_EXERCITIU — Fișa principală a exercițiului`
2. `03_TABEL_II_AVAL — Livrări produs finit`
3. `02_TABEL_I_AMONTE — Materii prime, ambalaje și materiale auxiliare`
4. `04_PRODUCTIE_CONSUM — Detaliere pe comenzi de producție`
5. `05_FLUX_LOTURI_SI_DOCUMENTE — Fluxuri loturi și documente fizice`
6. `Concluzie audit intern`
7. `Surse analizate`

The previous generic sections may remain available for diagnostics, but the default audit report must use the structure above.

## 4. Data authority rules

### WMS

WMS is official for:

- finished product deliveries;
- production-out movement confirmation;
- receipts, stock corrections, third-party deliveries and stock movements;
- document numbers, clients, suppliers and movement dates where available.

### PRD

PRD is official/support for:

- production order list;
- finished product quantity per order;
- consumed raw materials;
- consumed packaging;
- consumed auxiliary/gas material;
- deduplication by production order and consumed lot.

### Stock at moment

Stock file is used for:

- final stock checks;
- stock location where available;
- evidence that a lot still exists after production/delivery.

### Nomenclator

Nomenclator is used to classify items:

- finished product;
- raw material;
- packaging;
- auxiliary/gas.

## 5. Official report data model

Add a stable audit-level DTO, separate from low-level `TraceabilityCase.report_tables`.

Suggested model:

```python
@dataclass(frozen=True)
class AuditTraceabilityReport:
    exercise: AuditExercise
    balance: FinishedProductBalance
    downstream: list[FinishedProductDelivery]
    upstream: list[UpstreamMaterialLine]
    production_orders: list[ProductionOrderTrace]
    source_lot_flows: list[SourceLotFlow]
    physical_documents: list[PhysicalDocumentRequirement]
    observations: list[str]
    conclusion: AuditConclusion
```

### 5.1 AuditExercise

Fields:

- `code`
- `lot`
- `product_name`
- `case_type`
- `audit_date`
- `source_directory`
- `data_sources`
- `traceability_result` = `PASS`, `PASS_WITH_OBSERVATIONS`, `FAIL`, `INCOMPLETE`

### 5.2 FinishedProductBalance

Fields:

- `prd_produced_quantity`
- `prd_produced_um`
- `wms_production_out_quantity`
- `wms_production_out_um`
- `wms_delivered_quantity`
- `wms_delivered_um`
- `stock_quantity`
- `stock_um`
- `adjustments_quantity`
- `adjustments_um`
- `balance_status`
- `balance_observation`

Rules:

- production must compare PRD produced total to WMS `Ajustare pozitiva / PRODUCTION-OUT`;
- downstream must compare WMS deliveries in absolute value to WMS production-out, unless stock or adjustments explain the difference;
- WMS movements of type `Mutare` and `Mutare intre gestiuni` are not balance outputs unless explicitly requested.

### 5.3 FinishedProductDelivery

Fields:

- `order_number`
- `document_number`
- `client`
- `delivery_date`
- `quantity`
- `um`
- `rows`
- `source_rows`

### 5.4 UpstreamMaterialLine

Fields:

- `category` = `raw_material`, `packaging`, `auxiliary_gas`
- `code`
- `lot`
- `name`
- `quantity_consumed`
- `um`
- `receipt_summary`
- `supplier_summary`
- `document_summary`
- `third_party_delivery_status` = `DA`, `NU`, `NECLAR`, `NU_SE_APLICA`
- `third_party_delivery_details`
- `stock_at_moment`
- `stock_um`
- `observations`

Rules:

- raw materials must include third-party delivery verification;
- packaging must include lot and consumed quantity;
- gas must be displayed explicitly as auxiliary/gas, not raw material;
- `COR STOC` or missing receipt must be marked as an audit observation.

### 5.5 ProductionOrderTrace

Fields:

- `production_order`
- `finished_product_code`
- `finished_product_lot`
- `finished_product_name`
- `prd_quantity`
- `prd_um`
- `wms_production_out_quantity`
- `wms_production_out_um`
- `associated_delivery`
- `raw_materials`
- `packaging`
- `auxiliaries_gas`
- `observations`

Rules:

- report one block per production order;
- never render all orders as one very wide table;
- each order block contains small tables for raw materials, packaging and gas;
- associated delivery may be exact or candidate when only quantity matching is possible.

### 5.6 SourceLotFlow

Fields:

- `category`
- `code`
- `lot`
- `name`
- `receipt_total`
- `receipt_documents`
- `consumed_in_audited_lot`
- `consumed_in_other_orders`
- `third_party_delivered_total`
- `adjustments_total`
- `stock_at_moment`
- `flow_status`
- `observation`

### 5.7 PhysicalDocumentRequirement

Fields:

- `document_area` = `PRD`, `WMS`, `NIR`, `stock`, `correction`, `other`
- `document_type`
- `document_reference`
- `related_code`
- `related_lot`
- `related_order`
- `why_needed`
- `status` = `required`, `recommended`, `optional`

## 6. Report rendering contract

### 6.1 01_EXERCITIU

Must include:

- verified code and lot;
- product name;
- product type;
- source files used;
- result status;
- concise balance table;
- main observations.

### 6.2 03_TABEL_II_AVAL

Must include finished product deliveries with:

- client;
- document number;
- delivery quantity;
- delivery date if available;
- reconciliation against produced quantity.

### 6.3 02_TABEL_I_AMONTE

Must include all raw materials, packaging and auxiliary/gas lines with:

- code;
- lot;
- name;
- consumed quantity;
- source receipt/document summary where available;
- third-party delivery status for raw materials;
- audit observations.

### 6.4 04_PRODUCTIE_CONSUM

Must be rendered as one subsection per production order:

```text
Comanda producție <order>
- produs finit / lot / quantity
- WMS production-out
- associated finished product delivery
- raw materials table
- packaging table
- auxiliary/gas table
```

### 6.5 05_FLUX_LOTURI_SI_DOCUMENTE

Must include:

- source lot flow summary;
- raw-material lots used in other orders;
- third-party deliveries if any;
- stock/correction observations;
- physical document register.

## 7. Regression acceptance criteria

For `DS099904011 / 103.26`, the report must show:

- product: `PF-REFRIGERAT-FD CREVETI PREFIERTI 20/30 500G ATM LIDL`;
- PRD produced total: `1560 BUCATA`;
- WMS production-out total: `1560 BUCATA`;
- WMS delivered total: `-1560 BUCATA`;
- six production orders:
  - `0030412_DC`
  - `0030421_DC`
  - `0030423_DC`
  - `0030429_DC`
  - `0030431_DC`
  - `0030433_DC`
- raw material lots:
  - `DS099903930 / 90924-070 / 686 Kilogram`
  - `DS099903930 / 90987-079 / 108 Kilogram`
- third-party delivery status for both raw-material lots: `NU`;
- gas line: `60001 / 09.04.26 / GAZ ALIMENTAR ALISOL / 17.55 M3`;
- packaging lines: `10002`, `20011`, `40003`, `40027`, `40028`, `50012`;
- document register with PRD orders, WMS deliveries, raw-material receipts, packaging/gas evidence and correction/stock observations.

## 8. Implementation phases

### AUDIT-REPORT-01 — data DTO

Create `src/audit/audit_traceability_report.py` and map current normalized dataset / TraceabilityCase into `AuditTraceabilityReport`.

### AUDIT-REPORT-02 — DOCX renderer

Create audit-specific renderer:

- `src/report/audit_docx.py`
- default report uses the audit sections above;
- old `docx_minimal.py` remains diagnostic/fallback.

### AUDIT-REPORT-03 — regression fixture

Add regression script/test for `DS099904011 / 103.26`:

- validates totals;
- validates six order sections;
- validates raw-material third-party delivery status;
- validates document register existence.

### AUDIT-REPORT-04 — workflow artifact

Add `real_audit_traceability_report.docx` to TraceAI Diagnostics artifacts.

## 9. Non-negotiable constraints

- Do not invent missing document numbers, suppliers, addresses or dates.
- When evidence is partial, write `FARA DATE IDENTIFICATE` or `NECLAR`, not assumptions.
- Keep WMS as official movement source.
- Keep PRD as production/consumption support source.
- Use nomenclator for classification by code and name.
- Render one production order per block, not one wide table.
- Keep raw-material third-party delivery check visible.
- Keep physical document checklist at the end of the audit report.
