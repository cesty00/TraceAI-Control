# UI — contract de implementare

Acest folder conține straturile UI minimale pentru TraceAI Control.

În prezent există:

```text
funcție de orchestrare testabilă
CLI/UI shell peste orchestrator
UI vizual peste orchestrator
contract JSON audit checklist pentru interfață
view-model audit checklist bazat pe payload["sections"]
widgeturi dedicate pentru secțiuni audit checklist
copy/export pentru secțiunea selectată
generare DOCX audit checklist din aplicație
```

## Flux DOCX implicit în aplicație

Butonul de generare raport din aplicație trebuie să producă raportul audit checklist, nu raportul tehnic/minimal vechi.

Fluxul implicit este:

```text
run_traceability_case(source_directory, code, lot)
-> build_audit_traceability_report(traceability_case)
-> build_audit_checklist_report(audit_report)
-> generate_audit_checklist_docx_report(checklist_report, output_docx_path)
```

Adaptorul folosit de UI este:

```text
generate_audit_checklist_docx_from_traceability_case()
```

Orchestratorul principal este:

```text
generate_report_from_ui_request()
```

Mesajul de succes așteptat este:

```text
Raport audit checklist generat cu succes: <cale output>
```

Dacă un raport generat din aplicație începe cu:

```text
Raport trasabilitate TraceAI Control
RAPORT DE TRASABILITATE
```

înseamnă că aplicația rulează încă vechiul flux `docx_minimal` sau un build neactualizat.

Raportul audit checklist nou începe cu:

```text
TEST DE TRASABILITATE PENTRU AUDIT
Rezumat de conformare checklist
01_EXERCITIU — Fișa principală a exercițiului
```

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

UI-ul nu reconstruiește tabelele din `TraceabilityCase` și nu citește din DOCX.

## UI vizual audit checklist

Fișier:

```text
src/ui/visual.py
```

UI-ul vizual include:

```text
Previzualizează audit checklist
Copiază text
Copiază TSV
Exportă TSV...
Generează raport DOCX
```

`Generează raport DOCX` folosește orchestratorul UI și trebuie să genereze raportul audit checklist validat.

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
orchestrarea UI către generatorul DOCX audit checklist
mesajul de succes pentru raport audit checklist
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
