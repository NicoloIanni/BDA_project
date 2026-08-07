from pathlib import Path

import networkx as nx

from ocpm_partial_order.config import MAIN_DATASET_DB
from ocpm_partial_order.extraction import (
    extract_order_centred_execution,
)
from ocpm_partial_order.graphs.concurrency import (
    find_incomparable_event_pairs,
)
from ocpm_partial_order.graphs.instance_graph import (
    build_instance_graph,
)
from ocpm_partial_order.io.ocel_loader import (
    load_ocel2_sqlite,
)
from ocpm_partial_order.io.sample_loader import (
    load_causal_relations,
)
from ocpm_partial_order.visualization.graph_visualizer import (
    save_instance_graph,
)


ORDER_ID = "o-990424"

RELATIONS_PATH = Path(
    "data/derived/"
    "order_management_o_990424_causal_relations.json"
)

EXPECTED_EDGES = {
    (
        "place_o-990424",
        "confirm_o-990424",
    ),
    (
        "confirm_o-990424",
        "pay_o-990424",
    ),
    (
        "place_o-990424",
        "pick_i-881734",
    ),
    (
        "pick_i-881734",
        "create_p-660247",
    ),
    (
        "create_p-660247",
        "send_p-660247",
    ),
    (
        "send_p-660247",
        "deliver_p-660247",
    ),
}


def main() -> None:
    ocel = load_ocel2_sqlite(MAIN_DATASET_DB)

    execution = extract_order_centred_execution(
        ocel=ocel,
        order_id=ORDER_ID,
    )

    causal_relations = load_causal_relations(
        RELATIONS_PATH
    )

    graph = build_instance_graph(
        execution=execution,
        causal_relations=causal_relations,
    )

    print("Instance Graph reale")
    print("--------------------")
    print("Ordine:", ORDER_ID)
    print("Nodi:", graph.number_of_nodes())
    print("Archi:", graph.number_of_edges())
    print(
        "DAG:",
        nx.is_directed_acyclic_graph(graph),
    )

    print("\nNodi:")
    ordered_nodes = sorted(
        graph.nodes,
        key=lambda node: (
            graph.nodes[node]["timestamp"],
            node,
        ),
    )

    for node in ordered_nodes:
        attributes = graph.nodes[node]

        print(
            f"- {node}: "
            f"{attributes['activity']} | "
            f"{attributes['timestamp'].isoformat()}"
        )

    print("\nArchi causali:")
    for source, target in sorted(graph.edges):
        attributes = graph.edges[source, target]

        print(
            f"- {source} -> {target} | "
            f"types={sorted(attributes['object_types'])} | "
            f"ids={sorted(attributes['object_ids'])}"
        )

    incomparable_pairs = (
        find_incomparable_event_pairs(graph)
    )

    print("\nCoppie incomparabili:")
    for first, second in sorted(incomparable_pairs):
        print(
            f"- {first} || {second}"
        )

    assert graph.number_of_nodes() == 7
    assert set(graph.edges) == EXPECTED_EDGES
    assert nx.is_directed_acyclic_graph(graph)

    reduced_again = nx.transitive_reduction(graph)

    assert set(reduced_again.edges) == set(
        graph.edges
    ), (
        "Il grafo restituito contiene ancora "
        "archi transitivi ridondanti"
    )

    assert not nx.has_path(
        graph,
        "pay_o-990424",
        "deliver_p-660247",
    )
    assert not nx.has_path(
        graph,
        "deliver_p-660247",
        "pay_o-990424",
    )

    output_path = save_instance_graph(
        graph,
        Path(
            "outputs/graphs/"
            "order_management_o_990424_"
            "instance_graph.png"
        ),
    )

    print("\nVERIFICA GRAFO REALE SUPERATA")
    print("Grafo salvato in:")
    print(output_path.resolve())
    print(
        "\nNota: le causal relations sono "
        "state definite manualmente; "
        "non sono ancora derivate dall'OCPN."
    )


if __name__ == "__main__":
    main()
