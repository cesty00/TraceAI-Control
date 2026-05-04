# Windows validation result template

Use this file after running:

```text
installer/windows/VALIDATION_CHECKLIST.md
```

## Environment

| Field | Value |
|---|---|
| Validation date |  |
| Operator |  |
| Tested commit |  |
| Branch |  |
| Artifact tested |  |
| Windows version |  |
| Python version |  |
| PyInstaller version |  |
| Inno Setup version |  |

## Expected artifacts

| Artifact | Path | Status |
|---|---|---|
| PyInstaller executable | `dist\\TraceAI-Control\\TraceAI-Control.exe` |  |
| Build metadata | `traceai_build_info.json` |  |
| Inno Setup installer | `installer\\windows\\output\\TraceAI-Control-Setup.exe` |  |
| Diagnostic ZIP generated during smoke test |  |  |
| DOCX generated during smoke test |  |  |
| TSV export generated during smoke test |  |  |

## Step results

| Step | Expected result | Result | Notes |
|---|---|---|---|
| Test suite | `python -m pytest -q` passes, at least 129 passed |  |  |
| PyInstaller build | `build_windows.ps1` completes |  |  |
| Build verification | `verify_windows_build.ps1` confirms executable |  |  |
| Direct executable smoke test | UI opens |  |  |
| UI source preflight | Verifică surse works, no BLOCKER |  |  |
| UI audit checklist preview | Sections render in UI |  |  |
| UI copy/export section | Text/TSV export works |  |  |
| UI Diagnostic ZIP | ZIP is generated with required files |  |  |
| Direct executable DOCX test | DOCX is generated and opens |  |  |
| Inno Setup build | Installer is generated |  |  |
| Installation test | Application installs |  |  |
| Installed app smoke test | UI opens from installed app |  |  |
| Installed app Diagnostic ZIP | ZIP is generated from installed app |  |  |
| Installed app DOCX test | DOCX is generated |  |  |
| Uninstall test | Application uninstalls |  |  |

Use one of:

```text
ACCEPTED
REJECTED
NOT_APPLICABLE
```

## Diagnostic ZIP validation

| File | Status | Notes |
|---|---|---|
| build_info.json |  |  |
| source_inventory.json |  |  |
| preflight.json |  |  |
| audit_checklist_ui.json or audit_checklist_ui_error.json |  |  |
| manifest.json |  |  |
| README.txt |  |  |
| reports/*.docx optional |  |  |

## Report/DOCX validation

| Check | Status | Notes |
|---|---|---|
| Opens in Word/LibreOffice |  |  |
| Contains audit checklist sections |  |  |
| Contains upstream/amonte table |  |  |
| Contains downstream/aval table |  |  |
| Contains production/consumption section |  |  |
| Contains document register |  |  |
| Contains build info |  |  |
| Build commit matches tested artifact |  |  |

## Issues found

| ID | Severity | Description | Reproduction steps | Status |
|---|---|---|---|---|
|  |  |  |  |  |

Severity values:

```text
BLOCKER
MAJOR
MINOR
NOTE
```

## Final verdict

```text
[ ] ACCEPTED - Windows build and installer validated
[ ] REJECTED - fixes required
```

## Final notes

```text

```

## Rules confirmed

```text
[ ] UI does not contain business logic
[ ] UI does not classify case types
[ ] UI does not calculate balances
[ ] UI does not generate DOCX directly from CSV/XLSX
[ ] Installer does not modify Core/Rules/Report Engine
[ ] DOCX and UI use the same audit source of truth
[ ] Diagnostic ZIP is generated through support/UI boundaries
```
