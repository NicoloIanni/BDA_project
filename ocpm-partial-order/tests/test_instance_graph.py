from pathlib import Path

import networkx as nx

from ocpm_partial_order.graphs.instance_graph import (
    build_instance_graph,
)
from ocpm_partial_order.io.sample_loader import (
    load_causal_relations,
    load_process_execution,
)


def build_toy_graph() -> nx.DiGraph:
    execution = load_process_execution(
        Path(
            "data/samples/"
            "order_management_toy_execution.json"
        )
    )

    relations = load_causal_relations(
        Path(
            "data/samples/"
            "order_management_toy_causal_relations.json"
        )
    )

    return build_instance_graph(
        execution,
        relations,
    )


def test_instance_graph_is_dag() -> None:
    graph = build_toy_graph()

    assert nx.is_directed_acyclic_graph(graph)


def test_expected_edges_exist() -> None:
    graph = build_toy_graph()

    assert graph.has_edge("e1", "e2")
    assert graph.has_edge("e2", "e3")
    assert graph.has_edge("e1", "e4")
    assert graph.has_edge("e4", "e5")
    assert graph.has_edge("e5", "e6")
    assert graph.has_edge("e6", "e7")