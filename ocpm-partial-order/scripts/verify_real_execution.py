from collections import Counter

from ocpm_partial_order.config import MAIN_DATASET_DB
from ocpm_partial_order.extraction import (
    extract_order_centred_execution,
)
from ocpm_partial_order.io.ocel_loader import (
    load_ocel2_sqlite,
)


ORDER_ID = "o-990424"

EXPECTED_ACTIVITIES = {
    "place order",
    "confirm order",
    "pay order",
    "pick item",
    "create package",
    "send package",
    "package delivered",
}


def main() -> None:
    print("Caricamento dataset reale:")
    print(MAIN_DATASET_DB)

    ocel = load_ocel2_sqlite(MAIN_DATASET_DB)

    execution = extract_order_centred_execution(
        ocel=ocel,
        order_id=ORDER_ID,
    )

    event_ids = [
        event.event_id
        for event in execution.events
    ]

    activities = {
        event.activity
        for event in execution.events
    }

    objects = execution.objects()

    objects_by_type = Counter(
        object_type
        for object_type, _ in objects
    )

    structural_objects = {
        object_type: sorted(
            object_id
            for current_type, object_id in objects
            if current_type == object_type
        )
        for object_type in (
            "orders",
            "items",
            "packages",
        )
    }

    print("\nProcess execution estratta")
    print("--------------------------")
    print("Execution ID:", execution.execution_id)
    print("Numero eventi:", len(execution.events))
    print("Numero oggetti:", len(objects))
    print("Oggetti per tipo:", dict(sorted(objects_by_type.items())))

    print("\nOggetti strutturali:")
    for object_type, object_ids in structural_objects.items():
        print(f"- {object_type}: {object_ids}")

    print("\nEventi in ordine deterministico:")
    for event in execution.events:
        references = sorted(
            (
                obj.object_type,
                obj.object_id,
            )
            for obj in event.objects
        )

        formatted_references = ", ".join(
            f"{object_type}:{object_id}"
            for object_type, object_id in references
        )

        print(
            f"- {event.timestamp.isoformat()} | "
            f"{event.event_id} | "
            f"{event.activity}"
        )
        print(f"  objects=[{formatted_references}]")

    # Invarianti del candidato deterministico individuato
    # dal diagnostico inspect_order_candidates.py.
    assert execution.execution_id == (
        f"order-centred:{ORDER_ID}"
    ), "Execution ID inatteso"

    assert len(execution.events) == 7, (
        "Il diagnostico prevedeva esattamente 7 eventi, "
        f"ma l'adapter ne ha estratti {len(execution.events)}"
    )

    assert len(event_ids) == len(set(event_ids)), (
        "La process execution contiene eventi duplicati"
    )

    assert activities == EXPECTED_ACTIVITIES, (
        "Le attività estratte non corrispondono al ciclo "
        f"completo atteso. Trovate: {sorted(activities)}"
    )

    assert structural_objects["orders"] == [ORDER_ID], (
        "L'esecuzione contiene ordini estranei"
    )

    assert len(structural_objects["items"]) == 1, (
        "Il diagnostico prevedeva esattamente un item"
    )

    assert len(structural_objects["packages"]) == 1, (
        "Il diagnostico prevedeva esattamente un package"
    )

    expected_order = sorted(
        execution.events,
        key=lambda event: (
            event.timestamp,
            event.event_id,
        ),
    )

    assert execution.events == expected_order, (
        "Gli eventi non sono ordinati deterministicamente "
        "per timestamp ed event_id"
    )

    assert all(
        event.objects
        for event in execution.events
    ), "Almeno un evento è privo di oggetti associati"

    print("\nVERIFICA REALE SUPERATA")
    print(
        "L'adapter ha estratto correttamente il candidato "
        f"{ORDER_ID} dal dataset Order Management."
    )
    print(
        "Questa prova non dimostra fitness o conformità "
        "rispetto all'OCPN."
    )


if __name__ == "__main__":
    main()
