import pytest

from ocpm_partial_order.discovery.causal_relations import (
    derive_causal_relations,
    score_causal_relations,
)
from ocpm_partial_order.domain.causal_relation import (
    CausalRelation,
)


def _occurrences(count: int) -> set[int]:
    return set(range(count))


@pytest.fixture
def synthetic_ocdfg() -> dict:
    return {
        "edges": {
            "event_couples": {
                "items": {
                    (
                        "place order",
                        "pick item",
                    ): _occurrences(1000),
                    (
                        "pick item",
                        "create package",
                    ): _occurrences(1000),
                    (
                        "create package",
                        "pick item",
                    ): _occurrences(10),
                    (
                        "pick item",
                        "send package",
                    ): _occurrences(20),
                }
            }
        }
    }


def test_score_causal_relations(
    synthetic_ocdfg: dict,
) -> None:
    evidence = score_causal_relations(
        ocdfg=synthetic_ocdfg,
        object_types={"items"},
    )

    by_activities = {
        (
            item.relation.source_activity,
            item.relation.target_activity,
        ): item
        for item in evidence
    }

    pick_create = by_activities[
        ("pick item", "create package")
    ]

    assert pick_create.forward_frequency == 1000
    assert pick_create.backward_frequency == 10
    assert pick_create.dependency == pytest.approx(
        (1000 - 10) / (1000 + 10 + 1)
    )
    assert (
        pick_create.relative_support
        == pytest.approx(1.0)
    )

    pick_send = by_activities[
        ("pick item", "send package")
    ]

    assert pick_send.dependency == pytest.approx(
        20 / 21
    )
    assert (
        pick_send.relative_support
        == pytest.approx(0.02)
    )


def test_derive_causal_relations_filters_noise(
    synthetic_ocdfg: dict,
) -> None:
    relations = derive_causal_relations(
        ocdfg=synthetic_ocdfg,
        dependency_threshold=0.90,
        relative_support_threshold=0.05,
        object_types={"items"},
    )

    assert relations == {
        CausalRelation(
            source_activity="place order",
            target_activity="pick item",
            object_type="items",
        ),
        CausalRelation(
            source_activity="pick item",
            target_activity="create package",
            object_type="items",
        ),
    }


@pytest.mark.parametrize(
    (
        "dependency_threshold",
        "support_threshold",
    ),
    [
        (-0.01, 0.05),
        (1.01, 0.05),
        (0.90, -0.01),
        (0.90, 1.01),
    ],
)
def test_invalid_thresholds_are_rejected(
    synthetic_ocdfg: dict,
    dependency_threshold: float,
    support_threshold: float,
) -> None:
    with pytest.raises(ValueError):
        derive_causal_relations(
            ocdfg=synthetic_ocdfg,
            dependency_threshold=(
                dependency_threshold
            ),
            relative_support_threshold=(
                support_threshold
            ),
        )


def test_unknown_object_type_is_rejected(
    synthetic_ocdfg: dict,
) -> None:
    with pytest.raises(
        ValueError,
        match="Object type non presenti",
    ):
        derive_causal_relations(
            ocdfg=synthetic_ocdfg,
            object_types={"packages"},
        )