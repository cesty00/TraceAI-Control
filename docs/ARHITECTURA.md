# Arhitectură — TraceAI Control Modul Trasabilitate

## Obiectiv arhitectural

Aplicația trebuie să fie stabilă, testabilă și ușor de folosit zilnic.

Nu construim aplicația direct peste UI. Construim mai întâi motorul de trasabilitate.

## Componente principale

```text
Core Engine
Rules Engine
Report Engine
UI
Installer
Tests
```

## Core Engine

Responsabilități:

- citește fișierele sursă;
- normalizează coloanele;
- normalizează cantitățile;
- păstrează unitățile de măsură;
- identifică articolul și lotul;
- construiește obiectul TraceabilityCase.

Surse citite:

```text
trasabilitate_wms.csv
rapoarte productie.csv
nomenclator.xlsx
stoc la moment original.xlsx
```

## Rules Engine

Responsabilități:

- detectează tipul cazului;
- clasifică articolele;
- separă materii prime, ambalaje și auxiliare;
- aplică regula gazului;
- verifică bilanțurile;
- identifică AVAL MP;
- generează observații tehnice.

Tipuri caz:

```text
FINISHED_PRODUCT
RAW_MATERIAL
WMS_ONLY_PRODUCT
UNKNOWN
```

Regulă explicită:

```text
GAZ ALIMENTAR ALISOL = auxiliar / consumabil tehnologic
```

## Report Engine

Responsabilități:

- primește TraceabilityCase;
- generează DOCX;
- aplică structura potrivită tipului de caz;
- formulează concluzia;
- adaugă tabele și anexe;
- nu recalculează logica de business.

Regulă:

```text
DOCX-ul se generează doar din TraceabilityCase.
```

## UI

Responsabilități:

- permite selectarea fișierelor sursă;
- permite introducerea codului și lotului;
- rulează analiza;
- afișează status și rezumat;
- lansează generarea raportului DOCX;
- deschide folderul de rapoarte.

UI-ul nu trebuie să conțină logică de business.

## Installer

Responsabilități:

- instalează aplicația pe calculator;
- creează shortcut;
- include dependențe necesare;
- păstrează folder de output pentru rapoarte;
- permite update controlat.

## Tests

Testele verifică TraceabilityCase, nu doar DOCX-ul.

Test matrix v1:

```text
DS099903883 / 105.26
DS099904006 / 091.26
DS099904181 / 092.26
DS099904127 / 098.26
DS099904015 / 105.26
DS099904130 / 90994-082
DS099903913 / 896
```

## Obiect intern — TraceabilityCase

Structură conceptuală:

```text
TraceabilityCase
  case_info
  case_type
  source_files
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

## Flux intern

```text
Fișiere sursă
  -> Core Engine
  -> Rules Engine
  -> TraceabilityCase
  -> Report Engine
  -> DOCX
  -> UI afișează rezultat
```

## Reguli de separare

```text
Core Engine nu generează DOCX.
Rules Engine nu citește UI.
Report Engine nu citește fișiere sursă.
UI nu conține logică de business.
Tests verifică motorul, nu doar interfața.
```

## Structură viitoare repo

```text
src/
  core/
  rules/
  report/
  ui/
tests/
samples/
docs/
```

Nu se adaugă cod până la acceptarea documentației funcționale și arhitecturale.
