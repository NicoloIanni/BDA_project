# OCPM Partial Order — Order Management Prototype

Prototipo universitario per la costruzione di **Instance Graph object-centric a ordine parziale** a partire da process execution estratte da un log OCEL 2.0.

Il progetto è sviluppato da **Nicolò Ianni** e **Danilo La Palombara** nell’ambito di Big Data Analytics e Object-Centric Process Mining.

> **Stato attuale:** sono state completate la configurazione dell’ambiente, l’esplorazione del dataset, la discovery preliminare della Object-Centric Petri Net, la costruzione dell’Instance Graph su un esempio sintetico e su process execution reali, la derivazione automatica delle causal relations dall’Object-Centric Directly-Follows Graph, lo screening di 22 process execution, il conformance checking per tipo di oggetto e la validazione out-of-sample senza condivisione di casi o eventi.
>
> Per l’ordine `o-990424` è stato costruito automaticamente un Instance Graph con 7 nodi e 6 archi. Il grafo è un DAG, è transitivamente ridotto e conserva due rami causali incomparabili.
>
> La procedura deriva 26 causal relations: 22 tra attività differenti e 4 auto-relazioni. I self-loop permettono di ordinare correttamente le attività ripetute sullo stesso oggetto senza imporre un ordine tra attività uguali riferite a oggetti differenti.
>
> Il conformance checking è stato eseguito separatamente sulle proiezioni `orders`, `items` e `packages`. Tutte le 10.787 proiezioni risultano conformi alle rispettive Petri net componenti, con fitness media pari a 1 e senza token mancanti o residui. Questo risultato non costituisce una fitness object-centric globalmente sincronizzata.
>
> Nella validazione out-of-sample, le reti sono state scoperte soltanto sui training set e valutate su 2.202 tracce di test senza identificatori di caso o evento condivisi. Tutte le tracce risultano fitting; la precisione della componente `items`, pari a circa 0,47, evidenzia tuttavia un modello fortemente generalizzante.

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

L’obiettivo non è trasformare il log in una semplice sequenza cronologica. Il timestamp descrive l’ordine osservato, ma non è sufficiente a dimostrare una dipendenza causale.

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
        |       |
        |       +--> Petri net per orders
        |       +--> Petri net per items
        |       `--> Petri net per packages
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
        |       |
        |       +--> controllo DAG
        |       +--> controllo di copertura e connessione
        |       +--> riduzione transitiva
        |       +--> ricerca delle coppie incomparabili
        |       `--> controllo delle attività ripetute
        |
        `--> conformance checking per tipo di oggetto
                |
                +--> flattening delle proiezioni
                +--> token-based replay
                +--> diagnostica per singolo oggetto
                `--> riepilogo per tipo di oggetto
