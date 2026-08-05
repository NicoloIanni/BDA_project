# OCPM Partial Order - Order Management Prototype

## 1. Descrizione del progetto

Questo progetto ha l'obiettivo di costruire una rappresentazione a **ordine parziale** di una **process execution object-centric**, partendo dal dominio **Order Management**.

Nel process mining tradizionale, un processo viene spesso rappresentato come una sequenza totale di eventi associata a un singolo *case*.  
Nel contesto **object-centric**, invece, gli eventi possono essere associati contemporaneamente a più oggetti di tipo diverso, ad esempio:

- `orders`
- `items`
- `packages`
- `customers`
- `employees`
- `products`

Questo rende inadeguata una rappresentazione puramente sequenziale, perché alcune differenze tra tracce possono dipendere soltanto dall'ordine temporale registrato nel log e non da una vera dipendenza causale.

L'obiettivo del progetto è quindi costruire un **Instance Graph object-centric**, cioè un grafo che:

- rappresenti gli eventi come nodi;
- rappresenti le dipendenze causali come archi;
- evidenzi implicitamente gli eventi indipendenti o incomparabili;
- permetta di trattare come equivalenti due diverse linearizzazioni dello stesso comportamento concorrente.

---

## 2. Contesto metodologico

Il lavoro prende ispirazione da approcci basati sugli **Instance Graphs** e si colloca nel contesto dell'**Object-Centric Process Mining (OCPM)**.

L'idea generale è la seguente:

1. partire da una process execution object-centric;
2. assumere inizialmente note le **causal relations**;
3. costruire un grafo diretto aciclico che rappresenti solo le precedenze causali necessarie;
4. distinguere tra:
   - ordine temporale del log;
   - ordine causale effettivo del comportamento.

Nella prima versione del progetto non vengono gestiti:

- object-centric alignments;
- repairing;
- calcolo automatico della fitness;
- estrazione automatica delle causal relations;
- loop complessi e attività ripetute problematiche.

---

## 3. Dataset utilizzato

Il dataset principale del progetto è:

- **Order Management** (`order_management.sqlite`)

Questo dataset è un log object-centric in formato **OCEL 2.0 SQLite** e descrive la gestione degli ordini all'interno di un'azienda, includendo attività commerciali, logistiche e di spedizione.

Nella fase attuale del progetto non viene ancora usata una process execution reale estratta automaticamente dal dataset completo.  
Per il primo prototipo è stata costruita una **toy execution** semplificata ma coerente con il dominio Order Management.

---

## 4. Obiettivo del primo prototipo

Il primo prototipo ha un obiettivo volutamente limitato e controllato:

- ricevere una **process execution** già definita;
- ricevere un insieme di **causal relations** definite manualmente;
- costruire il corrispondente **Instance Graph**;
- verificare che il grafo sia:
  - corretto,
  - aciclico,
  - robusto rispetto a differenti ordinamenti temporali di eventi indipendenti.

In particolare, il prototipo deve dimostrare che:

> due esecuzioni con lo stesso comportamento causale ma con ordine temporale diverso per eventi incomparabili producono lo stesso grafo.

---

## 5. Struttura del progetto

