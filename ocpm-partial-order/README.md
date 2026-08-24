# OCPM Partial Order — Order Management Prototype

Prototipo universitario per la costruzione di **Instance Graph object-centric a ordine parziale** a partire da process execution estratte da un log OCEL 2.0.

Il progetto è sviluppato da **Nicolò Ianni** e **Danilo La Palombara** nell’ambito di Big Data Analytics e Object-Centric Process Mining.

> **Stato attuale:** sono state completate la configurazione dell’ambiente, l’esplorazione del dataset, la discovery preliminare della Object-Centric Petri Net, la costruzione dell’Instance Graph su un esempio sintetico e su una process execution reale, la derivazione automatica delle causal relations dall’Object-Centric Directly-Follows Graph e lo screening di 22 process execution reali.
>
> Per l’ordine `o-990424` è stato costruito automaticamente un Instance Graph con 7 nodi e 6 archi. Il grafo è un DAG, è transitivamente ridotto e conserva due rami causali incomparabili.
>
> La procedura deriva 26 causal relations: 22 tra attività differenti e 4 auto-relazioni. I self-loop permettono di ordinare correttamente le attività ripetute sullo stesso oggetto senza imporre un ordine tra attività uguali riferite a oggetti differenti.
>
> Le causal relations non sono ricavate direttamente dagli archi della OCPN: vengono inferite dalle frequenze dell’OC-DFG mediante dependency measure, supporto relativo e self-loop score. Non è stato ancora eseguito un conformance checking object-centric formale e non è stata dimostrata una fitness pari a 1.

---

## 1. Obiettivo

Nel process mining tradizionale gli eventi vengono normalmente organizzati in tracce utilizzando un singolo `case_id`. Questa rappresentazione è limitante quando uno stesso evento coinvolge contemporaneamente entità differenti, per esempio:

- un ordine;
- uno o più articoli;
- uno o più pacchi;
- un prodotto;
- un dipendente.

L’Object-Centric Process Mining evita di scegliere in anticipo un unico identificatore di caso e conserva i collegamenti tra eventi e oggetti di tipi differenti.

Questo progetto adatta a tale contesto il concetto di **Instance Graph**. Nel grafo:

- ogni nodo rappresenta un evento della process execution;
- ogni arco rappresenta una dipendenza causale ammessa;
- gli archi sono motivati da almeno un oggetto condiviso;
- gli eventi privi di un ordine causale restano incomparabili;
- la riduzione transitiva elimina gli archi ridondanti senza modificare la raggiungibilità.

L’obiettivo non è trasformare il log in una sequenza cronologica più ordinata. Il timestamp descrive l’ordine osservato, ma non è sufficiente a dimostrare una dipendenza causale.

Per esempio, se il pagamento viene registrato dopo la consegna, ciò non implica automaticamente:

```text
package delivered -> pay order
```

L’arco viene inserito soltanto se una causal relation applicabile e un oggetto condiviso lo giustificano.

---

## 2. Pipeline del progetto

La pipeline attuale è:

```text
OCEL 2.0 Order Management
        |
        +--> esplorazione del log
        |
        +--> discovery preliminare della OCPN
        |
        +--> discovery dell’OC-DFG
        |
        +--> scoring delle relazioni
        |       |
        |       +--> dependency measure
        |       +--> supporto relativo
        |       `--> self-loop score
        |
        +--> causal relations filtrate
        |
        +--> estrazione order-centred
        |
        +--> adapter verso il modello interno
        |
        +--> costruzione dell’Instance Graph
        |
        +--> controllo DAG
        +--> controllo di copertura e connessione
        +--> riduzione transitiva
        +--> ricerca delle coppie incomparabili
        `--> controllo delle attività ripetute
```

Le seguenti fasi devono rimanere distinte:

1. **model discovery:** ricavare un modello dal log;
2. **estrazione:** delimitare una process execution nel log object-centric;
3. **inferenza delle causal relations:** selezionare dipendenze candidate;
4. **costruzione dell’Instance Graph:** applicare le relazioni agli eventi e agli oggetti;
5. **conformance checking:** verificare formalmente se l’execution è riproducibile dal modello.

