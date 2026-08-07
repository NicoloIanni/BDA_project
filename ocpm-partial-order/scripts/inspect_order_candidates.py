from collections import defaultdict

from ocpm_partial_order.config import MAIN_DATASET_DB
from ocpm_partial_order.io.ocel_loader import load_ocel2_sqlite


LEADING_TYPE = "orders"
STRUCTURAL_TYPES = {"orders", "items", "packages"}

SUCCESS_ACTIVITIES = {
    "place order",
    "confirm order",
    "pay order",
    "pick item",
    "create package",
    "send package",
    "package delivered",
}

EXCEPTION_ACTIVITIES = {
    "item out of stock",
    "reorder item",
    "payment reminder",
    "failed delivery",
}


def main() -> None:
    ocel = load_ocel2_sqlite(MAIN_DATASET_DB)

    relations = ocel.relations[
        ["ocel:eid", "ocel:oid", "ocel:type"]
    ]

    event_activity = (
        ocel.events
        .set_index("ocel:eid")["ocel:activity"]
        .astype(str)
        .to_dict()
    )

    event_to_objects = defaultdict(list)
    object_to_events = defaultdict(set)

    for event_id, object_id, object_type in relations.itertuples(
        index=False,
        name=None,
    ):
        event_id = str(event_id)
        object_id = str(object_id)
        object_type = str(object_type)

        reference = (object_type, object_id)
        event_to_objects[event_id].append(reference)
        object_to_events[reference].add(event_id)

    def objects_of_type(event_ids: set[str], object_type: str) -> set[str]:
        return {
            object_id
            for event_id in event_ids
            for current_type, object_id in event_to_objects[event_id]
            if current_type == object_type
        }

    # Ricostruisce quali ordini sono collegati agli item
    # tramite almeno un evento condiviso.
    item_to_orders = defaultdict(set)

    for references in event_to_objects.values():
        orders = {
            object_id
            for object_type, object_id in references
            if object_type == "orders"
        }
        items = {
            object_id
            for object_type, object_id in references
            if object_type == "items"
        }

        for item_id in items:
            item_to_orders[item_id].update(orders)

    order_ids = sorted(
        object_id
        for object_type, object_id in object_to_events
        if object_type == LEADING_TYPE
    )

    candidates = []

    for order_id in order_ids:
        # Livello 1: eventi direttamente collegati all'ordine.
        order_events = set(
            object_to_events[(LEADING_TYPE, order_id)]
        )

        # Livello 2: item osservati negli eventi dell'ordine.
        direct_items = objects_of_type(order_events, "items")
        item_events = {
            event_id
            for item_id in direct_items
            for event_id in object_to_events[("items", item_id)]
        }

        # Livello 3: package osservati nel ciclo di vita degli item.
        packages = objects_of_type(item_events, "packages")
        package_events = {
            event_id
            for package_id in packages
            for event_id in object_to_events[("packages", package_id)]
        }

        selected_events = order_events | item_events | package_events
        selected_items = objects_of_type(selected_events, "items")

        foreign_items = selected_items - direct_items

        reached_orders = {
            reached_order
            for item_id in selected_items
            for reached_order in item_to_orders[item_id]
        }
        foreign_orders = reached_orders - {order_id}

        activities = {
            event_activity[event_id]
            for event_id in selected_events
        }

        candidates.append(
            {
                "order_id": order_id,
                "events": len(selected_events),
                "items": len(direct_items),
                "packages": len(packages),
                "foreign_items": len(foreign_items),
                "foreign_orders": len(foreign_orders),
                "complete": SUCCESS_ACTIVITIES <= activities,
                "simple": not bool(activities & EXCEPTION_ACTIVITIES),
                "activities": activities,
            }
        )

    eligible = [
        candidate
        for candidate in candidates
        if candidate["complete"]
        and candidate["foreign_items"] == 0
        and candidate["foreign_orders"] == 0
    ]

    simple_eligible = [
        candidate
        for candidate in eligible
        if candidate["simple"]
    ]

    simple_eligible.sort(
        key=lambda candidate: (
            candidate["events"],
            candidate["items"],
            candidate["packages"],
            candidate["order_id"],
        )
    )

    print("Diagnostica ordini Order Management")
    print("-----------------------------------")
    print("Ordini analizzati:", len(candidates))
    print("Candidati completi e non contaminati:", len(eligible))
    print("Candidati semplici senza eccezioni:", len(simple_eligible))

    print("\nPrimi 15 candidati semplici:")
    for candidate in simple_eligible[:15]:
        activities = ", ".join(sorted(candidate["activities"]))

        print(
            f"- {candidate['order_id']}: "
            f"events={candidate['events']}, "
            f"items={candidate['items']}, "
            f"packages={candidate['packages']}"
        )
        print(f"  activities=[{activities}]")

    if not simple_eligible:
        print(
            "\nNessun candidato soddisfa tutti i criteri. "
            "Non scegliere un ordine arbitrariamente: "
            "occorre riesaminare la regola di espansione."
        )


if __name__ == "__main__":
    main()
