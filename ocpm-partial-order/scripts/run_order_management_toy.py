from pathlib import Path

from ocpm_partial_order.graphs.concurrency import (
    find_incomparable_event_pairs,
)
from ocpm_partial_order.graphs.instance_graph import (
    build_instance_graph,
)
from ocpm_partial_order.io.sample_loader import (
    load_causal_relations,
    load_process_execution,
)
from ocpm_partial_order.visualization.graph_visualizer import (
    save_instance_graph,
)


def main() -> None:
    execution_path = Path(
        "data/samples/order_management_toy_execution.json"
    )

    relations_path = Path(
        "data/samples/order_management_toy_causal_relations.json"
    )

    execution = load_process_execution(execution_path)
    causal_relations = load_causal_relations(relations_path)

    graph = build_instance_graph(
        execution=execution,
        causal_relations=causal_relations,
    )

    incomparable_pairs = find_incomparable_event_pairs(graph)

    print("Nodi")
    for node_id, attributes in graph.nodes(data=True):
        print(
            f"- {node_id}: "
            f"{attributes.get('activity', '')}"
        )

    print("\nArchi causali")
    for source, target, attributes in graph.edges(data=True):
        print(
            f"- {source} -> {target} "
            f"{attributes}"
        )

    print("\nCoppie incomparabili")
    for first, second in sorted(incomparable_pairs):
        first_activity = graph.nodes[first].get(
            "activity",
            "",
        )
        second_activity = graph.nodes[second].get(
            "activity",
            "",
        )

        print(
            f"- {first} ({first_activity}) "
            f"|| {second} ({second_activity})"
        )

    output_path = save_instance_graph(
        graph,
        Path(
            "outputs/graphs/"
            "order_management_toy_instance_graph.png"
        ),
    )

    print("\nGrafo salvato in:")
    print(output_path.resolve())


if __name__ == "__main__":
    main()