```

Le attività metodologiche devono rimanere distinte:

1. **model discovery:** ricavare un modello dal log;
2. **estrazione:** delimitare una process execution nel log object-centric;
3. **inferenza delle causal relations:** selezionare dipendenze candidate;
4. **costruzione dell’Instance Graph:** applicare le relazioni agli eventi e agli oggetti;
5. **conformance checking:** verificare se le proiezioni sono riproducibili dalle Petri net componenti.

Il completamento di un’attività non dimostra automaticamente le altre.

---

## 3. Assunzioni e limiti metodologici

La versione attuale assume che:

- la process execution venga estratta con una regola order-centred;
- la chiusura strutturale segua `orders -> items -> packages`;
- `products` ed `employees` non vengano attraversati durante l’espansione;
- le causal relations siano rappresentate a livello di attività e tipo di oggetto;
- il conformance checking venga eseguito separatamente sulle proiezioni dei tipi strutturali;
- non vengano ancora calcolati object-centric alignment globalmente sincronizzati;
- non sia stato ancora eseguito un token-based replay object-centric globalmente sincronizzato;
- il controllo sulle proiezioni sia in-sample, perché la OCPN viene scoperta dallo stesso OCEL sottoposto a replay;
- non vengano applicati repairing, inserimenti o cancellazioni alla process execution;
- i self-loop di lunghezza 1 siano gestiti mediante una soglia dedicata;
- i loop complessi non siano ancora gestiti in modo generale;
- l’algoritmo rimanga indipendente dalle classi private di PM4Py o OCPA.

`products` ed `employees` vengono conservati negli eventi estratti, ma non vengono usati per espandere la process execution. Nel dataset sono oggetti condivisi trasversalmente e potrebbero collegare ordini differenti in una connected component molto grande.

Le causal relations automatiche non vengono ricavate direttamente dagli archi o dalla semantica di esecuzione della OCPN. Sono inferite dal comportamento osservato nell’OC-DFG mediante misure di frequenza.

---

## 4. Dataset Order Management

Il dataset principale è **Order Management**, distribuito come log OCEL 2.0 in formato SQLite.

Percorso locale:

```text
data/raw/order_management.sqlite
```

Il dataset contiene:

| Elemento | Quantità |
| --- | ---: |
| eventi | 21.008 |
| oggetti | 10.825 |
| relazioni evento-oggetto | 143.463 |
| attività | 11 |
| tipi di oggetto | 5 |

Distribuzione degli oggetti:

| Tipo | Quantità |
| --- | ---: |
| `items` | 7.659 |
| `orders` | 2.000 |
| `packages` | 1.128 |
| `products` | 20 |
| `employees` | 18 |

Attività presenti:

- `place order`;
- `confirm order`;
- `pay order`;
- `pick item`;
- `item out of stock`;
- `reorder item`;
- `create package`;
- `send package`;
- `package delivered`;
- `payment reminder`;
- `failed delivery`.

Il dataset non viene incluso nel repository. Deve essere collocato manualmente in `data/raw/`.

---

## 5. Sviluppo del progetto

### Configurazione dell’ambiente

L’ambiente utilizza:

- Python 3.11 o 3.12;
- PM4Py;
- pandas;
- NetworkX;
- Matplotlib;
- Graphviz;
- pytest;
- Jupyter e ipykernel.

### Esplorazione dell’OCEL

L’esplorazione iniziale verifica:

- tabelle di eventi, oggetti e relazioni;
- tipi di oggetto disponibili;
- attività osservate;
- numerosità e distribuzioni;
- relazioni molti-a-molti tra eventi e oggetti.

### Discovery preliminare della OCPN

La Object-Centric Petri Net viene scoperta con PM4Py. La struttura restituita contiene una Petri net tradizionale per ciascun tipo di oggetto.

Le componenti relative a `orders` e `packages` sono sufficientemente chiare. La componente relativa a `items` è più ciclica e generalizzante.

Una semplice analisi di raggiungibilità tra transizioni visibili produceva, per `items`, 42 relazioni rilevanti rispetto alle due attese nel caso di riferimento, includendo relazioni reciproche e auto-relazioni. La raggiungibilità nella rete non è stata quindi usata direttamente come causalità dell’Instance Graph.

### Toy example

Il primo controllo usa un esempio sintetico con sette eventi e relazioni causali note. Sono verificati:

- costruzione del grafo;
- assenza di cicli;
- riduzione transitiva;
- conservazione dello stesso ordine parziale dopo il riordinamento temporale di eventi indipendenti.

Il test centrale dimostra che l’inversione temporale di eventi appartenenti a rami indipendenti non modifica il grafo causale.

### Process execution reale `o-990424`

La prima process execution reale selezionata è centrata sull’ordine `o-990424` e contiene:

- ordine `o-990424`;
- articolo `i-881734`;
- pacco `p-660247`;
- 7 eventi complessivi.

Le attività osservate in ordine temporale sono:

```text
place order
-> confirm order
-> pick item
-> create package
-> send package
-> package delivered
-> pay order
```

La baseline manuale contiene sei relazioni e genera due rami dopo `place order`:

```text
ramo amministrativo:
place order -> confirm order -> pay order

