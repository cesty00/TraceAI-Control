# Checklist validare Windows — TraceAI Control

Acest document definește pașii de validare reală pe Windows pentru executabilul PyInstaller, installerul Inno Setup și aplicația instalată.

## Scop

Validarea confirmă fluxul Windows cap-coadă:

```text
GitHub/Local Windows build
-> executabil PyInstaller
-> installer Inno Setup
-> aplicație instalată
-> UI vizual
-> verificare surse
-> preview audit checklist
-> diagnostic ZIP
-> raport DOCX
```

## Mediu validare

| Câmp | Valoare |
|---|---|
| Data validării |  |
| Operator |  |
| Versiune Windows |  |
| Versiune Python |  |
| Versiune PyInstaller |  |
| Versiune Inno Setup |  |
| Commit testat |  |
| Artifact testat |  |

## Cerințe înainte de test

```text
[ ] Repo clonat local pe Windows sau artifact Windows descărcat din GitHub Actions
[ ] Python 3.11+ disponibil pentru validare locală repo, dacă se testează build local
[ ] Dependențele proiectului instalate, dacă se testează build local
[ ] PyInstaller instalat, dacă se testează build local
[ ] Inno Setup 6 instalat, dacă se testează installer local
[ ] Sursele oficiale de test sunt disponibile local
```

Surse oficiale acceptate prin source discovery:

```text
trasabilitate_wms.csv / trasabilitate_wms.zip
raport_productie.csv / rapoarte productie.csv / rapoarte_productie.csv
nomenclator.xlsx
stoc_la_moment_original.xlsx / stoc la moment original.xlsx
```

Caz de referință:

```text
cod = DS099903883
lot = 105.26
```

## 1. Test suite

Comandă:

```powershell
python -m pytest -q
```

Criteriu acceptare:

```text
[ ] Testele trec
[ ] Rezultat minim așteptat: 129 passed
```

## 2. Build executabil PyInstaller

Comandă:

```powershell
powershell -ExecutionPolicy Bypass -File .\installer\windows\build_windows.ps1
```

Criteriu acceptare:

```text
[ ] Scriptul rulează fără eroare
[ ] Există dist\TraceAI-Control\TraceAI-Control.exe
[ ] Există traceai_build_info.json în artifact/build
[ ] build_commit corespunde commitului testat
```

## 3. Verificare artifact build

Comandă:

```powershell
powershell -ExecutionPolicy Bypass -File .\installer\windows\verify_windows_build.ps1
```

Criteriu acceptare:

```text
[ ] Folderul dist\TraceAI-Control există
[ ] Executabilul dist\TraceAI-Control\TraceAI-Control.exe există
[ ] Executabilul nu este gol
[ ] Scriptul afișează pașii manuali de smoke test
```

## 4. Smoke test executabil direct

Comandă:

```powershell
.\dist\TraceAI-Control\TraceAI-Control.exe
```

Criteriu acceptare:

```text
[ ] UI-ul vizual pornește
[ ] Fereastra afișează câmpurile: folder surse, cod, lot, output DOCX, output Diagnostic ZIP
[ ] Butoanele sunt vizibile: Verifică surse, Previzualizează audit checklist, Generează Diagnostic ZIP, Generează raport DOCX
[ ] Nu apar erori la pornire
```

## 5. Verificare surse din UI

Pași:

```text
[ ] Selectați folderul cu sursele oficiale
[ ] Introduceți cod DS099903883
[ ] Introduceți lot 105.26
[ ] Apăsați Verifică surse
```

Criteriu acceptare:

```text
[ ] Rezultatul apare în UI
[ ] Statusul nu este BLOCKER
[ ] Sursele WMS/PRD/Nomenclator/Stoc sunt raportate cu status OK sau warning explicabil
```

## 6. Preview audit checklist din UI

Pași:

```text
[ ] Apăsați Previzualizează audit checklist
[ ] Selectați secțiuni din lista din stânga
[ ] Verificați afișarea detaliilor/tabelelor
[ ] Testați Copiază text, Copiază TSV și Exportă TSV pentru o secțiune tabelară
```

