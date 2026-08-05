from pathlib import Path

import networkx as nx

from ocpm_partial_order.graphs.instance_graph import (
    build_instance_graph,
)
from ocpm_partial_order.io.sample_loader import (
    load_causal_relations,
    load_process_execution,
)


def test_reordered_parallel_events_produce_same_graph() -> None:
    """
    Verifica che due diversi ordinamenti temporali degli eventi
    incomparabili producano lo stesso Instance Graph.
    """

    original_execution = load_process_execution(
        Path(
            "data/samples/"
            "order_management_toy_execution.json"
        )
    )

    reordered_execution = load_process_execution(
        Path(
            "data/samples/"
            "order_management_toy_execution_reordered.json"
        )
    )

    causal_relations = load_causal_relations(
        Path(
            "data/samples/"
            "order_management_toy_causal_relations.json"
        )
    )

    original_graph = build_instance_graph(
        execution=original_execution,
        causal_relations=causal_relations,
    )

    reordered_graph = build_instance_graph(
        execution=reordered_execution,
        causal_relations=causal_relations,
    )

    node_match = (
        nx.algorithms.isomorphism.categorical_node_match(
            "activity",
            "",
        )
    )

    edge_match = (
        nx.algorithms.isomorphism.categorical_edge_match(
            "object_types",
            set(),
        )
    )

    assert nx.is_isomorphic(
        original_graph,
        reordered_graph,
        node_match=node_match,
        edge_match=edge_match,
    )