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
└── README.md