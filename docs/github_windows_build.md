# GitHub Windows app build

This workflow is for users who do not build locally from source and only install
or run packaged artifacts.

## Workflow

GitHub Actions workflow:

```text
Windows App Build
.github/workflows/windows-app-build.yml
```

It runs on Windows and produces a downloadable ZIP artifact containing the app:

```text
TraceAI-Control-Windows-<commit>.zip
```

## What it does

```text
1. checks out the repository
2. installs Python and PyInstaller
3. runs tests
4. runs scripts/build_local_app.py with GITHUB_SHA
5. generates traceai_build_info.json
6. bundles traceai_build_info.json into the app
7. uploads TraceAI-Control-Windows-<commit>.zip as a GitHub Actions artifact
```

## How to use

1. Open GitHub repository.
2. Go to `Actions`.
3. Select `Windows App Build`.
4. Click `Run workflow`.
5. Wait for success.
6. Open the completed workflow run.
7. Download artifact `TraceAI-Control-Windows-<commit>`.
8. Extract the ZIP locally.
9. Run the executable from the extracted folder.

## Expected DOCX build information

Reports generated from this artifact should show the real GitHub commit:

```text
Commit build: <full GitHub SHA>
Canal build: github-actions
```

They should not show:

```text
Commit build: UNKNOWN
```
