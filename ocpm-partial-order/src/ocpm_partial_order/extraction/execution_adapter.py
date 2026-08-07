from collections import defaultdict
from datetime import datetime

from ocpm_partial_order.domain.event import (
    ExecutionEvent,
    ObjectReference,
)
from ocpm_partial_order.domain.process_execution import (
    ProcessExecution,
)


class StructuralContaminationError(ValueError):
    """
    Indica che l'espansione di un ordine ha raggiunto
    item oppure ordini estranei.
    """


def _require_columns(
    table,
    table_name: str,
    required_columns: set[str],
) -> None:
    missing_columns = required_columns - set(table.columns)

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))

        raise ValueError(
            f"La tabella {table_name} non contiene "
            f"le colonne richieste: {missing}"
        )


def _as_datetime(value) -> datetime:
    """
    Converte anche pandas.Timestamp nel datetime
    usato dal modello interno.
    """
    if hasattr(value, "to_pydatetime"):
        value = value.to_pydatetime()

    if not isinstance(value, datetime):
        raise TypeError(
            "Il timestamp dell'evento non è un datetime valido: "
            f"{value!r}"
        )

    return value


def extract_order_centred_execution(
    ocel,
    order_id: str,
) -> ProcessExecution:
    """
    Estrae una process execution limitata e centrata su un ordine.

    La chiusura strutturale segue esclusivamente:

        order -> items -> packages

    Gli altri tipi di oggetto associati agli eventi, per esempio
    products ed employees, vengono conservati nell'ExecutionEvent,
    ma non vengono attraversati per espandere l'esecuzione.

    L'estrazione viene rifiutata quando la chiusura introduce item
    oppure ordini estranei rispetto all'ordine richiesto.
    """
    _require_columns(
        ocel.events,
        "events",
        {
            "ocel:eid",
            "ocel:timestamp",
            "ocel:activity",
        },
    )
    _require_columns(
        ocel.relations,
        "relations",
        {
            "ocel:eid",
            "ocel:oid",
            "ocel:type",
        },
    )

    event_to_objects: dict[
        str,
        set[tuple[str, str]],
    ] = defaultdict(set)

    object_to_events: dict[
        tuple[str, str],
        set[str],
    ] = defaultdict(set)

    relation_columns = ocel.relations[
        ["ocel:eid", "ocel:oid", "ocel:type"]
    ]

    for event_id, object_id, object_type in (
        relation_columns.itertuples(
            index=False,
            name=None,
        )
    ):
        event_id = str(event_id)
        object_id = str(object_id)
        object_type = str(object_type)

        object_reference = (
            object_type,
            object_id,
        )

        event_to_objects[event_id].add(
            object_reference
        )
        object_to_events[object_reference].add(
            event_id
        )

    leading_object = ("orders", str(order_id))

    if leading_object not in object_to_events:
        raise ValueError(
            f"Ordine non trovato nelle relazioni OCEL: {order_id}"
        )

    def objects_of_type(
        event_ids: set[str],
        object_type: str,
    ) -> set[str]:
        return {
            object_id
            for event_id in event_ids
            for current_type, object_id
            in event_to_objects[event_id]
            if current_type == object_type
        }

    order_events = set(
        object_to_events[leading_object]
    )

    direct_items = objects_of_type(
        order_events,
        "items",
    )

    item_events = {
        event_id
        for item_id in direct_items
        for event_id in object_to_events[
            ("items", item_id)
        ]
    }

    packages = objects_of_type(
        item_events,
        "packages",
    )

    package_events = {
        event_id
        for package_id in packages
        for event_id in object_to_events[
            ("packages", package_id)
        ]
    }

    selected_event_ids = (
        order_events
        | item_events
        | package_events
    )

    selected_items = objects_of_type(
        selected_event_ids,
        "items",
    )
    selected_orders = objects_of_type(
        selected_event_ids,
        "orders",
    )

    foreign_items = selected_items - direct_items
    foreign_orders = selected_orders - {str(order_id)}

    # Ricostruisce anche gli ordini associati agli item
    # tramite altri eventi del log.
    item_to_orders: dict[str, set[str]] = (
        defaultdict(set)
    )

    for references in event_to_objects.values():
        referenced_items = {
            object_id
            for object_type, object_id in references
            if object_type == "items"
        }
        referenced_orders = {
            object_id
            for object_type, object_id in references
            if object_type == "orders"
        }

        for item_id in referenced_items:
            item_to_orders[item_id].update(
                referenced_orders
            )

    orders_reached_via_items = {
        reached_order
        for item_id in selected_items
        for reached_order in item_to_orders[item_id]
    }

    foreign_orders.update(
        orders_reached_via_items - {str(order_id)}
    )

    if foreign_items or foreign_orders:
        details = []

        if foreign_items:
            details.append(
                "item estranei="
                + ", ".join(sorted(foreign_items))
            )

        if foreign_orders:
            details.append(
                "ordini estranei="
                + ", ".join(sorted(foreign_orders))
            )

        raise StructuralContaminationError(
            f"L'estrazione dell'ordine {order_id} "
            "è strutturalmente contaminata: "
            + "; ".join(details)
        )

    event_metadata: dict[
        str,
        tuple[str, datetime],
    ] = {}

    event_columns = ocel.events[
        [
            "ocel:eid",
            "ocel:timestamp",
            "ocel:activity",
        ]
    ]

    for event_id, timestamp, activity in (
        event_columns.itertuples(
            index=False,
            name=None,
        )
    ):
        event_id = str(event_id)

        if event_id in event_metadata:
            raise ValueError(
                "Identificativo evento duplicato nella "
                f"tabella events: {event_id}"
            )

        event_metadata[event_id] = (
            str(activity),
            _as_datetime(timestamp),
        )

    missing_events = (
        selected_event_ids - set(event_metadata)
    )

    if missing_events:
        missing = ", ".join(sorted(missing_events))

        raise ValueError(
            "Eventi presenti nelle relazioni ma assenti "
            f"dalla tabella events: {missing}"
        )

    execution_events = []

    for event_id in selected_event_ids:
        activity, timestamp = event_metadata[event_id]

        object_references = {
            ObjectReference(
                object_id=object_id,
                object_type=object_type,
            )
            for object_type, object_id
            in event_to_objects[event_id]
        }

        execution_events.append(
            ExecutionEvent(
                event_id=event_id,
                activity=activity,
                timestamp=timestamp,
                objects=object_references,
            )
        )

    execution_events.sort(
        key=lambda event: (
            event.timestamp,
            event.event_id,
        )
    )

    return ProcessExecution(
        execution_id=f"order-centred:{order_id}",
        events=execution_events,
    )
