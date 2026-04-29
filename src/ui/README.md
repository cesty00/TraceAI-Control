# UI — contract de implementare

Acest folder este rezervat pentru viitorul UI profesional simplu.

UI-ul nu este implementat încă.

## Rol permis

UI-ul va fi doar strat de orchestrare:

```text
colectare source_directory
colectare code
colectare lot
colectare output_docx_path
apel engine existent
afișare succes / eroare
```

## Apel engine permis

Fluxul permis este:

```text
run_traceability_case(source_directory, code, lot)
-> generate_minimal_docx_report(traceability_case, output_docx_path)
```

## Interdicții

UI-ul nu are voie să conțină logică de business.

UI-ul nu citește direct fișierele operaționale pentru:

```text
clasificare caz
calcul bilanț
populare report_tables
generare DOCX directă
deducere trasabilitate amonte/aval
conversii de unități de măsură
```

## Document contract

Contractul complet este definit în:

```text
docs/UI_ENGINE_CONTRACT.md
```

## Următorul pas permis

Primul cod UI permis este o funcție de orchestrare testabilă, fără interfață grafică complexă.
