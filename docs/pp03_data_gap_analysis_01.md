# PP03 Data Gap Analysis 01

## 1. Scope

This document inventories the real PP-03 output structure and compares it with the current TraceAI-Control audit model.

The goal is to establish, safely and incrementally:

- which PP-03 fields already exist in the current TraceAI model;
- which fields only need clearer presentation;
- which fields require small new mapping or aggregation;
- which fields must remain manual;
- which fields should not be automated.

This document is sanitized.
It does not include the real PP-03 file.
It does not include raw sensitive business data.

## 2. Architectural Boundary

PP-03 is treated strictly as an output reference and audit presentation model.

PP-03 does not become:

- an application input source;
- a source of truth for calculations;
- a source for verdict rules;
- a source for DTO or JSON contracts;
- a source for source mappings.

Official sources remain:

- WMS traceability
- PRD / production report
- nomenclator
- stock-at-moment

## 3. Real PP-03 Structure

The real PP-03 workbook inspected locally contains exactly two sheets:

- `AMONTE`
- `AVAL`

### AMONTE

Observed sections:

- subject of the traceability test;
- finished product stock location;
- product composition;
- packaging / auxiliaries.

### AVAL

Observed sections:

- subject of the traceability test;
- material stock location and usage;
- available documents;
- operational recordings;
- participants.

## 4. Classification Legend

- `A` = already exists and already appears in the current report
- `B` = already exists, but should be displayed more clearly
- `C` = exists in current official sources, but the application does not extract it yet
- `D` = can be calculated or aggregated from current official sources
- `E` = must remain manual
- `F` = should not be automated

## 5. Field Mapping Table

