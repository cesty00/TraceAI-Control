# Local diagnostic bundle

TraceAI Control can generate a local support ZIP with the state seen by the
installed application.

## Command

```powershell
python -m src.support.diagnostic_bundle "C:\path\to\sources" --code DS099903883 --lot 105.26 --output TraceAI-Diagnostic.zip
```

Optional: include a generated DOCX report:

```powershell
python -m src.support.diagnostic_bundle "C:\path\to\sources" --code DS099903883 --lot 105.26 --output TraceAI-Diagnostic.zip --report "C:\path\to\raport.docx"
```

## ZIP contents

The ZIP contains best-effort support artifacts:

```text
manifest.json
README.txt
build_info.json
source_inventory.json
preflight.json
audit_checklist_ui.json
reports/<generated report>.docx   optional
```

If a layer fails, the ZIP still includes the other files and writes an error JSON,
for example:

```text
audit_checklist_ui_error.json
```

## Purpose

The bundle helps compare local behavior with GitHub diagnostics. It answers:

```text
Which build generated the output?
Which source files were found?
What did preflight report?
What audit UI payload was produced?
Were there warnings or blockers?
```

This is a support and observability artifact. It does not modify source files.