Completare una fase non dimostra automaticamente le altre.

---

## 3. Assunzioni e limiti metodologici

La versione attuale assume che:

- la process execution venga estratta con una regola order-centred;
- la chiusura strutturale segua `orders -> items -> packages`;
- `products` ed `employees` non vengano attraversati durante l’espansione;
- le causal relations siano rappresentate a livello di attività e tipo di oggetto;
- non siano necessari repairing, inserimenti o cancellazioni di eventi;
- non vengano ancora calcolati object-centric alignment;
- non sia stato ancora eseguito un token-based replay object-centric;
- i self-loop di lunghezza 1 siano gestiti mediante una soglia dedicata;
- i loop complessi non siano ancora gestiti in modo generale;
- l’algoritmo rimanga indipendente dalle classi private di PM4Py o OCPA.

`products` ed `employees` vengono conservati negli eventi estratti, ma non vengono usati per espandere la execution. Nel dataset sono oggetti condivisi trasversalmente e potrebbero collegare ordini differenti in una connected component molto grande.

---

## 4. Dataset Order Management

Il dataset principale è **Order Management**, memorizzato localmente in formato OCEL 2.0 SQLite:

```text
data/raw/order_management.sqlite
```

Il file non viene versionato e deve essere copiato manualmente nella cartella indicata.

L’esplorazione ha prodotto:

| Misura | Valore |
| --- | ---: |
| Eventi | 21.008 |
| Oggetti | 10.825 |
| Relazioni evento-oggetto | 143.463 |
| Attività | 11 |
| Tipi di oggetto | 5 |

I tipi di oggetto sono:

- `orders`;
- `items`;
- `packages`;
- `products`;
- `employees`.

Distribuzione degli oggetti:

| Tipo | Numero |
| --- | ---: |
| `items` | 7.659 |
| `orders` | 2.000 |
| `packages` | 1.128 |
| `products` | 20 |
| `employees` | 18 |

Il numero ridotto di prodotti e dipendenti rispetto al numero di ordini rende pericolosa un’espansione indiscriminata per connected components: questi oggetti possono comportarsi come ponti tra esecuzioni differenti.

---

## 5. Sviluppo del progetto

### Configurazione dell’ambiente

L’ambiente è stato configurato e verificato su Windows con:

- Python 3.12;
- virtual environment locale `.venv`;
- PM4Py;
- pandas;
- NetworkX;
- Matplotlib;
- Graphviz;
- pytest;
- Jupyter e ipykernel.

### Esplorazione dell’OCEL

Il notebook `02_ocel_exploration.ipynb`:

- carica l’OCEL 2.0 SQLite;
- analizza eventi, oggetti e relazioni;
- conta attività e tipi di oggetto;
- misura quanti oggetti sono associati agli eventi;
- documenta il rischio degli oggetti condivisi.

### Discovery preliminare della OCPN

Il notebook `03_ocpn_discovery.ipynb` usa PM4Py per scoprire una Object-Centric Petri Net.

Il risultato comprende:

- 11 attività;
- 5 tipi di oggetto;
- una Petri net per ciascun tipo;
- attività iniziali e finali;
- informazioni su archi, molteplicità e prestazioni.

Questa fase dimostra la discovery del modello, non la conformità delle execution. Non è stata dimostrata una fitness pari a 1.

### Prototipo preliminare — Toy example

Prima del dataset reale è stata verificata la pipeline su un esempio sintetico controllato:

- 7 eventi;
- 6 causal relations manuali;
- costruzione dell’Instance Graph;
- controllo DAG;
- riduzione transitiva;
- ricerca delle coppie incomparabili;
- generazione PNG;
- confronto tra due linearizzazioni temporali equivalenti.

Il test centrale dimostra che l’inversione temporale di due eventi appartenenti a rami indipendenti produce lo stesso grafo causale.

### Instance Graph su una execution reale

Il primo caso reale è l’ordine `o-990424`:

