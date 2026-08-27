from types import SimpleNamespace

import pytest

from ocpm_partial_order.conformance import (
    instance_graph_holdout_validation as holdout_module,
)

from ocpm_partial_order.config import (
    MAIN_DATASET_DB,
)
from ocpm_partial_order.conformance.instance_graph_holdout_validation import (
    ExcludedOrderDiagnostic,
    InstanceGraphHoldoutResult,
    evaluate_instance_graph_holdout,
    evaluate_training_threshold_sensitivity,
    export_holdout_instance_graphs,
)
from ocpm_partial_order.io.ocel_loader import (
    load_ocel2_sqlite,
)


EXPECTED_GRAPHS = {
    "o-991144": (11, 11, 14),
    "o-991284": (8, 8, 8),
    "o-991324": (11, 11, 14),
    "o-991520": (11, 11, 12),
    "o-991630": (9, 9, 10),
    "o-991686": (10, 10, 12),
    "o-991749": (7, 7, 6),
    "o-991925": (11, 11, 14),
    "o-991982": (9, 9, 10),
}


@pytest.fixture(scope="module")
def real_evaluation():
    ocel = load_ocel2_sqlite(
        MAIN_DATASET_DB
    )

    return evaluate_instance_graph_holdout(
        ocel
    )


def test_result_reports_edge_differences():
    result = InstanceGraphHoldoutResult(
        order_id="o-test",
        event_count=3,
        node_count=3,
        edge_count=1,
        reference_edge_count=2,
        is_dag=True,
        is_weakly_connected=False,
        covers_all_events=True,
        is_transitively_reduced=True,
        training_edges=frozenset(
            {
                ("e1", "e2"),
            }
        ),
        reference_edges=frozenset(
            {
                ("e1", "e2"),
                ("e2", "e3"),
            }
        ),
    )

    assert result.missing_reference_edges == (
        frozenset(
            {
                ("e2", "e3"),
            }
        )
    )
    assert not result.additional_training_edges
    assert not result.exact_topology
    assert not result.is_structurally_valid


def test_training_only_sensitivity_reports_stability(
    monkeypatch,
):
    training_ocdfg = {
        "edges": {
            "event_couples": {
                "orders": {
                    ("place order", "pay order"): 20,
                }
            }
        }
    }
    monkeypatch.setattr(
        holdout_module.pm4py,
        "discover_ocdfg",
        lambda _: training_ocdfg,
    )

    sensitivity = evaluate_training_threshold_sensitivity(
        object(),
        object_types=("orders",),
        dependency_thresholds=(0.80, 0.90),
        relative_support_thresholds=(0.05,),
        self_loop_thresholds=(0.90,),
    )

    assert sensitivity.configuration_count == 2
    assert sensitivity.stable_configuration_count == 2
    assert len(sensitivity.default_relations) == 1


def test_exports_only_evaluated_training_graphs(
    monkeypatch,
    tmp_path,
):
    evaluation = SimpleNamespace(
        results=(SimpleNamespace(order_id="o-test"),),
        split=SimpleNamespace(test_ocel=object()),
        training_relations=frozenset(),
    )
    calls = []

    monkeypatch.setattr(
        holdout_module,
        "extract_order_centred_execution",
        lambda ocel, order_id: (ocel, order_id),
    )
    monkeypatch.setattr(
        holdout_module,
        "build_instance_graph",
        lambda execution, relations: (
            execution,
            relations,
        ),
    )

    def fake_save(graph, output_path):
        calls.append((graph, output_path))
        return output_path

    monkeypatch.setattr(
        holdout_module,
        "save_instance_graph",
        fake_save,
    )

    paths = export_holdout_instance_graphs(
        evaluation,
        tmp_path,
    )

    assert paths == (tmp_path / "o-test.png",)
    assert len(calls) == 1


def test_real_split_has_no_leakage(
    real_evaluation,
):
    split = real_evaluation.split

    assert split.component_count == 68
    assert split.training_component_count == 44
    assert split.test_component_count == 24
    assert split.shared_event_count == 0
    assert split.shared_object_count == 0


def test_training_relations_match_reference(
    real_evaluation,
):
    assert len(
        real_evaluation.training_relations
    ) == 26
    assert len(
        real_evaluation.reference_relations
    ) == 26
    assert (
        real_evaluation.exact_relation_set
    )
    assert not (
        real_evaluation
        .missing_training_relations
    )
    assert not (
        real_evaluation
        .additional_training_relations
    )


def test_test_orders_are_classified(
    real_evaluation,
):
    assert (
        real_evaluation.test_order_count
        == 436
    )
    assert (
        real_evaluation.excluded_order_count
        == 427
    )
    assert (
        real_evaluation.evaluated_order_count
        == 9
    )

    classified = (
        set(
            real_evaluation
            .excluded_order_ids
        )
        | {
            result.order_id
            for result in (
                real_evaluation.results
            )
        }
    )

    assert classified == set(
        real_evaluation.test_order_ids
    )
    assert real_evaluation.evaluation_coverage == pytest.approx(
        9 / 436
    )
    assert sum(
        real_evaluation.exclusion_reason_counts.values()
    ) == 427
    assert all(
        isinstance(item, ExcludedOrderDiagnostic)
        for item in real_evaluation.excluded_orders
    )


def test_all_evaluated_graphs_are_valid(
    real_evaluation,
):
    assert (
        real_evaluation.valid_graph_count
        == 9
    )
    assert (
        real_evaluation
        .all_evaluated_graphs_valid
    )

    for result in real_evaluation.results:
        assert result.is_dag
        assert result.is_weakly_connected
        assert result.covers_all_events
        assert (
            result
            .is_transitively_reduced
        )


def test_all_holdout_topologies_are_exact(
    real_evaluation,
):
    assert (
        real_evaluation.exact_topology_count
        == 9
    )
    assert (
        real_evaluation
        .all_topologies_exact
    )

    for result in real_evaluation.results:
        assert result.exact_topology
        assert not (
            result
            .missing_reference_edges
        )
        assert not (
            result
            .additional_training_edges
        )


@pytest.mark.parametrize(
    (
        "order_id",
        "expected",
    ),
    sorted(EXPECTED_GRAPHS.items()),
)
def test_real_graph_dimensions(
    real_evaluation,
    order_id,
    expected,
):
    by_order = {
        result.order_id: result
        for result in real_evaluation.results
    }

    result = by_order[order_id]

    assert (
        result.event_count,
        result.node_count,
        result.edge_count,
    ) == expected
    assert (
        result.reference_edge_count
        == result.edge_count
    )