```text
ocpm-partial-order/
│
├── data/
│   ├── raw/
│   │   └── order_management.sqlite
│   └── samples/
│       ├── order_management_toy_execution.json
│       ├── order_management_toy_execution_reordered.json
│       └── order_management_toy_causal_relations.json
│
├── notebooks/
│   ├── 01_environment_check.ipynb
│   ├── 02_ocel_exploration.ipynb
│   └── 03_ocpn_discovery.ipynb
│
├── outputs/
│   ├── figures/
│   ├── graphs/
│   │   └── order_management_toy_instance_graph.png
│   ├── reports/
│   └── tables/
│
├── scripts/
│   ├── check_environment.py
│   ├── inspect_ocel.py
│   └── run_order_management_toy.py
│
├── src/
│   └── ocpm_partial_order/
│       ├── config.py
│       ├── discovery/
│       │   └── ocpn_discovery.py
│       ├── domain/
│       │   ├── causal_relation.py
│       │   ├── event.py
│       │   └── process_execution.py
│       ├── extraction/
│       │   └── execution_adapter.py
│       ├── graphs/
│       │   ├── concurrency.py
│       │   ├── instance_graph.py
│       │   └── validation.py
│       ├── io/
│       │   ├── ocel_loader.py
│       │   └── sample_loader.py
│       └── visualization/
│           └── graph_visualizer.py
│
├── tests/
│   ├── test_concurrency.py
│   ├── test_equivalent_linearizations.py
│   ├── test_instance_graph.py
│   └── test_sample_loader.py
│
├── pyproject.toml
├── requirements.txt
└── README.md# Object-Centric Partial-Order Instance Graphs

## Descrizione

Questo progetto studia la costruzione di **Instance Graph a ordine parziale** per processi **object-centric**, utilizzando come dataset principale **Order Management** in formato **OCEL 2.0 SQLite**.

Nel process mining tradizionale ogni evento viene normalmente associato a un singolo caso. In un log object-centric, invece, uno stesso evento può coinvolgere più oggetti appartenenti a tipi differenti, per esempio:

- `orders`
- `items`
- `packages`
- `customers`
- `employees`
- `products`

Una semplice sequenza temporale rischia quindi di introdurre dipendenze che non sono realmente causali. Il progetto prova a rappresentare soltanto le precedenze causali rilevanti, lasciando incomparabili gli eventi per i quali non è nota una relazione d'ordine.

---

## Obiettivo del primo prototipo

Il primo prototipo riceve:

1. una process execution object-centric già definita;
2. gli eventi e le relative attività;
3. i timestamp;
4. gli oggetti coinvolti in ogni evento;
5. i tipi degli oggetti;
6. un insieme di causal relations già disponibili.

L'output è un **grafo diretto aciclico** nel quale:

- ogni nodo rappresenta un evento;
- ogni arco rappresenta una dipendenza causale;
- gli archi possono essere associati agli object type che li giustificano;
- gli archi transitivi ridondanti vengono rimossi;
- gli eventi senza un percorso causale reciproco risultano incomparabili.

### Assunzioni attuali

La prima versione considera esclusivamente:

- process executions controllate e considerate conformi;
- causal relations definite manualmente;
- assenza di eventi mancanti o aggiuntivi;
- assenza di repairing;
- assenza di object-centric alignment;
- esempi senza loop complessi o ripetizioni ambigue.

La fitness non viene ancora calcolata automaticamente. Le execution reali saranno inizialmente verificate manualmente rispetto al modello.

---

## Dataset

Il dataset principale è:

```text
data/raw/order_management.sqlite
```

Il file non deve essere caricato nel repository Git perché è un dato esterno e può avere dimensioni elevate.

Il dataset descrive un processo di gestione degli ordini con eventi relativi a:

- creazione e conferma degli ordini;
- pagamento;
- gestione degli item;
- preparazione dei package;
- spedizione e consegna.

---

## Struttura del progetto

```text
ocpm-partial-order/
│
├── data/
│   ├── raw/
│   │   └── order_management.sqlite
│   └── samples/
│       ├── order_management_toy_execution.json
│       ├── order_management_toy_execution_reordered.json
│       └── order_management_toy_causal_relations.json
│
├── notebooks/
│   ├── 01_environment_check.ipynb
│   ├── 02_ocel_exploration.ipynb
│   └── 03_ocpn_discovery.ipynb
│
├── outputs/
│   ├── figures/
│   ├── graphs/
│   │   └── order_management_toy_instance_graph.png
│   ├── reports/
│   └── tables/
│
├── scripts/
│   ├── check_environment.py
│   ├── inspect_ocel.py
│   └── run_order_management_toy.py
│
├── src/
│   └── ocpm_partial_order/
│       ├── config.py
│       ├── discovery/
│       │   └── ocpn_discovery.py
│       ├── domain/
│       │   ├── causal_relation.py
│       │   ├── event.py
│       │   └── process_execution.py
│       ├── extraction/
│       │   └── execution_adapter.py
│       ├── graphs/
│       │   ├── concurrency.py
│       │   ├── instance_graph.py
│       │   └── validation.py
│       ├── io/
│       │   ├── ocel_loader.py
│       │   └── sample_loader.py
│       └── visualization/
│           └── graph_visualizer.py
│
├── tests/
│   ├── test_concurrency.py
│   ├── test_equivalent_linearizations.py
│   ├── test_instance_graph.py
│   └── test_sample_loader.py
│
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## Ambiente di sviluppo