ramo logistico:
place order -> pick item -> create package
-> send package -> package delivered
```

L’Instance Graph risultante contiene:

- 7 nodi;
- 6 archi;
- nessun ciclo;
- nessun arco transitivo ridondante;
- 8 coppie di eventi incomparabili tra i due rami.

Il fatto che `pay order` abbia un timestamp successivo a `package delivered` non introduce una dipendenza causale tra consegna e pagamento.

### Derivazione automatica delle causal relations

Le causal relations vengono derivate dall’Object-Centric Directly-Follows Graph. Per ogni coppia di attività e tipo di oggetto vengono calcolate frequenza, direzione predominante e rilevanza relativa.

Per attività differenti viene usata la dependency measure:

```text
dependency(a, b) =
    (frequency(a, b) - frequency(b, a))
    / (frequency(a, b) + frequency(b, a) + 1)
```

Il supporto relativo confronta la frequenza dell’arco con la massima frequenza uscente dalla stessa attività:

```text
relative_support(a, b) =
    frequency(a, b)
    / max_outgoing_frequency(a)
```

Le soglie predefinite sono:

```text
dependency threshold = 0.90
relative support threshold = 0.05
```

Con queste soglie vengono selezionate automaticamente 22 causal relations tra attività differenti. Dieci sono applicabili alla process execution `o-990424` e producono esattamente i sei archi della baseline, senza archi mancanti o aggiuntivi.

L’analisi di sensibilità considera 24 combinazioni di soglie. La topologia attesa viene mantenuta in 15 configurazioni, quindi il risultato non dipende da un solo valore scelto appositamente per il caso.

### Self-loop

Per una relazione nella quale attività sorgente e destinazione coincidono viene usato un punteggio dedicato:

```text
self_loop_score(a) =
    frequency(a, a)
    / (frequency(a, a) + 1)
