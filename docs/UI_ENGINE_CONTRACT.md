# Contract minim UI -> Engine

Acest document definește limita dintre viitorul UI profesional simplu și engine-ul existent TraceAI Control.

## Scop

UI-ul trebuie să permită operatorului să introducă datele minime și să genereze raportul DOCX folosind pipeline-ul existent.

UI-ul nu conține logică de business.

## Input UI minim

UI-ul colectează doar:

```text
source_directory
code
lot
output_docx_path
```

Semnificație:

| Câmp | Descriere |
|---|---|
| `source_directory` | folderul cu sursele oficiale |
| `code` | cod articol/produs |
| `lot` | lot verificat |
| `output_docx_path` | calea raportului DOCX generat |

## Surse acceptate

UI-ul nu selectează fișiere individuale și nu definește surse noi.

Sursele rămân cele oficiale:

```text
trasabilitate_wms.csv
rapoarte productie.csv
nomenclator.xlsx
stoc la moment original.xlsx
```

## Apel engine permis

UI-ul trebuie să facă un singur apel de orchestrare către fluxul existent:

```text
run_traceability_case(source_directory, code, lot)
-> generate_minimal_docx_report(traceability_case, output_docx_path)
```

Echivalent tehnic:

```python
traceability_case = run_traceability_case(source_directory, code, lot)
generate_minimal_docx_report(traceability_case, output_docx_path)
```

## Output UI minim

UI-ul afișează doar mesaje de stare:

```text
Raport generat cu succes: <output_docx_path>
```

sau:

```text
Eroare la generarea raportului: <mesaj eroare>
```

## Reguli stricte

UI-ul NU are voie să:

```text
citească direct CSV/XLSX pentru logică de business
clasifice tipuri de caz
calculeze bilanțuri
modifice TraceabilityCase
recalculeze tabele raportabile
genereze DOCX direct din surse operaționale
convertească unități de măsură
deducă trasabilitate amonte/aval
```

UI-ul are voie doar să:

```text
colecteze inputul minim
apeleze engine-ul existent
afișeze progres simplu
afișeze succes/eroare
deschidă folderul de output, dacă această funcție va fi permisă ulterior
```

## Separare responsabilități

| Strat | Responsabilitate |
|---|---|
| `src/core/` | citire, normalizare, validare, selecție |
| `src/rules/` | detectare caz, TraceabilityCase, reguli, bilanț preliminar |
| `src/report/` | generare DOCX din TraceabilityCase |
| `src/ui/` | colectare input și orchestration-only |

## Contract de eroare minim

UI-ul trebuie să trateze conservator erorile:

```text
folder lipsă
surse lipsă
cod/lot gol
eroare de validare dataset
eroare de generare DOCX
```

UI-ul nu repară automat datele.

## Testare viitoare recomandată

Primul test permis pentru UI nu trebuie să pornească o interfață grafică.

Testul minim recomandat:

```text
funcție de orchestrare UI primește source_directory/code/lot/output_docx_path
apelează engine-ul mock-uit sau controlat
returnează status succes/eroare
nu citește direct sursele
nu conține logică de business
```

## Limită curentă

Acest document definește contractul. Nu implementează încă UI vizual.
