# TraceAI Control — Modul Trasabilitate

## Scop

TraceAI Control — Modul Trasabilitate este aplicația destinată generării unui raport DOCX auditabil pentru trasabilitatea unui articol și lot.

Utilizatorul introduce:

```text
Cod articol
Lot
```

Aplicația analizează fișierele operaționale zilnice și generează un raport narativ, clar și verificabil.

## Surse oficiale

Aplicația folosește doar:

```text
trasabilitate_wms.csv
rapoarte productie.csv
nomenclator.xlsx
stoc la moment original.xlsx
```

## Surse excluse

Aplicația nu folosește:

```text
WME / fișă magazie
PP-03
OperatorView
patch-uri vechi
fișiere debug
```

## Tipuri de cazuri suportate

Aplicația trebuie să detecteze automat tipul cazului:

```text
FINISHED_PRODUCT
RAW_MATERIAL
WMS_ONLY_PRODUCT
UNKNOWN
```

## Livrabil principal

Livrabilul principal este:

```text
Raport DOCX de trasabilitate
```

Excel-ul nu este obiectivul principal.

## Stil raport

Raportul trebuie să fie:

```text
narativ
auditabil
clar
adaptat complexității cazului
```

Nu trebuie să fie un Excel copiat în Word.

## Reguli importante

- WMS este sursa pentru mișcări, documente, parteneri, loturi, cantități și documente comerciale.
- PRD este sursa pentru producție, comenzi și consumuri.
- Document intrare, Numar comanda și Document comanda se iau din WMS.
- GAZ ALIMENTAR ALISOL este material auxiliar / consumabil tehnologic.
- Gazul nu este materie primă alimentară.
- Unitățile de măsură se păstrează așa cum apar în surse.
- Dacă nu există date într-o secțiune, raportul trebuie să spună explicit acest lucru.

## Faza curentă

Faza curentă este documentarea funcțională și arhitecturală.

Nu se dezvoltă cod până la acceptarea documentației de bază.