```

La soglia predefinita è:

```text
self-loop threshold = 0.90
```

La procedura deriva quattro auto-relazioni. Complessivamente vengono quindi selezionate 26 causal relations:

```text
22 relazioni tra attività differenti
+ 4 auto-relazioni
= 26 causal relations
```

I self-loop vengono applicati soltanto a eventi consecutivi della stessa attività che condividono lo stesso oggetto. Attività uguali associate a oggetti differenti restano incomparabili.

### Screening delle 22 process execution

Tra i 2.000 ordini del dataset sono state individuate 22 process execution complete e non contaminate secondo la regola di estrazione adottata.

Per ogni execution vengono verificati:

- costruzione del grafo;
- assenza di cicli;
- connessione;
- copertura di tutti gli eventi;
- assenza di eventi isolati;
- riduzione transitiva;
- comportamento delle attività ripetute.

Risultati:

```text
execution analizzate: 22
grafi DAG: 22
grafi connessi: 22
grafi transitivamente ridotti: 22
execution con eventi isolati: 0
ripetizioni sospette: 0
```

Il caso `o-990254` contiene due eventi `failed delivery`, correttamente ordinati in una catena sullo stesso pacco.

Il caso `o-990042` contiene sette eventi `failed delivery`, anch’essi ordinati sullo stesso oggetto senza introdurre un ciclo.

Quando due eventi `pick item` riguardano articoli differenti, restano invece incomparabili.

### Conformance checking per tipo di oggetto

PM4Py non fornisce, nella versione utilizzata, un replay specifico di una singola process execution contro una OCPN con sincronizzazione globale tra tutti i tipi di oggetto.

Il progetto esegue quindi un controllo formale sulle singole proiezioni:

1. l’OCEL viene appiattito rispetto a un tipo di oggetto;
2. ogni oggetto diventa il caso di una traccia tradizionale;
3. la traccia viene confrontata con la Petri net componente dello stesso tipo;
4. PM4Py esegue il token-based replay;
5. vengono raccolti fitness, token mancanti e token residui.

Per `o-990424`:

| Tipo | Oggetto | Eventi | Fit | Fitness | Missing | Remaining |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| `orders` | `o-990424` | 3 | sì | 1.0 | 0 | 0 |
| `items` | `i-881734` | 7 | sì | 1.0 | 0 | 0 |
| `packages` | `p-660247` | 3 | sì | 1.0 | 0 | 0 |

Controllo sull’intero log:

| Tipo | Tracce | Conformi | Non conformi | Fitness media | Missing | Remaining |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `orders` | 2.000 | 2.000 | 0 | 1.0 | 0 | 0 |
| `items` | 7.659 | 7.659 | 0 | 1.0 | 0 | 0 |
| `packages` | 1.128 | 1.128 | 0 | 1.0 | 0 | 0 |
| **Totale** | **10.787** | **10.787** | **0** | **1.0** | **0** | **0** |

Questa è una verifica in-sample: la OCPN è stata scoperta dallo stesso OCEL sottoposto al replay. Il risultato misura la capacità delle componenti scoperte di riprodurre le proprie proiezioni, non la generalizzazione su dati esterni.

### Validazione out-of-sample senza leakage

Per valutare comportamento non utilizzato durante la discovery, ogni log appiattito viene suddiviso in training e test con rapporto obiettivo pari a `0.80`. Uno split diretto dei casi non è sufficiente per `items`: 131 eventi risulterebbero condivisi tra training e test, perché lo stesso evento può riferirsi a più articoli.

La procedura applicata è quindi:

1. collegare i casi che condividono almeno un identificatore di evento;
2. calcolare le componenti connesse;
3. assegnare ogni componente interamente al training o al test;
4. scoprire la Petri net esclusivamente dal training set;
5. valutare il test set mediante token-based replay e metriche di qualità.

| Tipo | Componenti | Training | Test | Rapporto effettivo | Varianti test non osservate |
| --- | ---: | ---: | ---: | ---: | ---: |
| `orders` | 2.000 | 1.600 | 400 | 0,8000 | 0 |
| `items` | 68 | 6.083 | 1.576 | 0,7942 | 28 |
| `packages` | 1.128 | 902 | 226 | 0,7996 | 0 |

Training e test non condividono identificatori di caso o di evento.

| Tipo | Tracce test | Fitting | Fitness | Precisione | Generalizzazione | Semplicità |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `orders` | 400 | 400 | 1,0 | 0,9978 | 0,9113 | 0,8824 |
| `items` | 1.576 | 1.576 | 1,0 | 0,4720 | 0,9567 | 0,6842 |
| `packages` | 226 | 226 | 1,0 | 0,9981 | 0,8863 | 0,8824 |
| **Totale** | **2.202** | **2.202** | **1,0** | n.d. | n.d. | n.d. |

Le 2.202 tracce di test risultano tutte conformi, senza token mancanti o residui. Per `orders` e `packages`, la fitness perfetta è accompagnata da una precisione superiore a 0,99. La precisione di `items`, pari a circa 0,47, mostra invece che la rete ammette molto comportamento aggiuntivo e conferma quantitativamente la struttura ciclica e generalizzante osservata durante l’analisi della OCPN.

Lo split di `items` è component-aware e privo di leakage, ma non è un holdout futuro in senso stretto: alcune componenti connesse attraversano periodi temporali sovrapposti.

### Validazione holdout object-centric basata su grafi

È stata aggiunta una validazione object-centric nativa basata sui confronti OC-DFG, OTG ed ET-OT forniti da PM4Py. Non si tratta di un replay sincronizzato sulla OCPN: il controllo confronta strutture object-centric scoperte esclusivamente sul training con quelle osservate nel test.

Lo split utilizza le componenti connesse degli oggetti strutturali `orders`, `items` e `packages`. I tipi `employees` e `products` vengono esclusi dallo split perché collegano l’intero log in una sola componente.

| Misura | Training | Test |
| --- | ---: | ---: |
| componenti | 44 | 24 |
| eventi | 16.547 | 4.461 |
| oggetti | 8.531 | 2.256 |
| eventi condivisi | 0 | 0 |
| oggetti condivisi | 0 | 0 |

| Rappresentazione | Fitness predefinita | Fitness strutturale |
| --- | ---: | ---: |
| OC-DFG | 0,4925 | 0,9851 |
| OTG | 0,5714 | 1,0000 |
| ET-OT | 0,6346 | 1,0000 |

Le fitness predefinite sono influenzate dalle diverse dimensioni di training e test. Il confronto strutturale mostra invece che tutto il comportamento osservato nel test era già presente nel training: la copertura del test è pari a 1 per attività e flussi OC-DFG tipizzati, archi OTG e relazioni ET-OT. Il test non introduce elementi strutturali nuovi.

Due soli flussi del training non ricompaiono nel test:

- `items: create package -> payment reminder`;
- `items: payment reminder -> send package`.

Entrambi appartengono alla stessa variante rara e sono osservati su sei item del training.

L’esperimento è implementato in `object_centric_graph_validation.py`, verificato da `test_object_centric_graph_validation.py`, riproducibile con `check_object_centric_graph_conformance.py` e documentato nel notebook `09_object_centric_graph_conformance.ipynb`.

```powershell
.\.venv\Scripts\python.exe .\scripts\check_object_centric_graph_conformance.py
```

Questi risultati forniscono evidenza di generalizzazione object-centric out-of-sample a livello di grafi, ma non dimostrano una fitness globalmente sincronizzata della OCPN.

### Controlli negativi

Il controllo non si limita ad accettare le tracce originali. La proiezione del pacco `p-660247` è stata modificata artificialmente per verificare che PM4Py riconosca le deviazioni.

| Scenario | Token fitness | Alignment fitness | Esito |
| --- | ---: | ---: | --- |
| traccia originale | 1.0 | 1.0 | conforme |
| evento finale rimosso | 0.6667 | 0.8 | non conforme |
| attività non prevista | 0.6667 | 0.6667 | non conforme |
| ordine invertito | 0.5 | 0.3333 | non conforme |

La transizione invisibile presente nell’allineamento della traccia originale appartiene al modello e non rappresenta una deviazione.

---

## 6. Modello dati interno

Il modello interno separa il dominio del progetto dalle strutture private degli strumenti esterni.

### `ObjectReference`

Rappresenta un oggetto mediante:

- tipo di oggetto;
- identificatore dell’oggetto.

### `ExecutionEvent`

Rappresenta un evento mediante:

- identificatore;
- attività;
- timestamp;
- riferimenti agli oggetti coinvolti.

### `ProcessExecution`

Contiene l’insieme ordinato degli eventi appartenenti alla process execution estratta.

### `CausalRelation`

Rappresenta una relazione tra:

- attività sorgente;
- attività destinazione;
- tipo di oggetto che giustifica la relazione.

### `CausalRelationEvidence`

Associa a una causal relation candidata:

- frequenza nella direzione osservata;
- frequenza nella direzione opposta;
- dependency measure;
- supporto relativo;
- eventuale self-loop score.

### Risultati di conformance

Il package `conformance` espone strutture immutabili per rappresentare:

- diagnostica di una singola traccia;
- riepilogo di tutte le tracce di un tipo;
- aggregazione delle proiezioni appartenenti a una process execution.

---

## 7. Costruzione dell’Instance Graph

Un arco tra due eventi viene inserito quando:

1. le attività corrispondono a una causal relation selezionata;
2. gli eventi condividono almeno un oggetto del tipo indicato dalla relazione;
3. l’ordine degli eventi è compatibile con la relazione;
4. per un self-loop, gli eventi appartengono allo stesso oggetto.

Dopo la costruzione vengono eseguiti:

- controllo di aciclicità;
- controllo di copertura;
- controllo di connessione;
- riduzione transitiva;
- individuazione delle coppie incomparabili.

Il risultato è un DAG che rappresenta un ordine parziale, non una semplice sequenza temporale.

---

## 8. Incomparabilità e parallelismo potenziale

Due eventi sono incomparabili quando non esiste un cammino dal primo al secondo né dal secondo al primo.

L’incomparabilità indica che le causal relations disponibili non impongono un ordine tra gli eventi. Può essere compatibile con il parallelismo, ma non ne costituisce da sola una prova definitiva.

Una coppia incomparabile può dipendere anche da:

- relazioni causali mancanti;
- soglie troppo restrittive;
- rumore nel log;
- limiti del modello;
- semantica non rappresentata.

Per questo motivo l’incomparabilità viene usata come proprietà del grafo e viene descritta come **parallelismo potenziale**.

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
|   |-- 06_real_execution.ipynb
|   |-- 07_conformance_checking.ipynb
|   |-- 08_out_of_sample_validation.ipynb
|   `-- 09_object_centric_graph_conformance.ipynb
|
|-- outputs/
|   |-- figures/
|   |-- graphs/
|   |-- reports/
|   `-- tables/
|
|-- scripts/
|   |-- check_environment.py
|   |-- check_object_type_conformance.py
|   |-- check_out_of_sample_conformance.py
|   |-- check_object_centric_graph_conformance.py
|   |-- inspect_ocel.py
|   |-- inspect_order_candidates.py
|   |-- run_order_management_discovered.py
|   |-- run_order_management_real.py
|   |-- run_order_management_toy.py
|   |-- run_toy_example.py
|   |-- screen_order_executions.py
|   `-- verify_real_execution.py
|
|-- src/ocpm_partial_order/
|   |-- config.py
|   |-- conformance/
|   |   |-- __init__.py
|   |   |-- holdout_validation.py
|   |   |-- object_centric_graph_validation.py
|   |   `-- object_type_replay.py
|   |-- discovery/
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
|   |-- test_holdout_validation.py
|   |-- test_object_centric_graph_validation.py
|   |-- test_object_type_conformance.py
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

Il dataset in `data/raw/` resta locale. Il file in `data/derived/` rappresenta la baseline manuale riproducibile.

---

## 10. Installazione su Windows

### Prerequisiti

- Python 3.11 o 3.12;
- Git;
- Graphviz.

Verifica di Python:

```powershell
python --version
```

Verifica di Graphviz:

```powershell
dot -V
```

### Creazione dell’ambiente virtuale

```powershell
python -m venv .venv
```

Aggiornamento di `pip`:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

Installazione del progetto con dipendenze di sviluppo:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Non è necessario attivare l’ambiente virtuale se si invoca direttamente il relativo eseguibile Python.

### Dataset

Copiare il dataset nel percorso:

```text
data/raw/order_management.sqlite
```

---

## 11. Esecuzione

Tutti i comandi seguenti devono essere eseguiti dalla radice del repository.

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
.\.venv\Scripts\python.exe .\scripts\run_toy_example.py
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

### Screening delle 22 process execution

```powershell
.\.venv\Scripts\python.exe .\scripts\screen_order_executions.py
```

### Conformance checking per tipo di oggetto

```powershell
.\.venv\Scripts\python.exe .\scripts\check_object_type_conformance.py
```

Lo script controlla la process execution di riferimento e tutte le proiezioni strutturali:

```text
proiezioni strutturali: 10787
proiezioni conformi: 10787
proiezioni non conformi: 0
token mancanti: 0
token residui: 0
```

### Validazione out-of-sample senza leakage

```powershell
.\.venv\Scripts\python.exe .\scripts\check_out_of_sample_conformance.py
```

Lo script costruisce uno split component-aware, scopre le Petri net soltanto sui training set e valuta 2.202 tracce di test. Stampa inoltre precisione, generalizzazione e semplicità per ciascun tipo di oggetto.

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
6. `06_real_execution.ipynb`;
7. `07_conformance_checking.ipynb`;
8. `08_out_of_sample_validation.ipynb`;
9. `09_object_centric_graph_conformance.ipynb`.

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
celle totali: 24
celle di codice: 9
celle eseguite: 9
errori: 0
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
celle totali: 22
celle di codice: 10
celle eseguite: 10
errori: 0
validazione notebook: superata
```

