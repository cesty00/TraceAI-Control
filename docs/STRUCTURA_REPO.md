# Structură repo — TraceAI Control Modul Trasabilitate

Structura inițială este intenționat simplă.

```text
TraceAI-Control/
  README.md
  docs/
    SPECIFICATIE_FUNCTIONALA.md
    TESTE_VALIDATE.md
    RAPORT_DOCX_MODEL.md
    ARHITECTURA.md
    TRACEABILITY_CASE.md
    ROADMAP.md
    STRUCTURA_REPO.md
  src/
    core/
    rules/
    report/
    ui/
  tests/
  samples/
```

## docs/

Conține documentația oficială a proiectului.

Nu conține cod.

## src/core/

Va conține Core Engine:

- citire fișiere;
- normalizare date;
- normalizare cantități;
- păstrare unități de măsură;
- pregătire dataset intern.

## src/rules/

Va conține Rules Engine:

- detectare case_type;
- clasificare componente;
- regulă gaz;
- bilanțuri;
- AVAL MP;
- observații tehnice;
- construire TraceabilityCase.

## src/report/

Va conține Report Engine:

- generare DOCX;
- tabele;
- concluzii;
- anexe;
- semnături.

Report Engine primește TraceabilityCase și nu citește direct fișiere sursă.

## src/ui/

Va conține interfața aplicației.

UI-ul nu conține logică de business.

## tests/

Va conține testele automate pentru cele 7 cazuri validate.

Testele verifică TraceabilityCase înainte de DOCX.

## samples/

Va conține eventual date de test anonimizate sau fixture-uri mici.

Fișierele operaționale reale nu trebuie încărcate fără decizie explicită.

## Regula de proiect

```text
Documentație înainte de cod.
Core înainte de UI.
Teste înainte de installer.
TraceabilityCase înainte de DOCX.
```
