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
| Windows version |  |
| Python version |  |
| PyInstaller version |  |
| Inno Setup version |  |

## Expected artifacts

| Artifact | Path | Status |
|---|---|---|
| PyInstaller executable | `dist\\TraceAI-Control\\TraceAI-Control.exe` |  |
| Inno Setup installer | `installer\\windows\\output\\TraceAI-Control-Setup.exe` |  |
| DOCX generated during smoke test |  |  |

## Step results

| Step | Expected result | Result | Notes |
|---|---|---|---|
| Test suite | `python -m pytest -q` passes |  |  |
| PyInstaller build | `build_windows.ps1` completes |  |  |
| Build verification | `verify_windows_build.ps1` confirms executable |  |  |
| Direct executable smoke test | UI opens |  |  |
| Direct executable DOCX test | DOCX is generated |  |  |
| Inno Setup build | installer is generated |  |  |
| Installation test | application installs |  |  |
| Installed app smoke test | UI opens from installed app |  |  |
| Installed app DOCX test | DOCX is generated |  |  |
| Uninstall test | application uninstalls |  |  |

Use one of:

```text
ACCEPTED
REJECTED
NOT_APPLICABLE
```

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
[ ] DOCX is generated through TraceabilityCase
```