### Notebook 07

Documenta:

- il conformance checking per tipo di oggetto;
- le proiezioni `orders`, `items` e `packages`;
- il token-based replay rispetto alle Petri net componenti;
- la conformità delle proiezioni di `o-990424`;
- il riepilogo sulle 10.787 proiezioni strutturali;
- un controllo negativo con la rimozione dell’attività finale;
- la distinzione tra fitness delle proiezioni e fitness object-centric globalmente sincronizzata;
- il carattere in-sample dell’esperimento.

Validazione:

```text
celle totali: 16
celle di codice: 8
celle eseguite: 8
errori salvati: 0
validazione notebook: superata
```

Esecuzione non interattiva del notebook 07:

```powershell
.\.venv\Scripts\python.exe -m jupyter nbconvert `
    --to notebook `
    --execute `
    --inplace `
    .\notebooks\07_conformance_checking.ipynb `
    --ExecutePreprocessor.timeout=600
```

### Notebook 08

Documenta:

- il leakage prodotto da uno split ingenuo dei casi;
- le 131 condivisioni di evento rilevate per `items`;
- la costruzione dello split per componenti connesse;
- la discovery eseguita esclusivamente sui training set;
- il token-based replay su 2.202 tracce out-of-sample;
- precisione, generalizzazione e semplicità dei modelli;
- la bassa precisione della componente `items`;
- i limiti della validazione component-aware.

Validazione:

```text
celle totali: 16
celle di codice: 7
celle eseguite: 7
errori salvati: 0
validazione notebook: superata
```

Esecuzione non interattiva del notebook 08:

```powershell
.\.venv\Scripts\python.exe -m jupyter nbconvert `
    --to notebook `
    --execute `
    --inplace `
    --ExecutePreprocessor.timeout=600 `
    .\notebooks\08_out_of_sample_validation.ipynb
```

