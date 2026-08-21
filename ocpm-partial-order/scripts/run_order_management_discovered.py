import networkx as nx
import pm4py

from ocpm_partial_order.config import (
    GRAPHS_DIR,
    MAIN_DATASET_DB,
)
from ocpm_partial_order.discovery import (
    derive_causal_relations,
    score_causal_relations,
)
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
from ocpm_partial_order.visualization.graph_visualizer import (
    save_instance_graph,
)


ORDER_ID = "o-990424"

DEPENDENCY_THRESHOLD = 0.90
RELATIVE_SUPPORT_THRESHOLD = 0.05

STRUCTURAL_TYPES = {
    "orders",
    "items",
    "packages",
}

EXPECTED_EDGE_OBJECTS = {
    (
        "place_o-990424",
        "confirm_o-990424",
    ): (
        {"items", "orders"},
        {"i-881734", "o-990424"},
    ),
    (
        "confirm_o-990424",
        "pay_o-990424",
    ): (
        {"items", "orders"},
        {"i-881734", "o-990424"},
    ),
    (
        "place_o-990424",
        "pick_i-881734",
    ): (
        {"items"},
        {"i-881734"},
    ),
    (
        "pick_i-881734",
        "create_p-660247",
    ): (
        {"items"},
        {"i-881734"},
    ),
    (
        "create_p-660247",
        "send_p-660247",
    ): (
        {"items", "packages"},
        {"i-881734", "p-660247"},
    ),
    (
        "send_p-660247",
        "deliver_p-660247",
    ): (
        {"items", "packages"},
        {"i-881734", "p-660247"},
    ),
}


def main() -> None:
    ocel = load_ocel2_sqlite(
        MAIN_DATASET_DB
    )

    ocdfg = pm4py.discover_ocdfg(ocel)

    evidence = score_causal_relations(
        ocdfg=ocdfg,
        object_types=STRUCTURAL_TYPES,
    )

    causal_relations = derive_causal_relations(
        ocdfg=ocdfg,
        dependency_threshold=(
            DEPENDENCY_THRESHOLD
        ),
        relative_support_threshold=(
            RELATIVE_SUPPORT_THRESHOLD
        ),
        object_types=STRUCTURAL_TYPES,
    )

    execution = extract_order_centred_execution(
        ocel=ocel,
        order_id=ORDER_ID,
    )

    execution_activities = {
        event.activity
        for event in execution.events
    }

    relevant_evidence = [
        item
        for item in evidence
        if item.relation in causal_relations
        and item.relation.source_activity
        in execution_activities
        and item.relation.target_activity
        in execution_activities
    ]

    graph = build_instance_graph(
        execution=execution,
        causal_relations=causal_relations,
    )

    print(
        "Instance Graph con causal relations "
        "derivate"
    )
    print("-------------------------------------")
    print("Ordine:", ORDER_ID)
    print(
        "Dependency threshold:",
        DEPENDENCY_THRESHOLD,
    )
    print(
        "Relative support threshold:",
        RELATIVE_SUPPORT_THRESHOLD,
    )
    print(
        "Causal relations totali:",
        len(causal_relations),
    )
    print(
        "Causal relations rilevanti:",
        len(relevant_evidence),
    )

    print("\nRelazioni rilevanti e misure:")

    for item in sorted(
        relevant_evidence,
        key=lambda value: (
            value.relation.source_activity,
            value.relation.target_activity,
            value.relation.object_type,
        ),
    ):
        relation = item.relation

        print(
            f"- {relation.source_activity} "
            f"-> {relation.target_activity} | "
            f"type={relation.object_type} | "
            f"forward="
            f"{item.forward_frequency} | "
            f"backward="
            f"{item.backward_frequency} | "
            f"dependency="
            f"{item.dependency:.3f} | "
            f"relative_support="
            f"{item.relative_support:.3f}"
        )

    print("\nInstance Graph:")
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
            f"types="
            f"{sorted(attributes['object_types'])} | "
            f"ids="
            f"{sorted(attributes['object_ids'])}"
        )

    incomparable_pairs = (
        find_incomparable_event_pairs(graph)
    )

    print("\nCoppie incomparabili:")

    for first, second in sorted(
        incomparable_pairs
    ):
        print(f"- {first} || {second}")

    assert graph.number_of_nodes() == 7
    assert set(graph.edges) == set(
        EXPECTED_EDGE_OBJECTS
    )
    assert nx.is_directed_acyclic_graph(graph)

    for edge, expected_attributes in (
        EXPECTED_EDGE_OBJECTS.items()
    ):
        expected_types, expected_ids = (
            expected_attributes
        )
        actual_attributes = graph.edges[edge]

        assert (
            actual_attributes["object_types"]
            == expected_types
        )
        assert (
            actual_attributes["object_ids"]
            == expected_ids
        )

    reduced_again = nx.transitive_reduction(
        graph
    )

    assert set(reduced_again.edges) == set(
        graph.edges
    ), (
        "Il grafo contiene ancora archi "
        "transitivi ridondanti"
    )

    assert len(incomparable_pairs) == 8

    assert not nx.has_path(
        graph,
        "confirm_o-990424",
        "pick_i-881734",
    )
    assert not nx.has_path(
        graph,
        "pick_i-881734",
        "confirm_o-990424",
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
        GRAPHS_DIR
        / (
            "order_management_o_990424_"
            "discovered_instance_graph.png"
        ),
    )

    print(
        "\nVERIFICA CON RELAZIONI "
        "DERIVATE SUPERATA"
    )
    print("Grafo salvato in:")
    print(output_path.resolve())
    print(
        "\nNota metodologica: le causal "
        "relations sono inferite dall'OC-DFG "
        "mediante dependency e supporto "
        "relativo. Non sono lette direttamente "
        "dagli archi della OCPN."
    )


if __name__ == "__main__":
    main()