import pandas as pd
import pytest
from pm4py.objects.ocel.obj import OCEL

from ocpm_partial_order.config import (
    MAIN_DATASET_DB,
)
from ocpm_partial_order.conformance.object_centric_graph_validation import (
    compare_structural_sets,
    evaluate_object_centric_graph_holdout,
    filter_structural_ocel,
    split_object_centric_components,
    typed_ocdfg_flows,
)
from ocpm_partial_order.io.ocel_loader import (
    load_ocel2_sqlite,
)


EVENT_ID = "ocel:eid"
OBJECT_ID = "ocel:oid"
OBJECT_TYPE = "ocel:type"
ACTIVITY = "ocel:activity"
TIMESTAMP = "ocel:timestamp"
QUALIFIER = "ocel:qualifier"


def _synthetic_ocel(
    two_components: bool = True,
) -> OCEL:
    event_rows = [
        {
            EVENT_ID: "e1",
            ACTIVITY: "start",
            TIMESTAMP: pd.Timestamp(
                "2024-01-01",
                tz="UTC",
            ),
        },
    ]
    object_rows = [
        {
            OBJECT_ID: "o1",
            OBJECT_TYPE: "orders",
        },
        {
            OBJECT_ID: "i1",
            OBJECT_TYPE: "items",
        },
    ]
    relation_rows = [
        {
            EVENT_ID: "e1",
            OBJECT_ID: "o1",
            QUALIFIER: "",
            ACTIVITY: "start",
            TIMESTAMP: pd.Timestamp(
                "2024-01-01",
                tz="UTC",
            ),
            OBJECT_TYPE: "orders",
        },
        {
            EVENT_ID: "e1",
            OBJECT_ID: "i1",
            QUALIFIER: "",
            ACTIVITY: "start",
            TIMESTAMP: pd.Timestamp(
                "2024-01-01",
                tz="UTC",
            ),
            OBJECT_TYPE: "items",
        },
    ]

    if two_components:
        event_rows.append(
            {
                EVENT_ID: "e2",
                ACTIVITY: "finish",
                TIMESTAMP: pd.Timestamp(
                    "2024-02-01",
                    tz="UTC",
                ),
            }
        )
        object_rows.extend(
            [
                {
                    OBJECT_ID: "o2",
                    OBJECT_TYPE: "orders",
                },
                {
                    OBJECT_ID: "i2",
                    OBJECT_TYPE: "items",
                },
            ]
        )
        relation_rows.extend(
            [
                {
                    EVENT_ID: "e2",
                    OBJECT_ID: "o2",
                    QUALIFIER: "",
                    ACTIVITY: "finish",
                    TIMESTAMP: pd.Timestamp(
                        "2024-02-01",
                        tz="UTC",
                    ),
                    OBJECT_TYPE: "orders",
                },
                {
                    EVENT_ID: "e2",
                    OBJECT_ID: "i2",
                    QUALIFIER: "",
                    ACTIVITY: "finish",
                    TIMESTAMP: pd.Timestamp(
                        "2024-02-01",
                        tz="UTC",
                    ),
                    OBJECT_TYPE: "items",
                },
            ]
        )

    return OCEL(
        events=pd.DataFrame(event_rows),
        objects=pd.DataFrame(object_rows),
        relations=pd.DataFrame(relation_rows),
    )


def test_structural_set_comparison_is_symmetric() -> None:
    comparison = compare_structural_sets(
        training_elements={"a", "b"},
        test_elements={"b", "c"},
    )

    assert comparison.shared_elements == {
        "b",
    }
    assert comparison.additional_test_elements == {
        "c",
    }
    assert (
        comparison
        .training_elements_absent_from_test
        == {"a"}
    )
    assert comparison.test_coverage == 0.50
    assert comparison.training_coverage == 0.50
    assert comparison.jaccard == pytest.approx(
        1 / 3
    )


def test_typed_ocdfg_flows_preserve_object_type() -> None:
    model = {
        "edges": {
            "event_couples": {
                "orders": {
                    ("start", "finish"): [
                        ("e1", "e2"),
                    ],
                },
                "items": {
                    ("start", "finish"): [
                        ("e1", "e3"),
                    ],
                },
            },
        },
    }

    flows = typed_ocdfg_flows(model)

    assert flows == {
        (
            "orders",
            "start",
            "finish",
        ),
        (
            "items",
            "start",
            "finish",
        ),
    }


