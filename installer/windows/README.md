# Installer Windows — TraceAI Control

Acest folder pregătește pașii pentru construirea unui executabil Windows pentru TraceAI Control.

## Status

Pregătire installer rafinată:

```text
script PowerShell de build
entry point PyInstaller explicit
verificare existență entry point înainte de build
instrucțiuni de rulare
reguli de validare manuală
fără schimbări în Core/Rules/Report/UI business boundary
```

Installerul complet nu este încă finalizat.

## Principiu

Executabilul Windows trebuie să pornească UI-ul vizual minimal:

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

## Cerințe locale

Pe mașina Windows de build:

```text
Python 3.11+ recomandat
pip
virtualenv / venv
pyinstaller
```

Instalare PyInstaller:

```powershell
python -m pip install pyinstaller
```

## Build

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

## Ce face scriptul

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

1. Pornește executabilul:

```powershell
.\dist\TraceAI-Control\TraceAI-Control.exe
```

2. Verifică faptul că apare formularul UI.
3. Selectează folderul cu sursele oficiale.
4. Completează codul articol și lotul.
5. Alege calea raportului DOCX.
6. Apasă generare.
7. Confirmă că raportul DOCX este creat.

## Reguli păstrate

Executabilul nu trebuie să introducă logică nouă:

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
installer MSI/NSIS/Inno Setup
pipeline CI pentru build Windows
verificare automată pe Windows
```
