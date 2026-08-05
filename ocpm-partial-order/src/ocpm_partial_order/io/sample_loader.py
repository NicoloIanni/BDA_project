import json
from datetime import datetime
from pathlib import Path

from ocpm_partial_order.domain.causal_relation import (
    CausalRelation,
)
from ocpm_partial_order.domain.event import (
    ExecutionEvent,
    ObjectReference,
)
from ocpm_partial_order.domain.process_execution import (
    ProcessExecution,
)


def load_process_execution(
    path: str | Path,
) -> ProcessExecution:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Execution non trovata: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        raw = json.load(file)

    events: list[ExecutionEvent] = []

    for raw_event in raw["events"]:
        objects = {
            ObjectReference(
                object_id=raw_object["object_id"],
                object_type=raw_object["object_type"],
            )
            for raw_object in raw_event["objects"]
        }

        events.append(
            ExecutionEvent(
                event_id=raw_event["event_id"],
                activity=raw_event["activity"],
                timestamp=datetime.fromisoformat(
                    raw_event["timestamp"]
                ),
                objects=objects,
            )
        )

    return ProcessExecution(
        execution_id=raw["execution_id"],
        events=events,
    )


def load_causal_relations(
    path: str | Path,
) -> set[CausalRelation]:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Causal relations non trovate: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        raw = json.load(file)

    return {
        CausalRelation(
            source_activity=item["source_activity"],
            target_activity=item["target_activity"],
            object_type=item["object_type"],
        )
        for item in raw
    }