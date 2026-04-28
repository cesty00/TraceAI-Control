# TraceabilityCase — contract intern v1

`TraceabilityCase` este obiectul intern stabil al aplicației.

Toate componentele trebuie să lucreze în jurul acestui obiect:

```text
Core Engine -> Rules Engine -> TraceabilityCase -> Report Engine -> DOCX / UI
```

## Principiu

Raportul DOCX nu citește direct fișierele sursă.

UI-ul nu recalculează trasabilitatea.

Testele validează `TraceabilityCase` înainte de raport.

## Structură conceptuală

```text
TraceabilityCase
  metadata
  source_files
  case_info
  case_type
  product_identity
  balance
  wms_receptions
  wms_deliveries
  production_orders
  consumed_components
  raw_materials
  packaging
  auxiliaries
  mp_third_party_movements
  stock_status
  technical_observations
  conclusion
  recommendation
  audit_documents
```

## metadata

```text
schema_version
created_at
engine_version
```

Exemplu:

```json
{
  "schema_version": "TraceAI.TraceabilityCase.v1",
  "created_at": "2026-04-28T00:00:00",
  "engine_version": "0.1.0"
}
```

## source_files

Fișierele folosite la analiză.

```text
wms_path
prd_path
nomenclator_path
stock_path
```

## case_info

Informații introduse sau detectate pentru cazul analizat.

```text
code
lot
requested_by
generated_for
```

## case_type

Valori permise:

```text
FINISHED_PRODUCT
RAW_MATERIAL
WMS_ONLY_PRODUCT
UNKNOWN
```

## product_identity

```text
code
name
lot
category
unit_of_measure
```

## balance

Pentru produse finite:

```text
produced_quantity
produced_uom
delivered_quantity
delivered_uom
operational_stock
stock_uom
reconciliation_status
```

Pentru materie primă:

```text
received_quantity
received_uom
consumed_quantity
consumed_uom
delivered_to_third_parties_quantity
stock_quantity
balance_note
```

Pentru WMS-only:

```text
received_quantity
delivered_quantity
stock_quantity
reconciliation_status
```

## wms_receptions

Rânduri de recepție WMS.

Câmpuri obligatorii când există:

```text
date
code
name
lot
partner
location
order_number
input_document
command_document
quantity
uom
source
```

Regulă:

```text
Document intrare = WMS
Numar comanda = WMS
Document comanda = WMS
```

## wms_deliveries

Rânduri de livrare WMS.

```text
date
code
name
lot
customer
location
order_number
command_document
quantity
uom
source
```

## production_orders

Comenzi de producție în care codul + lotul apar ca produs finit.

```text
order_number
production_date
finished_code
finished_name
finished_lot
quantity
uom
equivalent_weight
weight_uom
ddm
```

## consumed_components

Toate componentele consumate în producția lotului.

```text
production_order
component_code
component_name
component_lot
quantity
uom
classification
```

Classification:

```text
RAW_MATERIAL
PACKAGING
AUXILIARY
UNKNOWN
```

## raw_materials

Materiile prime alimentare extrase din `consumed_components`.

```text
code
name
lot
quantity
uom
reception_summary
third_party_summary
```

## packaging

Ambalaje extrase din `consumed_components`.

```text
code
name
lot
quantity
uom
reception_summary
```

## auxiliaries

Materiale auxiliare / consumabile tehnologice.

```text
code
name
lot
quantity
uom
reception_summary
```

Regulă obligatorie:

```text
GAZ ALIMENTAR ALISOL = AUXILIARY
```

Gazul nu se include niciodată în `raw_materials`.

## mp_third_party_movements

Livrări către terți pentru loturile de materie primă folosite.

```text
mp_code
mp_name
mp_lot
date
customer
order_number
command_document
quantity
uom
```

Regulă:

Dacă nu există livrări către terți, lista este goală, dar raportul trebuie să afișeze explicit că verificarea a fost făcută.

## stock_status

```text
appears_in_stock
stock_quantity
uom
locations
note
```

## technical_observations

Lista observațiilor tehnice.

```text
severity
code
message
source
```

Severity:

```text
INFO
WARNING
CRITICAL
```

## conclusion

Text pregătit pentru raport.

```text
status
summary
```

Status:

```text
TRASABILITATE COERENTĂ
TRASABILITATE COERENTĂ CU OBSERVAȚII
TRASABILITATE INCOMPLETĂ
NECESITĂ VERIFICARE MANUALĂ
```

## recommendation

Recomandare operațională pentru auditor / utilizator.

## audit_documents

Documente care trebuie pregătite fizic sau electronic:

```text
NIR / recepții
Documente livrare
Comenzi producție
Rapoarte producție
Documente stoc
```

## Reguli de validare v1

1. `case_type` este obligatoriu.
2. `source_files` este obligatoriu.
3. Pentru `FINISHED_PRODUCT`, `production_orders` trebuie să existe.
4. Pentru `RAW_MATERIAL`, `wms_receptions` și consumurile PRD trebuie verificate.
5. Pentru `WMS_ONLY_PRODUCT`, lipsa PRD trebuie menționată ca observație.
6. Gazul nu are voie în `raw_materials`.
7. Unitățile de măsură nu se convertesc automat.
8. Documentele WMS se păstrează cu denumirile operaționale: `Numar comanda`, `Document intrare`, `Document comanda`.