| Proprietà | Valore |
| --- | ---: |
| Eventi | 7 |
| Ordini | 1 |
| Item | 1 |
| Pacchi | 1 |

L’estrazione order-centred segue:

```text
order -> items -> packages
```

La baseline usa sei causal relations manuali e produce:

```text
place order -> confirm order -> pay order
     |
     `-> pick item -> create package -> send package -> package delivered
```

Il grafo possiede:

| Proprietà | Risultato |
| --- | ---: |
| Nodi | 7 |
| Archi | 6 |
| DAG | sì |
| Transitivamente ridotto | sì |
| Coppie incomparabili | 8 |

### Derivazione automatica delle causal relations

Una derivazione basata sulla semplice raggiungibilità nella OCPN è risultata troppo permissiva, soprattutto per il tipo `items`, la cui rete è ciclica e generalizzante.

È stata quindi adottata una soluzione basata sull’OC-DFG.

Per attività differenti viene calcolata la dependency measure:

```text
dependency(A, B) =
    (f(A, B) - f(B, A))
    / (f(A, B) + f(B, A) + 1)
```

Il supporto relativo è:

```text
relative_support(A, B) =
    f(A, B)
    / max_y f(A, y)
```

Le soglie iniziali sono:

| Parametro | Valore |
| --- | ---: |
| Dependency threshold | `0.90` |
| Supporto relativo | `0.05` |

Prima dell’estensione ai self-loop, la procedura selezionava 22 relazioni tra attività differenti. Dieci erano applicabili a `o-990424` e producevano esattamente i sei archi della baseline manuale.

La sensitivity analysis ha valutato 24 combinazioni di soglie. La topologia attesa è stata mantenuta in 15 configurazioni.

### Screening e self-loop

Lo screening estende la valutazione a tutte le 22 process execution complete e non contaminate individuate dal diagnostico.

#### Self-loop score

La prima versione escludeva le relazioni in cui sorgente e destinazione coincidevano. Ciò rendeva incomparabili tentativi di consegna consecutivi sullo stesso pacco.

Per le auto-relazioni viene ora usato:

```text
self_loop_score(A) =
    f(A, A) / (f(A, A) + 1)
```

La soglia è:

```text
self_loop_threshold = 0.90
```

La procedura deriva quattro auto-relazioni:

| Tipo | Relazione |
| --- | --- |
| `orders` | `payment reminder -> payment reminder` |
| `items` | `payment reminder -> payment reminder` |
| `items` | `failed delivery -> failed delivery` |
| `packages` | `failed delivery -> failed delivery` |

Il totale passa quindi a:

```text
26 causal relations
```

di cui:

- 22 tra attività differenti;
- 4 auto-relazioni.

#### Screening delle 22 execution

Lo script `screen_order_executions.py` controlla per ogni execution:

- DAG;
- connessione debole;
- copertura completa degli eventi;
- assenza di nodi isolati;
- riduzione transitiva;
- coppie incomparabili;
- sorgenti e pozzi;
- attività ripetute incomparabili sullo stesso oggetto.

Risultato:

| Misura | Valore |
| --- | ---: |
| Execution previste | 22 |
| Execution superate | 22 |
| Execution fallite | 0 |
| Grafi DAG | 22 |
| Grafi debolmente connessi | 22 |
| Grafi transitivamente ridotti | 22 |
| Execution con eventi isolati | 0 |
| Ripetizioni sospette | 0 |

I casi comprendono:

- 13 execution senza eccezioni;
- 9 execution con eccezioni;
- 3 execution con più di un pacco;
- da 1 a 8 item;
- fino a 22 eventi.

#### Caso `o-990254`

Due `failed delivery` sullo stesso pacco formano ora:

```text
fail_p-660164_54
    -> fail_p-660164_56
```

Le coppie incomparabili passano da 105 a 104.

#### Caso `o-990042`

Sette `failed delivery` sullo stesso pacco formano:

```text
fail_p-660027_4
    -> fail_p-660027_6
    -> fail_p-660027_7
    -> fail_p-660027_8
    -> fail_p-660027_9
    -> fail_p-660027_11
    -> fail_p-660027_12