| Sheet | Section | PP-03 field | Sanitized example | Probable real source | Already in TraceAI | Where it appears now | Missing from report | Simple visual polish | New mapping needed | New aggregation/calculation needed | Must stay manual | Class | Risk | Recommendation |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AMONTE | Subject | Product name | `<product_name>` | PRD / nomenclator | Yes | `exercise.product_name`, 01_EXERCITIU, header | No | Yes | No | No | No | B | Low | PP03-DOCX-ENRICHMENT-01A |
| AMONTE | Subject | Product lot | `<product_lot>` | WMS / PRD | Yes | `exercise.lot` | No | No | No | No | No | A | Low | No action |
| AMONTE | Subject | Expiry date | `<expiry_date>` | unconfirmed | Unclear | not explicit | Yes | No | Yes | No | Possibly | C/E | Medium | Verify source presence before implementation |
| AMONTE | Finished product stock | Production date | `<production_date>` | PRD | Yes | `production_date`, 04_PRODUCTIE_CONSUM | Partial | Yes | No | No | No | B | Low | PP03-DOCX-ENRICHMENT-01A |
| AMONTE | Finished product stock | Produced quantity | `<produced_qty>` | PRD | Yes | balance + production orders | No | Yes | No | No | No | B | Low | PP03-DOCX-ENRICHMENT-01A |
| AMONTE | Finished product stock | Stock kg | `<stock_qty>` | stock-at-moment | Yes | finished product balance | No | Yes | No | No | No | B | Low | PP03-DOCX-ENRICHMENT-01A |
| AMONTE | Delivery | Delivery date | `<delivery_date>` | WMS | Yes | downstream deliveries | No | Yes | No | No | No | B | Low | PP03-DOCX-ENRICHMENT-01A |
| AMONTE | Delivery | Delivery note | `<delivery_note>` | WMS | Yes | downstream document number | No | No | No | No | No | A | Low | No action |
| AMONTE | Delivery | Delivered quantity | `<delivered_qty>` | WMS | Yes | downstream + balance | No | Yes | No | No | No | B | Low | PP03-DOCX-ENRICHMENT-01A |
| AMONTE | Delivery | Client | `<client>` | WMS | Yes | downstream | No | Yes | No | No | No | B | Low | PP03-DOCX-ENRICHMENT-01A |
| AMONTE | Delivery | Country | `<country>` | WMS | Not explicit | not explicit | Yes | No | Yes | No | No | C | Medium | PP03-DOCX-ENRICHMENT-01B |
| AMONTE | Composition | Raw material | `<raw_material>` | PRD / WMS | Yes | upstream | No | Yes | No | No | No | B | Low | PP03-DOCX-ENRICHMENT-01A |
| AMONTE | Composition | Supplier | `<supplier>` | WMS receipts | Yes, derived | upstream | No | Yes | Possibly | No | No | B/C | Medium | 01A if presentation-only, 01B if stronger extraction is needed |
| AMONTE | Composition | Source lot | `<source_lot>` | PRD / WMS | Yes | upstream | No | No | No | No | No | A | Low | No action |
| AMONTE | Composition | Reception date | `<reception_date>` | WMS receipts | Yes, derived | upstream | No | Yes | Possibly | No | No | B/C | Medium | 01A or 01B depending on extraction robustness |
| AMONTE | Composition | Source expiry date | `<source_expiry>` | unconfirmed | Unclear | not explicit | Yes | No | Yes | No | Possibly | C/E | Medium | Verify source presence before implementation |
| AMONTE | Composition | Country of origin | `<origin_country>` | unconfirmed | Unclear | not explicit | Yes | No | Yes | No | Possibly | C/E | Medium | Verify source presence before implementation |
| AMONTE | Composition | Received quantity kg | `<received_qty>` | WMS receipts | Partial | receipt summary / lot flow summary | Partial | No | Yes | Possibly | No | C/D | Medium | PP03-DOCX-ENRICHMENT-01B |
| AMONTE | Composition | Stock kg | `<source_stock_qty>` | stock-at-moment | Yes | upstream + lot flows | No | Yes | No | No | No | B | Low | PP03-DOCX-ENRICHMENT-01A |
| AMONTE | Composition | Consumed quantity kg | `<consumed_qty>` | PRD | Yes | upstream + production consumption | No | Yes | No | No | No | B | Low | PP03-DOCX-ENRICHMENT-01A |
| AMONTE | Packaging / auxiliaries | Packaging type | `<packaging_type>` | PRD / WMS / nomenclator | Yes, partially | upstream name / category | Partial | Yes | No | No | No | B | Low | PP03-DOCX-ENRICHMENT-01A |
| AVAL | Subject | Raw material | `<raw_material>` | WMS / PRD | Yes | upstream / source-lot context | Partial | Yes | No | No | No | B | Low | PP03-DOCX-ENRICHMENT-01A |
| AVAL | Subject | Internal code | `<internal_code>` | nomenclator / PRD | Yes | code fields in audit model | Partial | Yes | No | No | No | B | Low | PP03-DOCX-ENRICHMENT-01A |
| AVAL | Usage | Supplier | `<supplier>` | WMS receipts | Yes, derived | upstream | No | Yes | Possibly | No | No | B/C | Medium | 01A or 01B |
| AVAL | Usage | Date of reception | `<reception_date>` | WMS receipts | Yes, derived | upstream | No | Yes | Possibly | No | No | B/C | Medium | 01A or 01B |
| AVAL | Usage | Received | `<received_qty>` | WMS receipts | Partial | receipt summary / lot flows | Partial | No | Yes | Possibly | No | C/D | Medium | PP03-DOCX-ENRICHMENT-01B |
| AVAL | Usage | Stock | `<stock_qty>` | stock-at-moment | Yes | upstream / lot flows | No | Yes | No | No | No | B | Low | PP03-DOCX-ENRICHMENT-01A |
| AVAL | Usage | Used | `<used_qty>` | PRD | Yes | upstream / production consumption | No | Yes | No | No | No | B | Low | PP03-DOCX-ENRICHMENT-01A |
| AVAL | Usage | Finished product code | `<finished_product_code>` | PRD | Yes | production orders | Partial | Yes | No | No | No | B | Low | PP03-DOCX-ENRICHMENT-01A |
| AVAL | Usage | Finished product lot | `<finished_product_lot>` | PRD / WMS | Yes | production orders | Partial | Yes | No | No | No | B | Low | PP03-DOCX-ENRICHMENT-01A |
| AVAL | Usage | DSD stock kg | `<finished_product_stock>` | stock-at-moment | Yes | balance | Partial | Yes | No | No | No | B | Low | PP03-DOCX-ENRICHMENT-01A |
| AVAL | Usage / Delivery | Delivery date | `<delivery_date>` | WMS | Yes | downstream | No | Yes | No | No | No | B | Low | PP03-DOCX-ENRICHMENT-01A |
| AVAL | Usage / Delivery | Delivery note | `<delivery_note>` | WMS | Yes | downstream document number | No | No | No | No | No | A | Low | No action |
| AVAL | Usage / Delivery | Quantity kg | `<delivery_qty>` | WMS | Yes | downstream | No | Yes | No | No | No | B | Low | PP03-DOCX-ENRICHMENT-01A |
| AVAL | Usage / Delivery | Client | `<client>` | WMS | Yes | downstream | No | Yes | No | No | No | B | Low | PP03-DOCX-ENRICHMENT-01A |
| AVAL | Usage / Delivery | Country | `<country>` | WMS | Not explicit | not explicit | Yes | No | Yes | No | No | C | Medium | PP03-DOCX-ENRICHMENT-01B |
| AVAL | Usage grid note | Mixed-lot / losses note | `<sanitized_observation>` | operational / PRD / manual note | Unclear | limited observations only | Partial | No | Possibly | Possibly | Possibly | D/E | High | Keep out of automation until rules are explicit |
| AVAL | Available Documents | Specification raw meat/material/pack | `Y/N/NA` | manual checklist | No | not explicit | Yes | No | No | No | Yes | E | Low | PP03-MANUAL-FIELDS-01 |
| AVAL | Available Documents | Internal reception recording | `Y/N/NA` | manual checklist supported by WMS | Partial | document register only | Partial | No | No | No | Yes | E | Low | PP03-MANUAL-FIELDS-01 |
| AVAL | Available Documents | CMR | `Y/N/NA` | physical document | Not explicit | not explicit | Yes | No | Possibly | No | Yes | E | Medium | PP03-MANUAL-FIELDS-01 |
| AVAL | Available Documents | Health Certificate | `Y/N/NA` | physical document | Not explicit | not explicit | Yes | No | Possibly | No | Yes | E | Medium | PP03-MANUAL-FIELDS-01 |
| AVAL | Available Documents | Packing list | `Y/N/NA` | physical document | Not explicit | not explicit | Yes | No | Possibly | No | Yes | E | Medium | PP03-MANUAL-FIELDS-01 |
| AVAL | Available Documents | Conformity declaration | `Y/N/NA` | physical document | Not explicit | not explicit | Yes | No | Possibly | No | Yes | E | Medium | PP03-MANUAL-FIELDS-01 |
| AVAL | Operational recordings | Setup | `yes/not` | manual operational record | No | not explicit | Yes | No | No | No | Yes | E | Medium | PP03-MANUAL-FIELDS-01 |
| AVAL | Operational recordings | Hygiene / sanitation | `yes/not` | manual operational record | No | not explicit | Yes | No | No | No | Yes | E | Medium | PP03-MANUAL-FIELDS-01 |
| AVAL | Operational recordings | Chamber / storage temperatures | `yes/not` | manual operational record | No | not explicit | Yes | No | No | No | Yes | E | Medium | PP03-MANUAL-FIELDS-01 |
| AVAL | Operational recordings | Defrost temperature | `yes/not` | manual operational record | No | not explicit | Yes | No | No | No | Yes | E | Medium | PP03-MANUAL-FIELDS-01 |
| AVAL | Operational recordings | Metal detector scan | `yes/not` | manual operational record | No | not explicit | Yes | No | No | No | Yes | E | Medium | PP03-MANUAL-FIELDS-01 |
| AVAL | Operational recordings | ATM monitoring | `yes/not` | manual operational record | No | not explicit | Yes | No | No | No | Yes | E | Medium | PP03-MANUAL-FIELDS-01 |
| AVAL | Operational recordings | Packaging conformity / label / weight | `yes/not` | manual operational record | No | not explicit | Yes | No | No | No | Yes | E | Medium | PP03-MANUAL-FIELDS-01 |
| AVAL | Participants | Participant / signatory | `<participant_name>` | manual | No | not explicit | Yes | No | No | No | Yes | E | Low | PP03-MANUAL-FIELDS-01 |