Gli avvisi ZMQ relativi al Proactor event loop e al TCP locale non indicano un errore del notebook. La verifica rilevante è l’assenza di output con `output_type = error`.

---

## 13. Test automatici

Esecuzione completa:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Risultato verificato:

```text
56 passed
```

La suite comprende:

| Area | Verifica |
| --- | --- |
| caricamento | parsing degli input sintetici |
| modello dati | eventi e oggetti |
| grafo | nodi, archi, DAG e riduzione transitiva |
| incomparabilità | rami causali distinti |
| linearizzazioni | stesso grafo per ordini temporali equivalenti |
| adapter | conversione dell’OCEL nel modello interno |
| estrazione | delimitazione order-centred |
| baseline reale | proprietà di `o-990424` |
| scoring | dependency e supporto relativo |
| self-loop | calcolo e filtraggio delle auto-relazioni |
| discovery reale | relazioni automatiche attese |
| loop reali | catene di `failed delivery` |
| oggetti differenti | attività uguali lasciate incomparabili |
| screening | validazione strutturale di 22 execution |
| conformance | replay delle proiezioni e diagnostica di fitness |
| holdout | split senza leakage e validazione out-of-sample |
| qualità | precisione, generalizzazione e semplicità |
| controllo negativo | riconoscimento di una traccia incompleta |

