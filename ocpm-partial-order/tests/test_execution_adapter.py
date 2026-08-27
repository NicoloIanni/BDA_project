from types import SimpleNamespace

import pandas as pd
import pytest

from ocpm_partial_order.extraction.execution_adapter import (
    StructuralContaminationError,
    extract_order_centred_execution,
)


def build_test_ocel():
    events = pd.DataFrame(
        [
            ("e4", "2024-01-01T09:20:00Z", "pick item"),
            ("e1", "2024-01-01T09:00:00Z", "place order"),
            ("e8", "2024-01-01T09:22:00Z", "unrelated event"),
            ("e2", "2024-01-01T09:10:00Z", "confirm order"),
            ("e6", "2024-01-01T09:40:00Z", "send package"),
            ("e3", "2024-01-01T09:15:00Z", "pay order"),
            ("e7", "2024-01-01T09:50:00Z", "package delivered"),
            ("e5", "2024-01-01T09:30:00Z", "create package"),
        ],
        columns=[
            "ocel:eid",
            "ocel:timestamp",
            "ocel:activity",
        ],
    )

    events["ocel:timestamp"] = pd.to_datetime(
        events["ocel:timestamp"],
        utc=True,
    )

    relations = pd.DataFrame(
        [
            ("e1", "o-1", "orders"),
            ("e1", "i-1", "items"),
            ("e1", "product-1", "products"),
            ("e1", "employee-1", "employees"),
            ("e2", "o-1", "orders"),
            ("e2", "employee-1", "employees"),
            ("e3", "o-1", "orders"),
            ("e4", "i-1", "items"),
            ("e4", "product-1", "products"),
            ("e4", "employee-1", "employees"),
            ("e5", "i-1", "items"),
            ("e5", "p-1", "packages"),
            ("e6", "p-1", "packages"),
            ("e6", "employee-1", "employees"),
            ("e7", "p-1", "packages"),
            # Stessi oggetti informativi, ma nessun oggetto
            # strutturale appartenente all'ordine.
            ("e8", "product-1", "products"),
            ("e8", "employee-1", "employees"),
        ],
        columns=[
            "ocel:eid",
            "ocel:oid",
            "ocel:type",
        ],
    )

    return SimpleNamespace(
        events=events,
        relations=relations,
    )


def test_extracts_bounded_order_execution() -> None:
    execution = extract_order_centred_execution(
        build_test_ocel(),
        "o-1",
    )

    assert execution.execution_id == "order-centred:o-1"

    assert [
        event.event_id
        for event in execution.events
    ] == [
        "e1",
        "e2",
        "e3",
        "e4",
        "e5",
        "e6",
        "e7",
    ]

    assert execution.objects() == {
        ("orders", "o-1"),
        ("items", "i-1"),
        ("packages", "p-1"),
        ("products", "product-1"),
        ("employees", "employee-1"),
    }


def test_does_not_expand_through_informational_objects() -> None:
    execution = extract_order_centred_execution(
        build_test_ocel(),
        "o-1",
    )

    assert "e8" not in execution.event_ids()

    place_order = execution.events[0]

    assert place_order.involves_object(
        "products",
        "product-1",
    )
    assert place_order.involves_object(
        "employees",
        "employee-1",
    )


def test_rejects_foreign_structural_objects() -> None:
    ocel = build_test_ocel()

    contamination = pd.DataFrame(
        [
            ("e6", "i-foreign", "items"),
        ],
        columns=[
            "ocel:eid",
            "ocel:oid",
            "ocel:type",
        ],
    )

    ocel.relations = pd.concat(
        [
            ocel.relations,
            contamination,
        ],
        ignore_index=True,
    )

    with pytest.raises(
        StructuralContaminationError,
        match="i-foreign",
    ) as error_info:
        extract_order_centred_execution(
            ocel,
            "o-1",
        )

    error = error_info.value

    assert error.order_id == "o-1"
    assert error.foreign_items == ("i-foreign",)
    assert error.reason_code == "foreign_items"


def test_rejects_unknown_order() -> None:
    with pytest.raises(
        ValueError,
        match="Ordine non trovato",
    ):
        extract_order_centred_execution(
            build_test_ocel(),
            "o-unknown",
        )