Il progetto è stato avviato con:

- Python 3.12
- PM4Py
- Pandas
- NetworkX
- Graphviz
- Pytest
- Jupyter
- Visual Studio Code

### Creazione dell'ambiente virtuale

Da PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Installazione del progetto

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### Verifica dell'ambiente

```powershell
python scripts/check_environment.py
```

---

## Caricamento di Order Management

Il dataset viene caricato tramite PM4Py usando il loader definito nel progetto.

Esempio:

```python
from ocpm_partial_order.config import MAIN_DATASET_DB
from ocpm_partial_order.io.ocel_loader import load_ocel2_sqlite

ocel = load_ocel2_sqlite(MAIN_DATASET_DB)
```

Lo script di ispezione può essere eseguito con:

```powershell
python scripts/inspect_ocel.py
```

Lo script mostra:

- colonne delle tabelle;
- numero di eventi;
- numero di oggetti;
- numero di relazioni evento-oggetto;
- attività;
- tipi di oggetto.

---

## Modello dati interno

Il progetto non usa direttamente le classi interne di PM4Py per costruire l'Instance Graph. È stato introdotto un modello indipendente dal tool.

### `ObjectReference`

Rappresenta un oggetto coinvolto in un evento:

```text
object_id
object_type
```

### `ExecutionEvent`

Rappresenta un evento della process execution:

```text
event_id
activity
timestamp
objects
```

### `ProcessExecution`

Rappresenta una singola esecuzione object-centric come insieme di eventi.

### `CausalRelation`

Rappresenta una relazione causale tra due attività rispetto a uno specifico object type:

```text
source_activity
target_activity
object_type
```

Questa separazione permette di sostituire in futuro PM4Py, OCPA o il metodo di estrazione senza riscrivere l'algoritmo principale.

---

## Algoritmo del primo Instance Graph

La versione attuale esegue i seguenti passaggi:

1. valida la process execution;
2. crea un nodo per ogni evento;
3. raccoglie gli eventi appartenenti al ciclo di vita di ciascun oggetto;
4. ordina gli eventi di ogni oggetto per timestamp;
5. confronta le coppie di attività con le causal relations;
6. aggiunge un arco quando la relazione causale è valida;
7. associa all'arco gli object type e gli object ID che lo giustificano;
8. verifica che il grafo sia aciclico;
9. applica la transitive reduction;
10. restituisce il DAG risultante.

La transitive reduction elimina gli archi ridondanti mantenendo invariata la raggiungibilità tra i nodi.

---

## Toy example Order Management

Il primo esempio controllato contiene le attività:

1. `place order`
2. `confirm order`
3. `pay order`
4. `pick item`
5. `create package`
6. `send package`
7. `package delivered`

Il comportamento causale atteso è:

```text
                 confirm order → pay order
                /
place order ───
                \
                 pick item → create package → send package → package delivered
```

Dopo `place order` vengono rappresentati due rami:

- ramo amministrativo;
- ramo logistico.

Non è stata inserita una relazione causale tra i due rami.

---

## Incomparabilità e parallelismo

