import pm4py
import pytest

from ocpm_partial_order.config import (
    MAIN_DATASET_DB,
)
from ocpm_partial_order.conformance import (
    check_execution_projections,
    check_object_projection,
    check_object_type_conformance,
    replay_flattened_object_trace,
)
from ocpm_partial_order.discovery import (
    discover_ocpn,
)
from ocpm_partial_order.io.ocel_loader import (
    load_ocel2_sqlite,
)


REFERENCE_OBJECTS = {
    "orders": {"o-990424"},
    "items": {"i-881734"},
    "packages": {"p-660247"},
}


@pytest.fixture(scope="module")
def real_ocel():
    return load_ocel2_sqlite(
        MAIN_DATASET_DB
    )


@pytest.fixture(scope="module")
def real_ocpn(real_ocel):
    return discover_ocpn(
        real_ocel
    )


@pytest.fixture(scope="module")
def package_trace(real_ocel):
    flattened_log = (
        pm4py.ocel_flattening(
            real_ocel,
            "packages",
        )
    )

    return flattened_log[
        flattened_log[
            "case:concept:name"
        ].astype(str)
        == "p-660247"
    ].copy()


def test_reference_execution_projections_fit(
    real_ocel,
    real_ocpn,
) -> None:
    report = check_execution_projections(
        ocel=real_ocel,
        ocpn=real_ocpn,
        object_ids_by_type=(
            REFERENCE_OBJECTS
        ),
    )

    assert len(
        report.trace_results
    ) == 3

    assert {
        (
            result.object_type,
            result.object_id,
        )
        for result in report.trace_results
    } == {
        (
            "orders",
            "o-990424",
        ),
        (
            "items",
            "i-881734",
        ),
        (
            "packages",
            "p-660247",
        ),
    }

    assert all(
        result.trace_is_fit
        for result in report.trace_results
    )

    assert all(
        result.trace_fitness == 1.0
        for result in report.trace_results
    )

    assert all(
        result.missing_tokens == 0
        for result in report.trace_results
    )

    assert all(
        result.remaining_tokens == 0
        for result in report.trace_results
    )


def test_execution_report_aggregates_fitness(
    real_ocel,
    real_ocpn,
) -> None:
    report = check_execution_projections(
        ocel=real_ocel,
        ocpn=real_ocpn,
        object_ids_by_type=(
            REFERENCE_OBJECTS
        ),
    )

    assert report.all_projections_fit
    assert (
        report.minimum_trace_fitness
        == pytest.approx(1.0)
    )
    assert (
        report.average_trace_fitness
        == pytest.approx(1.0)
    )


def test_all_package_projections_fit(
    real_ocel,
    real_ocpn,
) -> None:
    summary = (
        check_object_type_conformance(
            ocel=real_ocel,
            ocpn=real_ocpn,
            object_type="packages",
        )
    )

    assert summary.object_type == "packages"
    assert summary.trace_count == 1128
    assert (
        summary.fitting_trace_count
        == 1128
    )
    assert (
        summary.non_fitting_trace_count
        == 0
    )
    assert (
        summary.fitting_percentage
        == pytest.approx(100.0)
    )
    assert (
        summary.average_trace_fitness
        == pytest.approx(1.0)
    )
    assert summary.total_missing_tokens == 0
    assert (
        summary.total_remaining_tokens
        == 0
    )


def test_incomplete_package_trace_is_not_fit(
    real_ocpn,
    package_trace,
) -> None:
    incomplete_trace = (
        package_trace.iloc[:-1].copy()
    )

    result = (
        replay_flattened_object_trace(
            flattened_trace=(
                incomplete_trace
            ),
            component_petri_net=(
                real_ocpn[
                    "petri_nets"
                ]["packages"]
            ),
            object_type="packages",
            object_id="p-660247",
        )
    )

    assert not result.trace_is_fit
    assert (
        result.trace_fitness
        == pytest.approx(
            2 / 3,
        )
    )
    assert result.missing_tokens == 1
    assert result.remaining_tokens == 1
    assert result.activities == (
        "create package",
        "send package",
    )


def test_unknown_object_type_is_rejected(
    real_ocel,
    real_ocpn,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Object type non presente"
        ),
    ):
        check_object_projection(
            ocel=real_ocel,
            ocpn=real_ocpn,
            object_type="unknown",
            object_id="x-1",
        )


def test_unknown_object_id_is_rejected(
    real_ocel,
    real_ocpn,
) -> None:
    with pytest.raises(
        ValueError,
        match="Oggetto non trovato",
    ):
        check_object_projection(
            ocel=real_ocel,
            ocpn=real_ocpn,
            object_type="packages",
            object_id=(
                "package-not-existing"
            ),
        )