I sei test di conformance verificano:

- conformità delle proiezioni della process execution di riferimento;
- aggregazione delle misure di fitness;
- conformità delle 1.128 proiezioni dei pacchi;
- riconoscimento di una traccia incompleta;
- rifiuto di un tipo di oggetto sconosciuto;
- rifiuto di un identificatore di oggetto sconosciuto.

Gli otto test di holdout verificano:

- assegnazione congiunta dei casi che condividono eventi;
- rifiuto di rapporti di training non validi;
- rifiuto di log privi delle colonne richieste;
- rifiuto di log costituiti da una sola componente connessa;
- valutazione reale out-of-sample delle proiezioni `packages`.

---

## 14. Risultati dimostrati

Il progetto dimostra:

- caricamento ed esplorazione del dataset OCEL 2.0;
- discovery preliminare della OCPN;
- modello dati interno indipendente da PM4Py;
- costruzione dell’Instance Graph sintetico;
- equivalenza di linearizzazioni temporali indipendenti;
- estrazione order-centred di process execution reali;
- baseline manuale per `o-990424`;
- derivazione automatica dall’OC-DFG;
- scoring mediante dependency e supporto relativo;
- gestione dei self-loop di lunghezza 1;
- derivazione di 26 causal relations;
- corrispondenza esatta con la baseline di `o-990424`;
- screening di 22 process execution reali;
- 22 grafi DAG, connessi e transitivamente ridotti;
- assenza di eventi isolati e ripetizioni sospette;
- ordinamento delle ripetizioni sullo stesso oggetto;
- conservazione dell’incomparabilità su oggetti differenti;
- token-based replay sulle proiezioni `orders`, `items` e `packages`;
- conformità delle 10.787 proiezioni alle rispettive Petri net componenti;
- fitness media delle proiezioni pari a 1;
- assenza di token mancanti e residui nelle proiezioni complete;
- riconoscimento di tracce alterate mediante controlli negativi;
- split component-aware senza identificatori di caso o evento condivisi;
- discovery delle Petri net eseguita esclusivamente sui training set;
- conformità di 2.202 tracce out-of-sample;
- fitness out-of-sample media pari a 1 e assenza di token devianti;
- precisione out-of-sample superiore a 0,99 per `orders` e `packages`;
- individuazione della bassa precisione della componente `items`;
- calcolo di precisione, generalizzazione e semplicità;
- esecuzione senza errori dei notebook 05, 06, 07, 08 e 09;
- superamento di 56 test automatici.