```

Sette eventi generano 21 coppie possibili:

```text
7 * 6 / 2 = 21
```

Prima della correzione tutte risultavano incomparabili. Dopo la correzione, le coppie incomparabili complessive passano da 92 a 71.

#### Attività uguali su oggetti differenti

Il self-loop viene applicato all’interno del ciclo di vita dello stesso oggetto.

I due eventi `pick item` di `o-990878` appartengono a item differenti e restano incomparabili:

```text
pick_i-883511 || pick_i-883512
```

---

## 6. Modello dati interno

L’algoritmo non dipende direttamente dalle rappresentazioni interne di PM4Py o OCPA.

### `ObjectReference`

Rappresenta un oggetto associato a un evento:

- `object_id`;
- `object_type`.

### `ExecutionEvent`

Rappresenta un evento:

- `event_id`;
- `activity`;
- `timestamp`;
- insieme di `ObjectReference`.

### `ProcessExecution`

Contiene gli eventi di una execution e permette di ottenere:

- identificatori degli eventi;
- oggetti coinvolti;
- eventi associati a un oggetto.

### `CausalRelation`

Descrive una relazione causale ammessa:

- `source_activity`;
- `target_activity`;
- `object_type`.

### `CausalRelationEvidence`

Documenta le misure associate a una relazione candidata:

- frequenza forward;
- frequenza backward;
- dependency measure;
- supporto relativo;
- self-loop score, se sorgente e destinazione coincidono.

---

## 7. Costruzione dell’Instance Graph

Per ogni oggetto strutturale, l’algoritmo:

1. raccoglie gli eventi associati;
2. li ordina deterministicamente per timestamp e `event_id`;
3. verifica se le attività corrispondono a una causal relation;
4. crea un arco solo tra eventi che condividono l’oggetto;
5. unisce le annotazioni se lo stesso arco è supportato da più oggetti;
6. controlla l’assenza di cicli;
7. applica la riduzione transitiva.

Ogni arco conserva:

- i tipi di oggetto che lo giustificano;
- gli identificatori degli oggetti coinvolti.

Le relazioni vengono applicate alle singole occorrenze degli eventi, non soltanto alle etichette astratte delle attività.

---

## 8. Incomparabilità e parallelismo potenziale

Due eventi sono incomparabili quando non esiste un percorso causale in nessuna direzione:

```text
not path(A, B) and not path(B, A)
```

Nel prototipo queste coppie sono candidate al parallelismo.

L’incomparabilità non dimostra da sola che due eventi siano realmente paralleli. Può anche dipendere da:

- relazioni causali mancanti;
- soglie troppo restrittive;
- rumore nel log;
- limiti del modello;
- semantica non rappresentata.

Per questo motivo viene usata come proprietà del grafo, non come prova definitiva di concorrenza reale.

---

## 9. Struttura del repository

```text
ocpm-partial-order/
|-- data/
|   |-- raw/
|   |   `-- order_management.sqlite
|   |-- samples/
|   |   |-- order_management_toy_execution.json
|   |   |-- order_management_toy_execution_reordered.json
|   |   `-- order_management_toy_causal_relations.json
|   `-- derived/
|       `-- order_management_o_990424_causal_relations.json
|
|-- notebooks/
|   |-- 01_environment_check.ipynb
|   |-- 02_ocel_exploration.ipynb
|   |-- 03_ocpn_discovery.ipynb
|   |-- 04_real_instance_graph.ipynb
|   |-- 05_instance_graph.ipynb
|   `-- 06_real_execution.ipynb
|
|-- outputs/
|   |-- figures/
|   |-- graphs/
|   |   |-- order_management_toy_instance_graph.png
|   |   |-- order_management_o_990424_instance_graph.png
|   |   |-- order_management_o_990424_discovered_instance_graph.png
|   |   |-- order_management_o-990254_execution_screening.png
|   |   `-- order_management_o-990042_execution_screening.png
|   |-- reports/
|   |   `-- execution_screening.txt
|   `-- tables/
|
|-- scripts/
|   |-- check_environment.py
|   |-- inspect_ocel.py
|   |-- inspect_order_candidates.py
|   |-- run_order_management_toy.py
|   |-- run_order_management_real.py
|   |-- run_order_management_discovered.py
|   |-- run_toy_example.py
|   |-- screen_order_executions.py
|   `-- verify_real_execution.py
|
|-- src/ocpm_partial_order/
|   |-- config.py
|   |-- discovery/
|   |   |-- __init__.py
|   |   |-- causal_relations.py
|   |   `-- ocpn_discovery.py
|   |-- domain/
|   |   |-- causal_relation.py
|   |   |-- event.py
|   |   `-- process_execution.py
|   |-- extraction/
|   |   `-- execution_adapter.py
|   |-- graphs/
|   |   |-- concurrency.py
|   |   |-- instance_graph.py
|   |   `-- validation.py
|   |-- io/
|   |   |-- ocel_loader.py
|   |   `-- sample_loader.py
|   `-- visualization/
|       `-- graph_visualizer.py
|
|-- tests/
|   |-- fixtures/
|   |-- test_causal_relations.py
|   |-- test_concurrency.py
|   |-- test_discovered_causal_relations.py
|   |-- test_equivalent_linearizations.py
|   |-- test_execution_adapter.py
|   |-- test_instance_graph.py
|   |-- test_real_instance_graph.py
|   |-- test_real_self_loops.py
|   `-- test_sample_loader.py
|
|-- .gitignore
|-- pyproject.toml
|-- requirements.txt
`-- README.md
```

Gli artefatti in `outputs/` sono rigenerabili e possono essere esclusi dal versionamento.

Il dataset in `data/raw/` resta locale. Il file in `data/derived/` rappresenta invece la baseline manuale riproducibile.

---

## 10. Installazione su Windows

### Prerequisiti

- Python 3.11 o 3.12;
- Git;
- Graphviz installato;
- comando `dot` disponibile nel `PATH`.

Verifica di Graphviz:

```powershell
dot -V
```

### Creazione dell’ambiente virtuale

```powershell
py -3.12 -m venv .venv
```

Attivazione:

```powershell
.\.venv\Scripts\Activate.ps1
```

Installazione:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
```

