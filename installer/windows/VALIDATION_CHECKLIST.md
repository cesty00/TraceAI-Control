# Checklist validare Windows — TraceAI Control

Acest document definește pașii de validare reală pe o mașină Windows pentru executabilul PyInstaller și installerul Inno Setup.

## Scop

Validarea confirmă că fluxul Windows funcționează cap-coadă:

```text
build_windows.ps1
-> verify_windows_build.ps1
-> build_inno_setup.ps1
-> instalare aplicație
-> pornire UI vizual
-> generare raport DOCX
```

## Mediu validare

Completați înainte de test:

| Câmp | Valoare |
|---|---|
| Data validării |  |
| Operator |  |
| Versiune Windows |  |
| Versiune Python |  |
| Versiune PyInstaller |  |
| Versiune Inno Setup |  |
| Commit testat |  |

## Cerințe înainte de test

Bifați:

```text
[ ] Repo clonat local pe Windows
[ ] Python 3.11+ disponibil
[ ] Dependențele proiectului instalate
[ ] PyInstaller instalat
[ ] Inno Setup 6 instalat
[ ] Sursele oficiale de test sunt disponibile local
```

Surse oficiale așteptate:

```text
trasabilitate_wms.csv
rapoarte productie.csv
nomenclator.xlsx
stoc la moment original.xlsx
```

## 1. Test suite

Comandă:

```powershell
python -m pytest -q
```

Criteriu acceptare:

```text
[ ] Testele trec
[ ] Rezultat așteptat: 39 passed
```

Observații:

```text

```

## 2. Build executabil PyInstaller

Comandă:

```powershell
powershell -ExecutionPolicy Bypass -File .\installer\windows\build_windows.ps1
```

Criteriu acceptare:

```text
[ ] Scriptul rulează fără eroare
[ ] Executabilul este generat
[ ] Există dist\TraceAI-Control\TraceAI-Control.exe
```

Observații:

```text

```

## 3. Verificare artefact build

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

Observații:

```text

```

## 4. Smoke test executabil direct

Comandă:

```powershell
.\dist\TraceAI-Control\TraceAI-Control.exe
```

Criteriu acceptare:

```text
[ ] UI-ul vizual pornește
[ ] Fereastra afișează câmpurile pentru folder surse, cod, lot și output DOCX
[ ] Butonul de generare este vizibil
[ ] Nu apar erori la pornire
```

Observații:

```text

```

## 5. Generare raport DOCX din executabil direct

Pași:

```text
[ ] Selectați folderul cu sursele oficiale
[ ] Introduceți cod articol valid
[ ] Introduceți lot valid
[ ] Selectați output DOCX
[ ] Apăsați generare raport
```

Criteriu acceptare:

```text
[ ] Mesajul de succes este afișat
[ ] Fișierul DOCX este creat
[ ] DOCX-ul se poate deschide în Word / LibreOffice
[ ] Raportul conține secțiuni narative și tabele Word
```

Observații:

```text

```

## 6. Build installer Inno Setup

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
[ ] Installerul este generat
[ ] Există installer\windows\output\TraceAI-Control-Setup.exe
```

Observații:

```text

```

## 7. Instalare aplicație

Comandă / acțiune:

```powershell
.\installer\windows\output\TraceAI-Control-Setup.exe
```

Criteriu acceptare:

```text
[ ] Wizardul Inno Setup pornește
[ ] Aplicația se instalează în Program Files
[ ] Shortcutul din Start Menu este creat
[ ] Shortcutul Desktop este creat dacă a fost selectată opțiunea
[ ] Aplicația poate fi lansată după instalare
```

Observații:

```text

```

## 8. Smoke test aplicație instalată

Pași:

```text
[ ] Porniți aplicația din Start Menu
[ ] Verificați că UI-ul vizual pornește
[ ] Generați un raport DOCX folosind sursele oficiale
[ ] Confirmați că DOCX-ul este creat și se deschide
```

Criteriu acceptare:

```text
[ ] Aplicația instalată funcționează ca executabilul direct
[ ] Nu apar erori de path / fișiere lipsă
[ ] Raportul DOCX este generat corect
```

Observații:

```text

```

## 9. Dezinstalare

Pași:

```text
[ ] Dezinstalați aplicația din Windows Settings / Control Panel
[ ] Verificați eliminarea shortcuturilor
[ ] Verificați eliminarea folderului aplicației, dacă nu există fișiere generate de utilizator în el
```

Observații:

```text

```

## Verdict final

Alegeți unul:

```text
[ ] ACCEPTAT — build și installer validate pe Windows
[ ] RESPINS — necesită corecții
```

Rezumat probleme găsite:

```text

```

## Reguli care nu trebuie încălcate

În timpul validării nu se acceptă workaround-uri care introduc logică nouă în UI sau installer:

```text
UI-ul nu citește direct surse operaționale pentru logică de business
UI-ul nu clasifică tipuri de caz
UI-ul nu calculează bilanțuri
UI-ul nu generează DOCX direct din CSV/XLSX
Installerul nu schimbă Core/Rules/Report Engine
```