Criteriu acceptare:

```text
[ ] Secțiunile apar în ordinea audit-checklist-ui.v1
[ ] Datele pentru DS099903883 / 105.26 se afișează
[ ] Exportul TSV se creează corect
[ ] UI-ul nu se blochează
```

## 7. Diagnostic ZIP din UI

Pași:

```text
[ ] Alegeți output Diagnostic ZIP
[ ] Apăsați Generează Diagnostic ZIP
[ ] Deschideți ZIP-ul generat
```

Criteriu acceptare:

```text
[ ] ZIP-ul este creat
[ ] build_info.json există
[ ] source_inventory.json există
[ ] preflight.json există
[ ] audit_checklist_ui.json există sau audit_checklist_ui_error.json explică problema
[ ] manifest.json există
[ ] README.txt există
[ ] manifest errors este gol sau conține doar blocaje reale explicabile
[ ] Dacă DOCX-ul opțional lipsește, UI afișează notă clară și ZIP-ul se generează fără DOCX
```

## 8. Generare raport DOCX din executabil direct

Pași:

```text
[ ] Selectați output DOCX
[ ] Apăsați Generează raport DOCX
[ ] Deschideți raportul în Word / LibreOffice
```

Criteriu acceptare:

```text
[ ] Mesajul de succes este afișat
[ ] Fișierul DOCX este creat
[ ] DOCX-ul se deschide
[ ] Raportul conține audit checklist complet și tabele Word
[ ] Build info din DOCX conține commitul testat
```

## 9. Build installer Inno Setup

Comandă:

```powershell
powershell -ExecutionPolicy Bypass -File .\installer\windows\build_inno_setup.ps1
```

Dacă Inno Setup nu este detectat automat:

```powershell
powershell -ExecutionPolicy Bypass -File .\installer\windows\build_inno_setup.ps1 -InnoSetupCompilerPath "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
```

Criteriu acceptare:

```text
[ ] Scriptul rulează fără eroare
[ ] Există installer\windows\output\TraceAI-Control-Setup.exe
```

## 10. Instalare aplicație

```powershell
.\installer\windows\output\TraceAI-Control-Setup.exe
```

Criteriu acceptare:

```text
[ ] Wizardul pornește
[ ] Aplicația se instalează în Program Files sau folderul ales
[ ] Shortcutul din Start Menu este creat
[ ] Shortcutul Desktop este creat dacă a fost selectată opțiunea
[ ] Aplicația poate fi lansată după instalare
```

## 11. Smoke test aplicație instalată

Repetați pe aplicația instalată:

```text
[ ] Verifică surse
[ ] Previzualizează audit checklist
[ ] Generează Diagnostic ZIP
[ ] Generează raport DOCX
```

Criteriu acceptare:

```text
[ ] Aplicația instalată funcționează ca executabilul direct
[ ] Nu apar erori de path / fișiere lipsă
[ ] ZIP-ul diagnostic este creat
[ ] DOCX-ul este generat corect
[ ] Build info indică artifactul/commitul instalat
```

## 12. Dezinstalare

```text
[ ] Dezinstalați aplicația din Windows Settings / Control Panel
[ ] Verificați eliminarea shortcuturilor
[ ] Verificați eliminarea folderului aplicației, dacă nu există fișiere generate de utilizator în el
```

## Verdict final

```text
[ ] ACCEPTAT — build și installer validate pe Windows
[ ] RESPINS — necesită corecții
```

Rezumat probleme găsite:

```text

```

## Reguli care nu trebuie încălcate

```text
UI-ul nu citește direct surse operaționale pentru logică de business
UI-ul nu clasifică tipuri de caz
UI-ul nu calculează bilanțuri
UI-ul nu generează DOCX direct din CSV/XLSX
Installerul nu schimbă Core/Rules/Report Engine
DOCX și UI folosesc aceeași sursă audit
```