Se necessario:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Dataset

Copiare il database in:

```text
data/raw/order_management.sqlite
```

---

## 11. Esecuzione

### Controllo dell’ambiente

```powershell
.\.venv\Scripts\python.exe .\scripts\check_environment.py
```

### Ispezione dell’OCEL

```powershell
.\.venv\Scripts\python.exe .\scripts\inspect_ocel.py
```

### Selezione dei candidati

```powershell
.\.venv\Scripts\python.exe .\scripts\inspect_order_candidates.py
```

### Toy example

```powershell
.\.venv\Scripts\python.exe .\scripts\run_order_management_toy.py
```

### Verifica dell’estrazione reale

```powershell
.\.venv\Scripts\python.exe .\scripts\verify_real_execution.py
```

### Caso reale con relazioni manuali

```powershell
.\.venv\Scripts\python.exe .\scripts\run_order_management_real.py
```

### Caso reale con relazioni automatiche

```powershell
.\.venv\Scripts\python.exe .\scripts\run_order_management_discovered.py
```

Output principale:

```text
Dependency threshold: 0.9
Relative support threshold: 0.05
Self-loop threshold: 0.9
Causal relations totali: 26
Causal relations rilevanti: 10

Instance Graph:
Nodi: 7
Archi: 6
DAG: True

VERIFICA CON RELAZIONI DERIVATE SUPERATA
```

### Screening delle 22 execution

```powershell
.\.venv\Scripts\python.exe .\scripts\screen_order_executions.py
```

Riepilogo atteso:

```text
Execution previste: 22
Execution superate: 22
Execution fallite: 0
Ripetizioni sospette: 0

SCREENING COMPLETO SUPERATO
```

---

## 12. Notebook

Avvio di Jupyter Lab:

```powershell
.\.venv\Scripts\python.exe -m jupyter lab
```

Ordine consigliato:

