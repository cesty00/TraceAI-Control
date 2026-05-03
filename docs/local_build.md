# Local build workflow

This workflow creates a local TraceAI Control build that includes build metadata.
The generated app can then show the real commit in the UI and in generated DOCX
reports.

## Metadata-only check

```powershell
python scripts/build_local_app.py --metadata-only
```

This writes:

```text
build/metadata/traceai_build_info.json
```

Example payload:

```json
{
  "app_version": "0.5.0",
  "build_commit": "184c75645dd17d58d6a47e82fdce68c3472b4631",
  "build_date": "2026-05-03T15:00:00+00:00",
  "build_channel": "local-build"
}
```

## Build app with PyInstaller

Install PyInstaller if needed:

```powershell
pip install pyinstaller
```

Build the visual app:

```powershell
python scripts/build_local_app.py
```

The script:

```text
1. removes build/ and dist/ unless --no-clean is used
2. generates build/metadata/traceai_build_info.json
3. runs PyInstaller
4. includes traceai_build_info.json in the bundle
5. copies traceai_build_info.json next to the onedir executable for inspection
```

## Useful options

```powershell
python scripts/build_local_app.py --version 0.5.1 --channel local-build
python scripts/build_local_app.py --commit 184c75645dd17d58d6a47e82fdce68c3472b4631
python scripts/build_local_app.py --onefile
python scripts/build_local_app.py --metadata-only
```

## Expected result in DOCX

The generated DOCX should not show:

```text
Commit build: UNKNOWN
```

It should show the real build commit from `traceai_build_info.json`.