---

## 15. Risultati non ancora dimostrati

Il progetto non dimostra ancora:

- fitness object-centric globalmente sincronizzata pari a 1;
- conformance checking con sincronizzazione simultanea tra tipi di oggetto;
- token-based replay object-centric globale;
- object-centric alignment;
- repairing della process execution;
- gestione generale di eventi mancanti o aggiuntivi;
- generalizzazione su un dataset esterno indipendente;
- holdout strettamente future-only per la componente `items`;
- validità delle soglie su tutte le 2.000 process execution;
- correttezza su dataset differenti;
- gestione generale di loop complessi;
- disambiguazione generale di transizioni diverse con la stessa etichetta;
- derivazione diretta dalla semantica della OCPN;
- equivalenza generale tra OC-DFG filtrato e causalità del modello;
- identificazione certa del parallelismo reale dalla sola incomparabilità;
- scalabilità della costruzione dei grafi su tutte le process execution del log.

I risultati ottenuti costituiscono una verifica sperimentale sul dataset e sui casi selezionati, non una dimostrazione universale.

---

## 16. Riproducibilità

Verifica dell’ambiente:

```powershell
.\.venv\Scripts\python.exe .\scripts\check_environment.py
```

Esecuzione della suite completa:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Esecuzione dello screening:

```powershell
.\.venv\Scripts\python.exe .\scripts\screen_order_executions.py
```

Esecuzione del conformance checking:

```powershell
.\.venv\Scripts\python.exe .\scripts\check_object_type_conformance.py
```

Esecuzione della validazione out-of-sample:

```powershell
.\.venv\Scripts\python.exe .\scripts\check_out_of_sample_conformance.py
```

Esecuzione dei notebook conclusivi:

```powershell
.\.venv\Scripts\python.exe -m jupyter nbconvert `
    --to notebook `
    --execute `
    --inplace `
    --ExecutePreprocessor.timeout=600 `
    .\notebooks\07_conformance_checking.ipynb

.\.venv\Scripts\python.exe -m jupyter nbconvert `
    --to notebook `
    --execute `
    --inplace `
    --ExecutePreprocessor.timeout=600 `
    .\notebooks\08_out_of_sample_validation.ipynb
```

Controllo finale del repository:

```powershell
git diff --check
git status --short
```

Per riprodurre completamente gli esperimenti è necessario disporre localmente del dataset `order_management.sqlite`.

---

## 17. Riferimenti

- W. M. P. van der Aalst, *Object-Centric Process Mining: Dealing With Divergence and Convergence in Event Data*.
- A. Berti, S. J. van Zelst e W. M. P. van der Aalst, *Process Mining for Python (PM4Py): Bridging the Gap Between Process- and Data Science*.
- J. N. Adams et al., *Defining Cases and Variants for Object-Centric Event Data*.
- [OCEL standard](https://www.ocel-standard.org/).
- [PM4Py](https://github.com/process-intelligence-solutions/pm4py).
- [NetworkX](https://networkx.org/).

---

## Autori

**Nicolò Ianni**
**Danilo La Palombara**