1. `01_environment_check.ipynb`;
2. `02_ocel_exploration.ipynb`;
3. `03_ocpn_discovery.ipynb`;
4. `04_real_instance_graph.ipynb`;
5. `05_instance_graph.ipynb`;
6. `06_real_execution.ipynb`.

### Notebook 04

Documenta l’estrazione order-centred e la baseline manuale sul caso reale.

### Notebook 05

Documenta:

- analisi della OCPN;
- limite della raggiungibilità ingenua;
- discovery dell’OC-DFG;
- dependency e supporto relativo;
- sensitivity analysis;
- confronto tra relazioni automatiche e baseline.

Validazione:

```text
Celle totali: 24
Celle di codice: 9
Celle eseguite: 9
Celle Markdown: 15
Errori: 0
```

### Notebook 06

Documenta:

- le 26 causal relations;
- le quattro auto-relazioni;
- il self-loop score;
- lo screening delle 22 execution;
- i casi con più item e pacchi;
- le principali eccezioni;
- le catene di `failed delivery`;
- l’incomparabilità su oggetti differenti;
- i limiti metodologici.

Validazione:

```text
Celle totali: 22
Celle di codice: 10
Celle Markdown: 12
Celle eseguite: 10
Errori: 0
Dimensione: 381650 byte
Validazione notebook: superata
```

Esecuzione non interattiva:

```powershell
.\.venv\Scripts\python.exe -m jupyter nbconvert `
    --to notebook `
    --execute `
    --inplace `
    .\notebooks\06_real_execution.ipynb `
    --ExecutePreprocessor.timeout=600