Due eventi sono definiti **incomparabili** quando:

- non esiste un percorso causale dal primo al secondo;
- non esiste un percorso causale dal secondo al primo.

Nel prototipo le coppie incomparabili sono considerate **candidate al parallelismo**.

Questa formulazione è intenzionalmente prudente: l'assenza di una relazione causale non dimostra che due eventi siano avvenuti nello stesso istante.

Esempio:

```text
confirm order || pick item
```

indica che il grafo non impone un ordine causale tra le due attività.

---

## Validazione con linearizzazioni equivalenti

Sono state create due versioni della stessa toy execution.

### Prima execution

```text
confirm order
pick item
```

### Seconda execution

```text
pick item
confirm order
```

Le due attività non sono collegate da una causal relation. Per questo motivo il diverso ordine temporale non deve modificare l'Instance Graph.

I grafi vengono confrontati tramite isomorfismo considerando:

- l'attività associata ai nodi;
- gli object type associati agli archi.

Il test è stato superato.

Questo dimostra che il prototipo non confonde automaticamente:

```text
ordine temporale
```

con:

```text
ordine causale
```

---

## Test automatici

La suite contiene attualmente cinque test:

1. caricamento della toy execution;
2. verifica che il grafo sia un DAG;
3. verifica degli archi causali attesi;
4. verifica dell'incomparabilità tra `confirm order` e `pick item`;
5. verifica dell'equivalenza tra due linearizzazioni temporali differenti.

Esecuzione:

```powershell
pytest -v
```

Risultato raggiunto:

```text
5 passed
```

---

## Esecuzione del toy example

Da PowerShell:

```powershell
.\.venv\Scripts\python.exe .\scripts\run_order_management_toy.py
```

Lo script:

- carica la toy execution;
- carica le causal relations;
- costruisce il grafo;
- stampa nodi e archi;
- individua le coppie incomparabili;
- genera l'immagine PNG.

Output:

```text
outputs/graphs/order_management_toy_instance_graph.png
```

---

## Stato del progetto

### Completato

- configurazione dell'ambiente;
- caricamento di Order Management;
- esplorazione iniziale dell'OCEL;
- modello dati interno;
- toy execution;
- causal relations manuali;
- costruzione del primo Instance Graph;
- transitive reduction;
- individuazione delle coppie incomparabili;
- visualizzazione Graphviz;
- cinque test automatici superati;
- verifica delle linearizzazioni equivalenti.

### Non ancora completato

- estrazione automatica di una process execution reale;
- selezione automatica delle execution con fitness uguale a 1;
- estrazione automatica delle causal relations dalla OCPN;
- object-centric alignment;
- repairing;
- gestione robusta di loop e attività ripetute;
- applicazione sistematica al dataset completo.

---

## Prossimi passi

Il prossimo blocco di lavoro prevede:

1. scoperta e ispezione della Object-Centric Petri Net di Order Management;
2. selezione di una process execution reale piccola;
3. conversione della execution nel modello interno;
4. verifica manuale della conformità;
5. applicazione dell'algoritmo alla execution reale;
6. confronto tra risultato sintetico e risultato reale.

L'estrazione della process execution deve restare separata dall'algoritmo di costruzione del grafo, in modo da non dipendere da connected components, leading type o da una specifica libreria.

---

## Autori

Progetto sviluppato da:

- Nicolò Ianni
- Danilo La Palombara

---

## Riferimenti

- C. Diamantini, D. Genga, D. Potena, W. M. P. van der Aalst, *Building Instance Graphs for Highly Variable Processes*, Expert Systems with Applications, 2016.
- J. N. Adams et al., *Defining Cases and Variants for Object-Centric Event Data*, International Conference on Process Mining, 2022.
- PM4Py Documentation: https://processintelligence.solutions/pm4py/
- NetworkX Documentation: https://networkx.org/documentation/stable/
- Graphviz Documentation: https://graphviz.org/documentation/
