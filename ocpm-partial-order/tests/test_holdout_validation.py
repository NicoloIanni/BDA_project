import pandas as pd
import pytest

from ocpm_partial_order.config import (
    MAIN_DATASET_DB,
)
from ocpm_partial_order.conformance import (
    evaluate_object_type_holdout,
    split_flattened_object_type_log,
)
from ocpm_partial_order.io.ocel_loader import (
    load_ocel2_sqlite,
)


CASE_ID = "case:concept:name"
EVENT_ID = "ocel:eid"
ACTIVITY = "concept:name"
TIMESTAMP = "time:timestamp"


def _row(
    event_id: str,
    case_id: str,
    activity: str,
    timestamp: str,
) -> dict:
    return {
        EVENT_ID: event_id,
        CASE_ID: case_id,
        ACTIVITY: activity,
        TIMESTAMP: pd.Timestamp(
            timestamp,
            tz="UTC",
        ),
    }


@pytest.fixture
def shared_event_log() -> pd.DataFrame:
    return pd.DataFrame(
        [
            _row(
                "shared-ab",
                "A",
                "start",
                "2024-01-01",
            ),
            _row(
                "shared-ab",
                "B",
                "start",
                "2024-01-01",
            ),
            _row(
                "b-end",
                "B",
                "finish",
                "2024-01-02",
            ),
            _row(
                "c-start",
                "C",
                "start",
                "2024-02-01",
            ),
            _row(
                "c-end",
                "C",
                "finish",
                "2024-02-02",
            ),
            _row(
                "d-start",
                "D",
                "start",
                "2024-03-01",
            ),
            _row(
                "d-end",
                "D",
                "finish",
                "2024-03-02",
            ),
        ]
    )


def test_split_keeps_shared_event_cases_together(
    shared_event_log: pd.DataFrame,
) -> None:
    split = split_flattened_object_type_log(
        flattened_log=shared_event_log,
        object_type="items",
        train_ratio=0.50,
    )

    train_cases = set(
        split.train_log[CASE_ID]
    )
    test_cases = set(
        split.test_log[CASE_ID]
    )

    assert train_cases == {"A", "B"}
    assert test_cases == {"C", "D"}
    assert not train_cases & test_cases

    train_events = set(
        split.train_log[EVENT_ID]
    )
    test_events = set(
        split.test_log[EVENT_ID]
    )

    assert not train_events & test_events
    assert split.component_count == 3
    assert split.train_component_count == 1
    assert split.test_component_count == 2
    assert split.train_case_count == 2
    assert split.test_case_count == 2
    assert split.effective_train_ratio == 0.50


@pytest.mark.parametrize(
    "train_ratio",
    [
        -0.01,
        0.0,
        1.0,
        1.01,
    ],
)
def test_invalid_train_ratio_is_rejected(
    shared_event_log: pd.DataFrame,
    train_ratio: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="train_ratio",
    ):
        split_flattened_object_type_log(
            flattened_log=shared_event_log,
            object_type="items",
            train_ratio=train_ratio,
        )


def test_missing_columns_are_rejected() -> None:
    incomplete_log = pd.DataFrame(
        {
            CASE_ID: ["A", "B"],
        }
    )

    with pytest.raises(
        ValueError,
        match="colonne richieste",
    ):
        split_flattened_object_type_log(
            flattened_log=incomplete_log,
            object_type="items",
        )


def test_single_component_is_rejected() -> None:
    connected_log = pd.DataFrame(
        [
            _row(
                "shared",
                "A",
                "start",
                "2024-01-01",
            ),
            _row(
                "shared",
                "B",
                "start",
                "2024-01-01",
            ),
        ]
    )

    with pytest.raises(
        ValueError,
        match="stessa componente",
    ):
        split_flattened_object_type_log(
            flattened_log=connected_log,
            object_type="items",
        )


def test_real_package_holdout_evaluation() -> None:
    ocel = load_ocel2_sqlite(
        MAIN_DATASET_DB
    )

    evaluation = (
        evaluate_object_type_holdout(
            ocel=ocel,
            object_type="packages",
            train_ratio=0.80,
            noise_threshold=0.0,
        )
    )

    assert (
        evaluation.split.component_count
        == 1128
    )
    assert (
        evaluation.split.train_case_count
        == 902
    )
    assert (
        evaluation.split.test_case_count
        == 226
    )
    assert (
        evaluation.test_conformance
        .trace_count
        == 226
    )
    assert (
        evaluation.test_conformance
        .fitting_trace_count
        == 226
    )
    assert (
        evaluation.test_conformance
        .average_trace_fitness
        == pytest.approx(1.0)
    )
    assert (
        evaluation.test_conformance
        .total_missing_tokens
        == 0
    )
    assert (
        evaluation.test_conformance
        .total_remaining_tokens
        == 0
    )
    assert evaluation.test_precision > 0.99
    assert evaluation.test_generalization > 0.85
    assert evaluation.model_simplicity > 0.80
