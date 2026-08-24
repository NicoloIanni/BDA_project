from pathlib import Path

import networkx as nx
import pm4py
import pytest

from ocpm_partial_order.config import (
    MAIN_DATASET_DB,
)
from ocpm_partial_order.discovery import (
    derive_causal_relations,
)
from ocpm_partial_order.domain.causal_relation import (
    CausalRelation,
)
from ocpm_partial_order.extraction import (
    extract_order_centred_execution,
)
from ocpm_partial_order.graphs.instance_graph import (
    build_instance_graph,
)
from ocpm_partial_order.io.ocel_loader import (
    load_ocel2_sqlite,
)


STRUCTURAL_TYPES = {
    "orders",
    "items",
    "packages",
}

ORDER_IDS = {
    "two_failures": "o-990254",
    "seven_failures": "o-990042",
    "different_items": "o-990878",
}

EXPECTED_SELF_RELATIONS = {
    CausalRelation(
        source_activity="failed delivery",
        target_activity="failed delivery",
        object_type="items",
    ),
    CausalRelation(
        source_activity="failed delivery",
        target_activity="failed delivery",
        object_type="packages",
    ),
    CausalRelation(
        source_activity="payment reminder",
        target_activity="payment reminder",
        object_type="items",
    ),
    CausalRelation(
        source_activity="payment reminder",
        target_activity="payment reminder",
        object_type="orders",
    ),
}


@pytest.fixture(scope="module")
def real_loop_result() -> tuple[
    set[CausalRelation],
    dict[str, nx.DiGraph],
]:
    dataset_path = Path(MAIN_DATASET_DB)

    if not dataset_path.is_file():
        pytest.skip(
            "Dataset reale non disponibile: "
            f"{dataset_path}"
        )

    ocel = load_ocel2_sqlite(dataset_path)
    ocdfg = pm4py.discover_ocdfg(ocel)

    causal_relations = derive_causal_relations(
        ocdfg=ocdfg,
        object_types=STRUCTURAL_TYPES,
    )

    graphs = {}

    for order_id in ORDER_IDS.values():
        execution = (
            extract_order_centred_execution(
                ocel=ocel,
                order_id=order_id,
            )
        )

        graphs[order_id] = build_instance_graph(
            execution=execution,
            causal_relations=causal_relations,
        )

    return causal_relations, graphs


def _nodes_with_activity(
    graph: nx.DiGraph,
    activity: str,
) -> list[str]:
    return sorted(
        (
            node
            for node, attributes
            in graph.nodes(data=True)
            if attributes["activity"] == activity
        ),
        key=lambda node: (
            graph.nodes[node]["timestamp"],
            node,
        ),
    )


def _internal_edges(
    graph: nx.DiGraph,
    nodes: list[str],
) -> set[tuple[str, str]]:
    node_set = set(nodes)

    return {
        (source, target)
        for source, target in graph.edges
        if source in node_set
        and target in node_set
    }


def test_expected_self_relations_are_discovered(
    real_loop_result: tuple[
        set[CausalRelation],
        dict[str, nx.DiGraph],
    ],
) -> None:
    causal_relations, _ = real_loop_result

    discovered_self_relations = {
        relation
        for relation in causal_relations
        if relation.source_activity
        == relation.target_activity
    }

    assert (
        discovered_self_relations
        == EXPECTED_SELF_RELATIONS
    )


def test_two_failed_deliveries_form_a_chain(
    real_loop_result: tuple[
        set[CausalRelation],
        dict[str, nx.DiGraph],
    ],
) -> None:
    _, graphs = real_loop_result

    graph = graphs[
        ORDER_IDS["two_failures"]
    ]

    failed_nodes = _nodes_with_activity(
        graph,
        "failed delivery",
    )

    assert failed_nodes == [
        "fail_p-660164_54",
        "fail_p-660164_56",
    ]

    expected_edges = {
        (
            "fail_p-660164_54",
            "fail_p-660164_56",
        )
    }

    assert (
        _internal_edges(
            graph,
            failed_nodes,
        )
        == expected_edges
    )

    assert nx.has_path(
        graph,
        failed_nodes[0],
        failed_nodes[-1],
    )


def test_seven_failed_deliveries_form_a_chain(
    real_loop_result: tuple[
        set[CausalRelation],
        dict[str, nx.DiGraph],
    ],
) -> None:
    _, graphs = real_loop_result

    graph = graphs[
        ORDER_IDS["seven_failures"]
    ]

    failed_nodes = _nodes_with_activity(
        graph,
        "failed delivery",
    )

    assert failed_nodes == [
        "fail_p-660027_4",
        "fail_p-660027_6",
        "fail_p-660027_7",
        "fail_p-660027_8",
        "fail_p-660027_9",
        "fail_p-660027_11",
        "fail_p-660027_12",
    ]

    expected_edges = set(
        zip(
            failed_nodes,
            failed_nodes[1:],
        )
    )

    assert (
        _internal_edges(
            graph,
            failed_nodes,
        )
        == expected_edges
    )

    assert nx.has_path(
        graph,
        failed_nodes[0],
        failed_nodes[-1],
    )


def test_pick_events_of_different_items_remain_incomparable(
    real_loop_result: tuple[
        set[CausalRelation],
        dict[str, nx.DiGraph],
    ],
) -> None:
    _, graphs = real_loop_result

    graph = graphs[
        ORDER_IDS["different_items"]
    ]

    pick_nodes = _nodes_with_activity(
        graph,
        "pick item",
    )

    assert pick_nodes == [
        "pick_i-883511",
        "pick_i-883512",
    ]

    first_pick, second_pick = pick_nodes

    assert not nx.has_path(
        graph,
        first_pick,
        second_pick,
    )
    assert not nx.has_path(
        graph,
        second_pick,
        first_pick,
    )


def test_real_loop_graphs_are_reduced_dags(
    real_loop_result: tuple[
        set[CausalRelation],
        dict[str, nx.DiGraph],
    ],
) -> None:
    _, graphs = real_loop_result

    for graph in graphs.values():
        assert nx.is_directed_acyclic_graph(
            graph
        )

        reduced_again = (
            nx.transitive_reduction(graph)
        )

        assert set(reduced_again.edges) == set(
            graph.edges
        )