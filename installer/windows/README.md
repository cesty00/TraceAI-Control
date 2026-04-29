# Installer Windows — TraceAI Control

Acest folder pregătește pașii pentru construirea, verificarea și împachetarea unui executabil Windows pentru TraceAI Control.

## Status

Pregătire installer Windows integrată:

```text
script PowerShell de build PyInstaller
entry point PyInstaller explicit
verificare existență entry point înainte de build
script PowerShell de verificare artefact build
script Inno Setup pentru installer complet
script PowerShell pentru rularea Inno Setup Compiler
instrucțiuni de rulare
reguli de validare manuală
fără schimbări în Core/Rules/Report/UI business boundary
```

Installerul Inno Setup este pregătit tehnic, dar trebuie validat pe o mașină Windows cu Inno Setup instalat.

## Principiu

Executabilul Windows pornește UI-ul vizual minimal:

```text
src\ui\visual.py
```

În dezvoltare, UI-ul poate fi pornit cu:

```powershell
python -m src.ui.visual
```

UI-ul vizual rămâne doar strat de orchestrare peste:

```text
generate_report_from_ui_request()
```

Installerul nu introduce logică de business.

## Cerințe locale

Pe mașina Windows de build:

```text
Python 3.11+ recomandat
pip
virtualenv / venv
pyinstaller
Inno Setup 6
```

Instalare PyInstaller:

```powershell
python -m pip install pyinstaller
```

Inno Setup trebuie instalat local, astfel încât compilatorul să existe de obicei la una dintre căile:

```text
C:\Program Files (x86)\Inno Setup 6\ISCC.exe
C:\Program Files\Inno Setup 6\ISCC.exe
```

## 1. Build executabil PyInstaller

Din rădăcina repo-ului:

```powershell
powershell -ExecutionPolicy Bypass -File .\installer\windows\build_windows.ps1
```

Pentru rulare fără teste, doar când testele au fost deja rulate separat:

```powershell
powershell -ExecutionPolicy Bypass -File .\installer\windows\build_windows.ps1 -SkipTests
```

Output așteptat:

```text
dist/TraceAI-Control/TraceAI-Control.exe
```

## 2. Verificare build PyInstaller

După build, rulează:

```powershell
powershell -ExecutionPolicy Bypass -File .\installer\windows\verify_windows_build.ps1
```

Scriptul de verificare:

```text
verifică existența folderului dist\TraceAI-Control
verifică existența executabilului dist\TraceAI-Control\TraceAI-Control.exe
verifică faptul că executabilul nu este gol
afișează path-ul și dimensiunea executabilului
afișează pașii manuali de smoke test
```

Scriptul de verificare nu pornește automat UI-ul și nu apelează engine-ul.

## 3. Build installer Inno Setup

Fișiere:

```text
installer/windows/TraceAI-Control.iss
installer/windows/build_inno_setup.ps1
```

După ce executabilul PyInstaller există, rulează:

```powershell
powershell -ExecutionPolicy Bypass -File .\installer\windows\build_inno_setup.ps1
```

Dacă `ISCC.exe` nu este detectat automat:

```powershell
powershell -ExecutionPolicy Bypass -File .\installer\windows\build_inno_setup.ps1 -InnoSetupCompilerPath "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
```

Output așteptat:

```text
installer/windows/output/TraceAI-Control-Setup.exe
```

Installerul Inno Setup:

```text
instalează conținutul din dist\TraceAI-Control
creează shortcut în Start Menu
poate crea shortcut pe Desktop
poate lansa aplicația după instalare
```

## Ce face scriptul de build PyInstaller

Scriptul `build_windows.ps1`:

```text
setează repo root
verifică existența entry point-ului src\ui\visual.py
rulează testele cu python -m pytest -q, dacă nu este folosit -SkipTests
verifică PyInstaller
curăță artefactele build/dist vechi
rulează PyInstaller cu entry point explicit
verifică existența executabilului rezultat
```

Entry point PyInstaller:

```text
src\ui\visual.py
```

Output verificat:

```text
dist\TraceAI-Control\TraceAI-Control.exe
```

## Validare manuală după build

1. Pornește executabilul sau aplicația instalată.
2. Verifică faptul că apare formularul UI.
3. Selectează folderul cu sursele oficiale.
4. Completează codul articol și lotul.
5. Alege calea raportului DOCX.
6. Apasă generare.
7. Confirmă că raportul DOCX este creat.

Executabil direct:

```powershell
.\dist\TraceAI-Control\TraceAI-Control.exe
```

Installer:

```powershell
.\installer\windows\output\TraceAI-Control-Setup.exe
```

## Reguli păstrate

Executabilul și installerul nu trebuie să introducă logică nouă:

```text
nu citește direct surse operaționale în UI
nu clasifică tipuri de caz în UI
nu calculează bilanțuri în UI
nu generează DOCX direct din CSV/XLSX
nu convertește unități de măsură
nu deduce trasabilitate amonte/aval
```

## Limitări curente

Acest folder nu include încă:

```text
semnare executabil
icon final
pipeline CI pentru build Windows
verificare automată pe Windows prin CI
validare reală pe o mașină Windows
```
