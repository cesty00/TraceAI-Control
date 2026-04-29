# UI — contract de implementare

Acest folder este rezervat pentru viitorul UI profesional simplu.

UI-ul vizual nu este implementat încă. În prezent există doar funcția de orchestrare testabilă.

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

În cod, acest flux este expus prin:

```text
generate_report_from_ui_request()
```

## Funcția de orchestrare

Fișier:

```text
src/ui/orchestrator.py
```

Exporturi:

```text
UiGenerationRequest
UiGenerationResult
generate_report_from_ui_request
validate_ui_generation_request
```

### Input: `UiGenerationRequest`

```text
source_directory
code
lot
output_docx_path
```

### Output: `UiGenerationResult`

```text
success
output_path
message
error
```

## Exemplu de utilizare

```python
from src.ui.orchestrator import UiGenerationRequest, generate_report_from_ui_request

request = UiGenerationRequest(
    source_directory="cale/catre/date",
    code="DS099903883",
    lot="105.26",
    output_docx_path="raport_trasabilitate.docx",
)

result = generate_report_from_ui_request(request)

if result.success:
    print(result.message)
else:
    print(result.error)
```

## Comportament controlat

Funcția de orchestrare:

```text
validează doar câmpurile UI minime
apelează engine-ul existent
returnează status succes/eroare
nu citește direct CSV/XLSX
nu conține logică de business
```

Dacă lipsesc date obligatorii, engine-ul nu este apelat.

Dacă engine-ul ridică o eroare, funcția întoarce un `UiGenerationResult` cu:

```text
success=False
output_path=None
message="Eroare la generarea raportului."
error=<mesaj eroare>
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

## Testare

Testele dedicate sunt în:

```text
tests/test_ui_orchestrator.py
```

Acestea verifică:

```text
orchestrare corectă către engine
validare câmpuri lipsă
fără apel engine când inputul este invalid
capturare eroare engine
raportare câmpuri obligatorii lipsă
```

## Document contract

Contractul complet este definit în:

```text
docs/UI_ENGINE_CONTRACT.md
```

## Următorul pas permis

Următorul pas UI permis este un shell minimal peste orchestrator, fără UI vizual complex și fără logică de business.
