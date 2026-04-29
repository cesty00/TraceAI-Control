# Teste TraceAI Control

Testele acoperă modulele curente Core, Rules, TraceabilityCase și Report Engine.

## Teste unitare

Fișierele `test_*.py` validează:

- inventarierea surselor;
- normalizarea datasetului;
- validarea datasetului;
- selecția cod/lot;
- rularea Core Pipeline;
- detectarea tipului de caz;
- construirea `TraceabilityCase`;
- popularea `report_tables`;
- bilanțul preliminar conservator;
- generarea DOCX narativ cu tabele Word reale și bilanț preliminar.

## Flux end-to-end controlat

`test_e2e_docx_controlled_flow.py` folosește date sintetice controlate pentru a valida fluxul:

```text
NormalizedDataSet
-> record_selection
-> case_type_detection
-> build_traceability_case
-> generate_minimal_docx_report
-> verificare word/document.xml
```

Scopul testului este să confirme integrarea tehnică dintre Rules Engine, TraceabilityCase și Report Engine fără UI și fără citirea directă a surselor operaționale în Report Engine.

Reguli păstrate:

```text
DOCX se generează din TraceabilityCase.
Bilanțul preliminar este conservator.
Nu se convertesc automat unități de măsură.
Nu se deduce trasabilitate amonte/aval.
```

Rulare:

```bash
python -m pytest -q
```
