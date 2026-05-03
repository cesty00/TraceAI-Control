# UI — contract de implementare

Acest folder conține straturile UI minimale pentru TraceAI Control.

În prezent există:

```text
funcție de orchestrare testabilă
CLI/UI shell minimal peste orchestrator
UI vizual minimal peste orchestrator
contract JSON audit checklist pentru interfață
view-model audit checklist bazat pe payload["sections"]
widgeturi dedicate pentru secțiuni audit checklist
```

UI-ul vizual este implementat minimal, cu Tkinter, și rămâne doar strat peste orchestrator.

## Rol permis

UI-ul este doar strat de orchestrare și prezentare:

```text
colectare source_directory
colectare code
colectare lot
colectare output_docx_path
apel engine existent
afișare succes / eroare
afișare secțiuni audit checklist deja pregătite în audit-checklist-ui.v1
```

## Apel engine permis

Fluxul permis pentru raportul DOCX minimal existent este:

```text
run_traceability_case(source_directory, code, lot)
-> generate_minimal_docx_report(traceability_case, output_docx_path)
```

În cod, acest flux este expus prin:

```text
generate_report_from_ui_request()
```

Fluxul permis pentru interfața audit checklist este:

```text
build_audit_checklist_ui_payload(source_directory, code, lot)
-> build_audit_checklist_ui_view_model(payload)
-> build_section_list_items(view_model)
-> build_section_display_model(section)
-> render secțiuni în UI
```

UI-ul nu reconstruiește tabelele din `TraceabilityCase` și nu citește din DOCX.

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

## Audit checklist UI JSON

Fișier:

```text
src/ui/audit_checklist_json.py
```

Contract:

```text
schema_version = audit-checklist-ui.v1
```

Payload-ul conține:

```text
subject
sections
report
```

`sections` este ordinea de afișare pentru interfață. `report` păstrează raportul complet pentru consumatori avansați, dar UI-ul standard trebuie să randeze din `sections`.

## Audit checklist view-model

Fișier:

```text
src/ui/audit_checklist_view_model.py
```

Exporturi:

```text
AuditChecklistUiSection
AuditChecklistUiViewModel
build_audit_checklist_ui_view_model
validate_audit_checklist_ui_payload
```

Rol:

```text
validează schema UI
citește payload["sections"]
clasifică secțiunile ca table / details / empty
expune column_keys pentru tabele
expune field_keys pentru detalii
păstrează valorile din payload fără reinterpretare business
```

## Audit checklist section widgets

Fișier:

```text
src/ui/audit_checklist_section_widgets.py
```

Exporturi:

```text
SectionListItem
SectionDisplayModel
build_section_list_items
find_section_by_key
build_section_display_model
```

Rol:

```text
construiește lista de navigare a secțiunilor
păstrează ordinea din view-model
construiește modelul de afișare pentru secțiunea selectată
transformă details în perechi cheie/valoare
transformă table în coloane și rânduri pentru Treeview
nu calculează și nu interpretează business
```

Exemplu de utilizare Python:

```python
from src.ui.audit_checklist_json import build_audit_checklist_ui_payload
from src.ui.audit_checklist_view_model import build_audit_checklist_ui_view_model
from src.ui.audit_checklist_section_widgets import build_section_display_model, build_section_list_items

payload = build_audit_checklist_ui_payload(
    "cale/catre/date",
    code="DS099903883",
    lot="105.26",
)
view_model = build_audit_checklist_ui_view_model(payload)
items = build_section_list_items(view_model)
selected = view_model.sections[0]
display = build_section_display_model(selected)

print(items[0].label)
print(display.summary)
```

## UI vizual audit checklist

Fișier:

```text
src/ui/visual.py
```

Flux testabil:

```text
submit_audit_checklist_form_values(source_directory, code, lot)
-> build_audit_checklist_ui_payload(...)
-> build_audit_checklist_ui_view_model(payload)
-> VisualAuditChecklistResult
```

Funcții:

```text
VisualAuditChecklistResult
submit_audit_checklist_form_values
validate_audit_checklist_form_values
format_audit_checklist_preview
format_section_display_text
```

UI-ul vizual include butonul:

```text
Previzualizează audit checklist
```

Butonul afișează:

```text
listă de secțiuni în stânga
titlu și sumar pentru secțiunea selectată
detalii text pentru secțiunea selectată
tabel Treeview pentru secțiunile table
```

Aceasta este o randare UI minimală, nu un raport audit nou și nu o sursă de adevăr separată.

## Exemplu de utilizare Python pentru DOCX minimal

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

## CLI/UI shell minimal

Fișier:

```text
src/ui/cli.py
```

Rulare:

```bash
python -m src.ui.cli "cale/catre/date" --code DS099903883 --lot 105.26 --output raport_trasabilitate.docx
```

CLI-ul minimal:

```text
parsează argumentele
construiește UiGenerationRequest
apelează generate_report_from_ui_request()
afișează mesajul rezultatului
returnează cod 0 la succes
returnează cod 1 la eroare
```

## UI vizual minimal

Fișier:

```text
src/ui/visual.py
```

Rulare:

```bash
python -m src.ui.visual
```

UI-ul vizual minimal include:

```text
câmp folder surse oficiale
câmp cod articol
câmp lot
câmp raport DOCX output
buton previzualizare audit checklist
buton generare raport DOCX
listă secțiuni audit checklist
panou detalii / tabel pentru secțiunea selectată
mesaj succes / eroare
```

Funcții testabile:

```text
build_request_from_form_values()
submit_visual_form_values()
submit_audit_checklist_form_values()
format_audit_checklist_preview()
format_section_display_text()
run_visual_app()
```

Testele nu pornesc fereastra grafică; verifică maparea câmpurilor, apelul către orchestrator prin handler injectat, modelele de afișare și fallback-ul textual pentru secțiunea selectată.

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

Pentru audit checklist, lipsa `source_directory`, `code` sau `lot` oprește apelul către builderul de payload.

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

UI-ul audit checklist nu are voie să:

```text
parseze DOCX
reconstruiască tabele din TraceabilityCase brut
recalculeze cantități
schimbe ordinea secțiunilor primită în payload["sections"]
înlocuiască lipsurile explicite FARA DATE IDENTIFICATE
```

## Testare

Testele dedicate sunt în:

```text
tests/test_ui_orchestrator.py
tests/test_ui_cli.py
tests/test_ui_visual.py
tests/test_audit_checklist_ui_json.py
tests/test_audit_checklist_view_model.py
tests/test_audit_checklist_section_widgets.py
```

Acestea verifică:

```text
orchestrare corectă către engine
validare câmpuri lipsă
fără apel engine când inputul este invalid
capturare eroare engine
raportare câmpuri obligatorii lipsă
maparea argumentelor CLI în UiGenerationRequest
cod 0 la succes CLI
cod 1 la eroare CLI
maparea câmpurilor vizuale în UiGenerationRequest
apelarea orchestratorului din formularul vizual
propagarea rezultatului de succes/eroare în UI vizual
schema audit-checklist-ui.v1
ordinea secțiunilor audit checklist
maparea rows / data în view-model fără rebuild business
validarea formelor invalide de payload UI
previzualizarea audit checklist din view-model
modelele de afișare pentru secțiuni details/table/empty
fallback text pentru secțiunea selectată
oprirea apelului audit checklist când lipsesc câmpuri UI
```

## Document contract

Contractul complet este definit în:

```text
docs/UI_ENGINE_CONTRACT.md
```

## Următorul pas permis

Următorul pas UI permis este rafinarea experienței vizuale a widgeturilor dedicate, fără logică de business nouă.
