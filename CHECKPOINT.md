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
Faza 7.0 — Pregătire installer Windows: script PyInstaller + documentație integrate
Faza 7.1 — Script Windows build rafinat: entry point explicit + verificare înainte de build
Faza 7.2 — Verificare build Windows: script PowerShell + documentație integrate
Faza 7.3 — Pregătire installer Inno Setup: script .iss + build PowerShell + documentație integrate
Faza 7.4 — Checklist validare Windows: integrat
Installer Windows complet: pregătit tehnic, dar NEVALIDAT încă pe Windows real
```

## Decizie principală

UI-ul vizual există doar ca strat peste orchestrator. Installerul și verificarea buildului nu introduc logică de business.

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
Pregătire installer Windows
Rafinare script Windows build
Verificare build Windows
Pregătire installer Inno Setup
Checklist validare Windows
Validare reală Windows
Icon / semnare / CI Windows
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
18. Scriptul Windows build pornește de la UI-ul vizual minimal și nu schimbă engine-ul.
19. Scriptul Windows build folosește entry point explicit `src\ui\visual.py` și verifică existența lui înainte de build.
20. Scriptul de verificare Windows build verifică doar artefactul rezultat și nu pornește automat UI-ul / engine-ul.
21. Scriptul Inno Setup împachetează executabilul PyInstaller existent și nu introduce logică de business.
22. Checklistul de validare Windows definește pașii reali de acceptare fără workaround-uri în UI sau installer.

## Structura repo la checkpoint

```text
TraceAI-Control/
  README.md
  CHECKPOINT.md
  docs/
    UI_ENGINE_CONTRACT.md
  installer/
    windows/
      README.md
      TraceAI-Control.iss
      VALIDATION_CHECKLIST.md
      build_inno_setup.ps1
      build_windows.ps1
      verify_windows_build.ps1
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

## Build, verificare, installer și checklist Windows integrate

Implementare:

```text
installer/windows/build_windows.ps1
installer/windows/verify_windows_build.ps1
installer/windows/TraceAI-Control.iss
installer/windows/build_inno_setup.ps1
installer/windows/VALIDATION_CHECKLIST.md
```

Documentație:

```text
installer/windows/README.md
README.md
```

Build executabil PyInstaller:

```powershell
powershell -ExecutionPolicy Bypass -File .\installer\windows\build_windows.ps1
```

Build fără teste, doar dacă testele au fost deja rulate separat:

```powershell
powershell -ExecutionPolicy Bypass -File .\installer\windows\build_windows.ps1 -SkipTests
```

Verificare build după generarea executabilului:

```powershell
powershell -ExecutionPolicy Bypass -File .\installer\windows\verify_windows_build.ps1
```

Build installer Inno Setup:

```powershell
powershell -ExecutionPolicy Bypass -File .\installer\windows\build_inno_setup.ps1
```

Checklist validare Windows:

```text
installer/windows/VALIDATION_CHECKLIST.md
```

Entry point PyInstaller:

```text
src\ui\visual.py
```

Output executabil așteptat:

```text
dist\TraceAI-Control\TraceAI-Control.exe
```

Output installer așteptat:

```text
installer\windows\output\TraceAI-Control-Setup.exe
```

Checklistul acoperă:

```text
test suite
build executabil PyInstaller
verificare artefact build
smoke test executabil direct
generare raport DOCX din executabil direct
build installer Inno Setup
instalare aplicație
smoke test aplicație instalată
dezinstalare
verdict final ACCEPTAT / RESPINS
```

Limitări installer curente:

```text
nu există încă semnare executabil
nu există icon final
nu există pipeline CI Windows
nu există validare reală finalizată pe o mașină Windows
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
validare reală installer Windows
semnare executabil
icon final
pipeline CI Windows
```

## Următorul pas la reluare

Următorul pas corect este:

```text
rularea checklistului de validare pe o mașină Windows reală și marcarea rezultatului ACCEPTAT / RESPINS
```

Primul cod permis după validare:

```text
installer/windows/VALIDATION_CHECKLIST.md
installer/windows/README.md
README.md
CHECKPOINT.md
```

Regulă importantă:

```text
Nu se adaugă logică de business în installer.
Installerul trebuie să pornească UI-ul vizual minimal existent.
UI-ul vizual trebuie să apeleze același generate_report_from_ui_request().
DOCX rămâne generat din TraceabilityCase, nu direct din fișierele sursă.
Bilanțul preliminar rămâne conservator și nu convertește unități de măsură automat.
```

## Fraza de reluare recomandată

```text
Continuăm de la CHECKPOINT.md cu rularea checklistului de validare pe o mașină Windows reală și marcarea rezultatului ACCEPTAT / RESPINS.
```
