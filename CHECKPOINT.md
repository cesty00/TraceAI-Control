# CHECKPOINT — TraceAI Control Modul Trasabilitate

Data checkpoint: 2026-04-29

## Status general

Proiectul este în repo-ul:

```text
cesty00/TraceAI-Control
```

Stadiul curent este:

```text
Faza 0 — Documentație și arhitectură inițială: finalizată
Faza 1 — Schelet repo: finalizată
Faza 2 — Core Engine: implementată tehnic v1
Faza 3 — Rules Engine: implementată tehnic v1
Faza 4 — TraceabilityCase: contract + report_tables + populare controlată + reguli clasificare + bilanț preliminar conservator implementate
Faza 5 — Report Engine DOCX: implementată tehnic v1 narativ + tabele Word reale + șablon profesional minimal + bilanț preliminar randat
Faza 5.1 — Flux E2E controlat DOCX: implementat tehnic
Faza 5.2 — Runner demonstrativ DOCX controlat: implementat tehnic + test automat dedicat + documentație de utilizare
Faza 5.3 — README principal sincronizat cu statusul curent și runnerul demonstrativ
Faza 6.0 — Contract minim UI -> engine: definit și documentat
Faza 6.1 — Funcție UI de orchestrare testabilă: implementată tehnic + documentată
Faza 6.2 — CLI/UI shell minimal peste orchestrator: implementat tehnic + testat + documentat
Faza 6.3 — UI vizual minimal peste orchestrator: implementat tehnic + testat + documentat
Installer Windows: NU a început încă
```

## Decizie principală

UI-ul vizual există doar ca strat peste orchestrator. Nu conține logică de business.

Ordinea proiectului este:

```text
Documentație
Core Engine
Rules Engine
TraceabilityCase
Teste automate
Report Engine DOCX
Flux E2E controlat
Runner demonstrativ DOCX
Documentație runner demonstrativ
README principal sincronizat
Contract UI -> engine
Funcție UI de orchestrare testabilă
CLI/UI shell minimal
UI vizual minimal
Installer Windows
```

## Reguli critice validate

1. Gazul ALISOL este auxiliar / consumabil tehnologic.
2. Gazul nu intră niciodată la materii prime alimentare.
3. Unitățile de măsură nu se convertesc automat.
4. Dacă o secțiune nu are date, raportul trebuie să spună explicit acest lucru.
5. Raportul DOCX trebuie să fie narativ și auditabil, nu un Excel copiat în Word.
6. DOCX-ul se generează din TraceabilityCase, nu direct din fișiere.
7. UI-ul nu conține logică de business.
8. Bilanțul preliminar este conservator și nu deduce fluxuri lipsă.
9. Fluxul E2E controlat folosește date sintetice de test, nu UI și nu fișiere operaționale reale.
10. Runnerul demonstrativ folosește dataset sintetic controlat și nu schimbă regulile de business.
11. Documentația runnerului explică explicit că demo-ul nu citește surse operaționale reale.
12. README.md principal reflectă statusul tehnic curent și nu mai conține status vechi de pre-cod.
13. Contractul UI -> engine limitează UI-ul la colectare input, apel engine și afișare succes/eroare.
14. Funcția UI de orchestrare nu citește direct sursele și nu conține logică de business.
15. Documentația UI explică explicit `UiGenerationRequest`, `UiGenerationResult` și `generate_report_from_ui_request()`.
16. CLI/UI shell-ul minimal apelează doar orchestratorul și nu conține logică de business.
17. UI-ul vizual minimal apelează doar orchestratorul și nu conține logică de business.

## Structura repo la checkpoint

```text
TraceAI-Control/
  README.md
  CHECKPOINT.md
  docs/
    UI_ENGINE_CONTRACT.md
  src/
    core/
    rules/
    report/
    ui/
      README.md
      __init__.py
      cli.py
      orchestrator.py
      visual.py
  tests/
    README.md
    test_source_inventory.py
    test_normalized_dataset.py
    test_dataset_validation.py
    test_record_selection.py
    test_run_pipeline.py
    test_case_type_detection.py
    test_run_rules_pipeline.py
    test_traceability_case.py
    test_run_traceability_case.py
    test_docx_minimal.py
    test_e2e_docx_controlled_flow.py
    test_demo_docx_runner.py
    test_ui_orchestrator.py
    test_ui_cli.py
    test_ui_visual.py
  samples/
    README.md
    demo_docx_runner.py
```

## UI vizual minimal implementat

Implementare:

```text
src/ui/visual.py
src/ui/__init__.py
```

Documentație:

```text
src/ui/README.md
README.md
```

Test dedicat:

```text
tests/test_ui_visual.py
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
buton generare raport DOCX
mesaj succes / eroare
```

Funcții testabile:

```text
build_request_from_form_values()
submit_visual_form_values()
run_visual_app()
```

Reguli UI vizual:

```text
nu citește direct surse operaționale
nu clasifică tipuri de caz
nu calculează bilanțuri
nu generează DOCX direct din CSV/XLSX
nu conține logică de business
apelează doar generate_report_from_ui_request()
```

## Testare curentă

Testele unitare și E2E controlate acoperă modulele Core, Rules, TraceabilityCase, bilanț preliminar conservator, Report Engine DOCX, fluxul controlat TraceabilityCase -> DOCX, runnerul demonstrativ, funcția UI de orchestrare, CLI/UI shell-ul minimal și UI-ul vizual minimal:

```text
python -m pytest -q
39 passed
```

## Limită curentă

Nu există încă:

```text
trasabilitate amonte/aval calculată
bilanțuri detaliate / reconciliere operațională completă
branding complet / logo / paginare avansată / cuprins automat
installer
```

## Următorul pas la reluare

Următorul pas corect este:

```text
pregătirea pentru installer Windows sau rafinare strict vizuală UI, fără logică de business nouă
```

Primul cod permis:

```text
src/ui/
tests/
docs/
README.md
```

Regulă importantă:

```text
Nu se adaugă logică de business în UI.
UI-ul vizual trebuie să apeleze același generate_report_from_ui_request().
DOCX rămâne generat din TraceabilityCase, nu direct din fișierele sursă.
Bilanțul preliminar rămâne conservator și nu convertește unități de măsură automat.
```

## Fraza de reluare recomandată

```text
Continuăm de la CHECKPOINT.md cu pregătirea pentru installer Windows sau rafinare strict vizuală UI, fără logică de business nouă.
```
