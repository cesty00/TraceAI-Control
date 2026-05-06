# UI-PERF-01A — Plan de măsurare a performanței UI

## Scope

Acest document definește un plan docs-only pentru măsurarea timpilor de răspuns ai acțiunilor principale din UI.

Acest stage măsoară și documentează.
Nu optimizează aplicația.
Nu schimbă aplicația.
Nu schimbă engine.
Nu schimbă UI.
Nu schimbă rendererul DOCX.
Nu schimbă tests.
Nu schimbă workflow-uri.
Nu schimbă DTO/JSON contracts.
Nu schimbă calculations.
Nu schimbă source mappings.
Nu schimbă verdict rules.
Nu schimbă extraction logic.
Nu schimbă unit handling.
Nu schimbă `CHECKPOINT.md` sau `README.md`.

Acest document nu reprezintă release claim.
Nu reprezintă product-stage DONE claim.

## 1. Scopul măsurării

Scopul acestui plan este să definească modul în care măsurăm timpul de răspuns al acțiunilor relevante din UI pentru operator.

Acest micro-stage nu introduce optimizări și nu validează performanța finală a aplicației.
El stabilește doar metoda de măsurare, câmpurile de înregistrare și interpretarea rezultatelor observate.

## 2. Acțiuni UI măsurate

Acțiunile care trebuie măsurate sunt:

- pornire aplicație, dacă se decide relevant pentru cazul curent;
- selectare folder surse;
- verificare surse / preflight;
- preview / audit checklist;
- generare raport DOCX;
- generare Diagnostic ZIP;
- flux complet end-to-end.

## 3. Metrice înregistrate

Pentru fiecare măsurare trebuie înregistrate cel puțin următoarele câmpuri:

- start timestamp;
- end timestamp;
- durată în secunde;
- cod produs;
- lot;
- număr surse detectate;
- dimensiune aproximativă input;
- rezultat: `success` / `warning` / `error`;
- tip eroare, dacă există;
- output generat;
- observații operator.

## 4. Cazuri inițiale recomandate

Cazurile inițiale pentru care se recomandă măsurarea sunt:

- `DS099903883` / lot `105.26`;
- caz cu `Data Quality: ERROR`;
- caz fără matching records;
- caz cu sursă coruptă sau necitibilă;
- caz complet, dacă există fixture sau surse disponibile.

## 5. Praguri orientative, neblocante

Pragurile de mai jos sunt orientative și nu blochează singure release-ul sau pilotul:

- preflight sub `5` secunde;
- preview sub `10` secunde;
- DOCX sub `15` secunde;
- Diagnostic ZIP sub `5` secunde;
- flux complet sub `30` secunde pentru un caz normal.

Depășirea acestor praguri trebuie notată și interpretată în context, nu tratată automat ca blocker.

## 6. Metodă de măsurare

Pentru fiecare acțiune măsurată:

1. se notează starea inițială a cazului și inputurile folosite;
2. se înregistrează `start timestamp` imediat înainte de acțiune;
3. se înregistrează `end timestamp` imediat după finalizarea acțiunii sau după apariția erorii;
4. se calculează durata în secunde;
5. se consemnează output-ul produs și rezultatul observat;
6. se notează orice warning, eroare sau observație operator.

Pentru fluxul end-to-end, măsurarea începe înainte de selectarea folderului și se încheie după ultimul output relevant pentru caz.

## 7. Interpretarea rezultatelor

Acest document nu declară performanța aplicației ca validată.

Măsurătorile reale vor fi completate ulterior, în execuții controlate sau în pilot feedback.

Orice depășire de prag trebuie clasificată ca observație, warning sau blocker doar după context, ținând cont de:

- tipul cazului;
- volumul și calitatea datelor de intrare;
- prezența unor erori sau warning-uri de date;
- diferența dintre un flux normal și un flux cu probleme deliberate.

## 8. Tabel de măsurare manuală

| Acțiune UI | Cod produs | Lot | Surse detectate | Dimensiune input | Start timestamp | End timestamp | Durată secunde | Rezultat | Tip eroare | Output generat | Observații operator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Pornire aplicație |  |  |  |  |  |  |  |  |  |  |  |
| Selectare folder surse |  |  |  |  |  |  |  |  |  |  |  |
| Verificare surse / preflight |  |  |  |  |  |  |  |  |  |  |  |
| Preview / audit checklist |  |  |  |  |  |  |  |  |  |  |  |
| Generare raport DOCX |  |  |  |  |  |  |  |  |  |  |  |
| Generare Diagnostic ZIP |  |  |  |  |  |  |  |  |  |  |  |
| Flux complet end-to-end |  |  |  |  |  |  |  |  |  |  |  |

## 9. Secțiune pentru observații

Se consemnează aici observații relevante care ajută interpretarea timpilor măsurați, de exemplu:

- input neobișnuit de mare;
- sursă coruptă sau parțial lizibilă;
- warning-uri de date care au afectat fluxul;
- întârziere observată doar la anumite tipuri de output;
- diferențe între rulări similare.

## 10. Secțiune pentru decizie

Pentru fiecare execuție sau set de măsurări, decizia se consemnează ca:

- `acceptable`
- `acceptable with observations`
- `needs optimization`

Această decizie nu închide proiectul și nu marchează automat nicio etapă de produs ca `DONE`.

## 11. Notă explicită

Acest document descrie doar planul de măsurare a performanței UI.

Nu reprezintă măsurarea efectivă.
Nu reprezintă optimizare implementată.
Nu reprezintă release claim.
Nu reprezintă `daily-use internal release`.
Nu declară proiectul închis.

Performanța reală va fi evaluată incremental, iar eventualele optimizări sau corecții rămân posibile după release, în linie cu poziționarea proiectului ca `controlled internal pilot` / `pre-release internal candidate`.
