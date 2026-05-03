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
rafinări UX de prezentare pentru secțiuni și tabele
copy/export pentru secțiunea selectată
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
copiere/export secțiune selectată din modelul de afișare
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
-> export_section_display_as_text(display_model)
-> export_section_display_as_tsv(display_model)
```

UI-ul nu reconstruiește tabelele din `TraceabilityCase` și nu citește din DOCX.

## Audit checklist section widgets

Fișier:

```text
src/ui/audit_checklist_section_widgets.py
```

Exporturi relevante:

```text
SectionListItem
SectionDisplayModel
build_section_list_items
find_section_by_key
build_section_display_model
export_section_display_as_text
export_section_display_as_tsv
rows_to_tsv
normalize_tsv_cell
humanize_field_label
truncate_display_text
```

Rol:

```text
construiește lista de navigare a secțiunilor
păstrează ordinea din view-model
construiește modelul de afișare pentru secțiunea selectată
exportă secțiunea selectată ca text lizibil
exportă secțiunea selectată ca TSV pentru Excel/Sheets
normalizează celulele TSV ca să rămână un rând per record
nu calculează și nu interpretează business
```

## UI vizual audit checklist

Fișier:

```text
src/ui/visual.py
```

Funcții relevante:

```text
VisualAuditChecklistResult
submit_audit_checklist_form_values
validate_audit_checklist_form_values
format_audit_checklist_preview
format_section_display_text
write_selected_section_tsv
```

UI-ul vizual include:

```text
Previzualizează audit checklist
Copiază text
Copiază TSV
Exportă TSV...
```

Copierea/exportul folosește strict `SectionDisplayModel`. Nu citește fișiere operaționale și nu generează raport audit nou.

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

Acestea verifică inclusiv:

```text
export text pentru secțiunea selectată
export TSV pentru table/details/empty
normalizare celule TSV
scriere TSV pe disc din UI visual helper
oprirea apelului audit checklist când lipsesc câmpuri UI
```

## Document contract

Contractul complet este definit în:

```text
docs/UI_ENGINE_CONTRACT.md
```

## Următorul pas permis

Următorul pas UI permis este rafinare de usability pentru exporturi sau pachetare aplicație, fără logică de business nouă.