@pytest.mark.parametrize(
    "train_ratio",
    [
        -0.01,
        0.0,
        1.0,
        1.01,
    ],
)
def test_invalid_component_train_ratio_is_rejected(
    train_ratio: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="train_ratio",
    ):
        split_object_centric_components(
            ocel=_synthetic_ocel(),
            object_types=(
                "orders",
                "items",
            ),
            train_ratio=train_ratio,
        )


def test_missing_structural_type_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="assenti",
    ):
        filter_structural_ocel(
            ocel=_synthetic_ocel(),
            object_types=(
                "orders",
                "items",
                "packages",
            ),
        )


def test_component_split_has_no_leakage() -> None:
    split = split_object_centric_components(
        ocel=_synthetic_ocel(),
        object_types=(
            "orders",
            "items",
        ),
        train_ratio=0.50,
    )

    assert split.object_types == (
        "items",
        "orders",
    )
    assert split.component_count == 2
    assert split.training_component_count == 1
    assert split.test_component_count == 1
    assert split.training_event_count == 1
    assert split.test_event_count == 1
    assert split.training_object_count == 2
    assert split.test_object_count == 2
    assert split.shared_event_count == 0
    assert split.shared_object_count == 0
    assert split.effective_training_ratio == 0.50

    training_events = set(
        split.training_ocel.events[EVENT_ID]
    )
    test_events = set(
        split.test_ocel.events[EVENT_ID]
    )
    training_objects = set(
        split.training_ocel.objects[OBJECT_ID]
    )
    test_objects = set(
        split.test_ocel.objects[OBJECT_ID]
    )

    assert not training_events & test_events
    assert not training_objects & test_objects


def test_single_object_centric_component_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="sola componente",
    ):
        split_object_centric_components(
            ocel=_synthetic_ocel(
                two_components=False
            ),
            object_types=(
                "orders",
                "items",
            ),
            train_ratio=0.50,
        )


def test_real_object_centric_graph_holdout() -> None:
    ocel = load_ocel2_sqlite(
        MAIN_DATASET_DB
    )

    evaluation = (
        evaluate_object_centric_graph_holdout(
            ocel=ocel,
            object_types=(
                "orders",
                "items",
                "packages",
            ),
            train_ratio=0.80,
        )
    )

    split = evaluation.split

    assert split.component_count == 68
    assert split.training_component_count == 44
    assert split.test_component_count == 24
    assert split.training_event_count == 16547
    assert split.test_event_count == 4461
    assert split.training_object_count == 8531
    assert split.test_object_count == 2256
    assert split.shared_event_count == 0
    assert split.shared_object_count == 0
    assert (
        split.effective_training_ratio
        == pytest.approx(0.7877, abs=1e-4)
    )

    assert (
        evaluation.ocdfg_default_fitness
        == pytest.approx(
            0.4925373134328358
        )
    )
    assert (
        evaluation.ocdfg_structural_fitness
        == pytest.approx(
            0.9850746268656716
        )
    )
    assert (
        evaluation.otg_default_fitness
        == pytest.approx(
            0.5714285714285714
        )
    )
    assert (
        evaluation.otg_structural_fitness
        == pytest.approx(1.0)
    )
    assert (
        evaluation.etot_default_fitness
        == pytest.approx(
            0.6346153846153846
        )
    )
    assert (
        evaluation.etot_structural_fitness
        == pytest.approx(1.0)
    )

    assert (
        evaluation.ocdfg_activities
        .test_coverage
        == pytest.approx(1.0)
    )
    assert (
        evaluation.ocdfg_typed_flows
        .test_coverage
        == pytest.approx(1.0)
    )
    assert (
        evaluation.ocdfg_typed_flows
        .training_coverage
        == pytest.approx(
            64 / 66
        )
    )
    assert (
        evaluation.ocdfg_typed_flows
        .jaccard
        == pytest.approx(
            64 / 66
        )
    )

    assert not (
        evaluation.ocdfg_typed_flows
        .additional_test_elements
    )
    assert (
        evaluation.ocdfg_typed_flows
        .training_elements_absent_from_test
        == {
            (
                "items",
                "create package",
                "payment reminder",
            ),
            (
                "items",
                "payment reminder",
                "send package",
            ),
        }
    )

    assert (
        evaluation.otg_edges.test_coverage
        == pytest.approx(1.0)
    )
    assert (
        evaluation.otg_edges.jaccard
        == pytest.approx(1.0)
    )
    assert (
        evaluation.etot_relations
        .test_coverage
        == pytest.approx(1.0)
    )
    assert (
        evaluation.etot_relations.jaccard
        == pytest.approx(1.0)
    )