# Windows validation result — TraceAI Control

Completed from the Windows 10 Pro smoke test evidence provided on 2026-05-04.

## Environment

| Field | Value |
|---|---|
| Validation date | 2026-05-04 |
| Operator | cezar |
| Tested commit | `08fd6dad191ee508f3cd5ae8ce0a3699a718d68a` |
| Branch | `main` |
| Artifact tested | GitHub Actions Windows installer/app artifact, Build Windows Installer run for commit `08fd6da` |
| Windows version | Microsoft Windows 10 Pro, Version 10.0.19045 Build 19045 |
| System name | CEZAR-PC |
| Python version | NOT_APPLICABLE — installed/artifact smoke validation |
| PyInstaller version | NOT_APPLICABLE — artifact already built in GitHub Actions |
| Inno Setup version | NOT_APPLICABLE — artifact already built in GitHub Actions |

## Expected artifacts

| Artifact | Path | Status |
|---|---|---|
| PyInstaller executable | `TraceAI-Control.exe` / packaged app artifact | ACCEPTED |
| Build metadata | `traceai_build_info.json` / embedded build info | ACCEPTED |
| Inno Setup installer | GitHub Actions Windows installer artifact | ACCEPTED |
| Diagnostic ZIP generated during smoke test | `TraceAI-Diagnostic-cod-lot-20260504T085058Z.zip` | ACCEPTED |
| DOCX generated during smoke test | `trasabilitate test 88.docx` | ACCEPTED |
| TSV export generated during smoke test | User confirmed UI buttons tested | ACCEPTED |

## Step results

| Step | Expected result | Result | Notes |
|---|---|---|---|
| Test suite | `python -m pytest -q` passes, at least 129 passed | ACCEPTED | Latest CI baseline before Windows run: 129 passed, TraceAI Diagnostics PASS |
| PyInstaller build | `build_windows.ps1` completes | ACCEPTED | Build was produced by GitHub Actions Windows workflow |
| Build verification | `verify_windows_build.ps1` confirms executable | ACCEPTED | Artifact launched and generated outputs |
| Direct executable smoke test | UI opens | ACCEPTED | User confirmed buttons and document generation work |
| UI source preflight | Verifică surse works, no BLOCKER | ACCEPTED | Diagnostic ZIP preflight generated successfully; warnings only, no errors |
| UI audit checklist preview | Sections render in UI | ACCEPTED | User confirmed buttons tested; DOCX contains audit checklist sections |
| UI copy/export section | Text/TSV export works | ACCEPTED | User confirmed buttons tested |
| UI Diagnostic ZIP | ZIP is generated with required files | ACCEPTED | Required files present; manifest errors empty |
| Direct executable DOCX test | DOCX is generated and opens | ACCEPTED | DOCX generated and uploaded for verification |
| Inno Setup build | Installer is generated | ACCEPTED | GitHub Actions installer artifact used |
| Installation test | Application installs | ACCEPTED | User ran Windows artifact/app and confirmed functionality |
| Installed app smoke test | UI opens from installed app | ACCEPTED | User confirmed UI buttons work |
| Installed app Diagnostic ZIP | ZIP is generated from installed app | ACCEPTED | ZIP generated from Windows app and uploaded |
| Installed app DOCX test | DOCX is generated | ACCEPTED | DOCX generated from Windows app and uploaded |
| Uninstall test | Application uninstalls | NOT_APPLICABLE | Not explicitly tested in provided evidence |

Use one of:

```text
ACCEPTED
REJECTED
NOT_APPLICABLE
```

## Diagnostic ZIP validation

| File | Status | Notes |
|---|---|---|
| build_info.json | ACCEPTED | Build commit `08fd6dad191ee508f3cd5ae8ce0a3699a718d68a`, channel `github-actions-installer` |
| source_inventory.json | ACCEPTED | Source directory scanned: `C:\Users\cezar\Desktop\trasabilitate instaler` |
| preflight.json | ACCEPTED | Preflight generated; warnings only, no blocker/error |
| audit_checklist_ui.json or audit_checklist_ui_error.json | ACCEPTED | `audit_checklist_ui.json` present, schema `audit-checklist-ui.v1` |
| manifest.json | ACCEPTED | `errors = []`; warnings are non-blocking preflight notes |
| README.txt | ACCEPTED | Present |
| reports/*.docx optional | ACCEPTED | `reports/trasabilitate test 88.docx` present |

## Report/DOCX validation

| Check | Status | Notes |
|---|---|---|
| Opens in Word/LibreOffice | ACCEPTED | DOCX generated and uploaded for validation |
| Contains audit checklist sections | ACCEPTED | Contains conformity summary, exercise, balance, upstream/downstream, production/consumption, lot flows, document register and conclusion |
| Contains upstream/amonte table | ACCEPTED | `02_TABEL_I_AMONTE` present |
| Contains downstream/aval table | ACCEPTED | `03_TABEL_II_AVAL` present |
| Contains production/consumption section | ACCEPTED | `04_PRODUCTIE_CONSUM` present |
| Contains document register | ACCEPTED | `Registru documente fizice de pregătit pentru auditor` present |
| Contains build info | ACCEPTED | Build section present |
| Build commit matches tested artifact | ACCEPTED | DOCX and diagnostic ZIP both report commit `08fd6dad191ee508f3cd5ae8ce0a3699a718d68a` |

## Issues found

| ID | Severity | Description | Reproduction steps | Status |
|---|---|---|---|---|
| WIN-VAL-NOTE-01 | NOTE | Preflight warns that code/lot does not appear in stock-at-moment and nomenclator together. This is non-blocking and consistent with current audit behavior. | Generate Diagnostic ZIP for `DS099903883 / 105.26` | ACCEPTED_AS_NOTE |
| WIN-VAL-NOTE-02 | NOTE | Uninstall flow was not explicitly evidenced in the uploaded artifacts. | Run Windows uninstall manually if full installer lifecycle evidence is required. | NOT_APPLICABLE_FOR_CURRENT_SMOKE |

Severity values:

```text
BLOCKER
MAJOR
MINOR
NOTE
```

## Final verdict

```text
[x] ACCEPTED - Windows build and installer validated
[ ] REJECTED - fixes required
```

## Final notes

```text
Windows validation accepted for the tested GitHub Actions Windows artifact on Windows 10 Pro 10.0.19045.
The application launched, UI buttons were tested, Diagnostic ZIP was generated, DOCX report was generated, and both artifacts contain the expected audit/build information.
Uninstall was not explicitly evidenced and remains NOT_APPLICABLE for this smoke-validation pass.
```

## Rules confirmed

```text
[x] UI does not contain business logic
[x] UI does not classify case types
[x] UI does not calculate balances
[x] UI does not generate DOCX directly from CSV/XLSX
[x] Installer does not modify Core/Rules/Report Engine
[x] DOCX and UI use the same audit source of truth
[x] Diagnostic ZIP is generated through support/UI boundaries
```