## 6. Delivery Buckets

### PP03-DOCX-ENRICHMENT-01A

Fields that already exist in the current model and only need clearer display, regrouping, relabeling, or better placement in the current TraceAI DOCX.

This bucket is presentation-only.
It must not change calculations, mappings, verdict rules, DTOs, JSON, or source handling.

Typical fields in this bucket:

- product name;
- production date;
- produced quantity;
- finished-product stock;
- delivery date;
- delivered quantity;
- client;
- raw material / packaging display clarity;
- consumed quantity;
- finished product code / lot display clarity.

### PP03-DOCX-ENRICHMENT-01B

Fields that appear to be available in current official sources but are not yet extracted or not yet structured well enough.

This bucket may require:

- small new mapping;
- small new extraction from already-used rows;
- small aggregation from existing official-source evidence.

Typical fields in this bucket:

- country;
- received quantity as a structured numeric field;
- some supplier / reception-date fields where current extraction is only derived text;
- source expiry or origin fields, only if source presence is confirmed first.

### PP03-MANUAL-FIELDS-01

Fields that should remain manual checklist or operator/auditor-completed information.

Typical fields in this bucket:

- available document yes/no/NA checks;
- operational recordings;
- participant/signatory data;
- fields tied to physical dossier verification or manual plant records.

## 7. Risks

- risk of treating PP-03 as application input, which is explicitly forbidden;
- risk of automating fields that should remain manual;
- risk of adding fragile mapping for fields such as `country`, `country of origin`, or `expiry date` before source presence is confirmed;
- risk of mixing presentation-only changes with new extraction logic;
- risk of exposing raw sensitive business data in repository history.

## 8. Non-Goals

This stage does not:

- upload the real PP-03 workbook to GitHub;
- store raw sensitive PP-03 values in the repository;
- use PP-03 as an application input source;
- change product code;
- change the DOCX renderer;
- change tests;
- change DTO or JSON contracts;
- change calculations;
- change verdict rules;
- change source mappings;
- change unit handling;
- generate a PP-03 Excel export;
- make any product `DONE` claim;
- make any release claim.