```

Gli avvisi ZMQ relativi al Proactor event loop e al TCP locale non indicano un errore del notebook. La verifica rilevante è l’assenza di output con `output_type = error`.

---

## 13. Test automatici

Esecuzione completa:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Risultato verificato dopo l'introduzione dello screening:

```text
32 passed
```

La suite comprende:

| Area | Verifica |
| --- | --- |
| caricamento | parsing degli input sintetici |
| modello dati | eventi e oggetti |
| grafo | nodi, archi, DAG e riduzione transitiva |
| incomparabilità | rami causali distinti |
| linearizzazioni | stesso grafo per ordini temporali equivalenti |
| adapter | conversione OCEL nel modello interno |
| estrazione | delimitazione order-centred |
| baseline reale | proprietà di `o-990424` |
| scoring | dependency e supporto relativo |
| self-loop | calcolo e filtraggio delle auto-relazioni |
| discovery reale | relazioni automatiche attese |
| loop reali | catene di `failed delivery` |
| oggetti differenti | attività uguali lasciate incomparabili |
| screening | validazione strutturale di 22 execution |

Test specifici della derivazione automatica e dello screening:

```text
tests/test_causal_relations.py
tests/test_discovered_causal_relations.py
tests/test_real_self_loops.py
```

`test_causal_relations.py` contiene 12 casi, comprendenti scoring ordinario, self-loop e validazione delle soglie.

`test_discovered_causal_relations.py` contiene 3 test di integrazione su `o-990424`.

`test_real_self_loops.py` contiene 5 verifiche reali:

- scoperta delle quattro auto-relazioni;
- catena dei due fallimenti di `o-990254`;
- catena dei sette fallimenti di `o-990042`;
- incomparabilità dei pick su item differenti;
- proprietà DAG e riduzione transitiva.

---

## 14. Risultati dimostrati

Il progetto dimostra:

- caricamento ed esplorazione del dataset OCEL 2.0;
- discovery preliminare della OCPN;
- modello dati interno indipendente da PM4Py;
- costruzione dell’Instance Graph sintetico;
- equivalenza di linearizzazioni temporali indipendenti;
- estrazione order-centred di execution reali;
- baseline manuale per `o-990424`;
- derivazione automatica dall’OC-DFG;
- scoring mediante dependency e supporto relativo;
- gestione dei self-loop di lunghezza 1;
- derivazione di 26 causal relations;
- corrispondenza esatta con la baseline di `o-990424`;
- screening di 22 execution reali;
- 22 grafi DAG, connessi e transitivamente ridotti;
- assenza di eventi isolati;
- assenza di ripetizioni sospette;
- ordinamento delle ripetizioni sullo stesso oggetto;
- conservazione dell’incomparabilità su oggetti differenti;
- esecuzione senza errori dei notebook 05 e 06;
- superamento di 32 test automatici.

---

## 15. Risultati non ancora dimostrati

Il progetto non dimostra ancora:

- fitness pari a 1;
- conformance checking object-centric formale;
- token-based replay object-centric completo;
- object-centric alignment;
- repairing della process execution;
- gestione generale di eventi mancanti o aggiuntivi;
- validità delle soglie su tutte le 2.000 execution;
- correttezza su dataset differenti;
- gestione generale di loop complessi;
- disambiguazione generale di transizioni diverse con la stessa etichetta;
- derivazione diretta dalla semantica della OCPN;
- equivalenza generale tra OC-DFG filtrato e causalità del modello;
- identificazione certa del parallelismo reale dalla sola incomparabilità;
- scalabilità su tutte le process execution del log.

I risultati ottenuti costituiscono una verifica sperimentale sui casi selezionati, non una dimostrazione universale.

---

## 16. Prossimi passi

### 16.1 Conformance checking

Studiare la disponibilità di:

- token-based replay object-centric;
- fitness per tipo di oggetto;
- diagnostica della OCPN;
- alignment object-centric;
- verifica della riproducibilità delle execution.

### 16.2 Estensione oltre le 22 execution

Analizzare:

- execution incomplete;
- execution strutturalmente contaminate;
- ordini collegati da oggetti condivisi;
- casi esclusi dai criteri attuali;
- dataset object-centric differenti.

### 16.3 Stabilità delle soglie

Le soglie `0.90 / 0.05 / 0.90` sono state mantenute fisse durante lo screening delle 22 execution.

Il risultato riduce il rischio di overfitting sul solo `o-990424`, ma non dimostra validità universale. Sarà utile separare formalmente calibrazione e valutazione.

### 16.4 Loop complessi

Rimangono da analizzare:

- loop che coinvolgono più attività;
- ritorni a stati precedenti;
- relazioni reciproche dovute a cicli;
- transizioni differenti con la stessa etichetta;
- distinzione tra loop e rumore statistico.

### 16.5 Confronto tra sorgenti causali

Confrontare:

- relazioni manuali;
- relazioni inferite dall’OC-DFG;
- relazioni estratte dalla OCPN;
- relazioni ottenute tramite replay o alignment.

---

## 17. Riproducibilità

Prima di ogni commit importante eseguire:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

```powershell
.\.venv\Scripts\python.exe .\scripts\run_order_management_discovered.py
```

```powershell
.\.venv\Scripts\python.exe .\scripts\screen_order_executions.py
```

```powershell
.\.venv\Scripts\python.exe -m jupyter nbconvert `
    --to notebook `
    --execute `
    --inplace `
    .\notebooks\06_real_execution.ipynb `
    --ExecutePreprocessor.timeout=600
```

```powershell
git status --short
git diff --check
```

Su Windows può comparire:

```text
LF will be replaced by CRLF
```

È un avviso sulle terminazioni di riga e non indica necessariamente un errore. `git diff --check` non deve segnalare trailing whitespace, conflict marker o altri problemi reali.

---

## 18. Riferimenti

- W. M. P. van der Aalst e A. Berti, *Discovering Object-Centric Petri Nets*, Fundamenta Informaticae, 175(1–4), 2020.
- A. J. M. M. Weijters, W. M. P. van der Aalst e A. K. Alves de Medeiros, *Process Mining with the HeuristicsMiner Algorithm*, Eindhoven University of Technology, 2006.
- PM4Py — Process Mining for Python: https://processintelligence.solutions/pm4py
- PM4Py source code: https://github.com/process-intelligence-solutions/pm4py
- NetworkX documentation: https://networkx.org/documentation/stable/

---

## Autori

**Nicolò Ianni**

**Danilo La Palombara**
