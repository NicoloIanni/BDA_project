from dataclasses import dataclass, field

from .event import ExecutionEvent


@dataclass
class ProcessExecution:
    """
    Insieme degli eventi appartenenti a una singola
    esecuzione object-centric.
    """

    execution_id: str
    events: list[ExecutionEvent] = field(default_factory=list)

    def event_ids(self) -> set[str]:
        return {
            event.event_id
            for event in self.events
        }

    def objects(self) -> set[tuple[str, str]]:
        result: set[tuple[str, str]] = set()

        for event in self.events:
            for obj in event.objects:
                result.add(
                    (
                        obj.object_type,
                        obj.object_id,
                    )
                )

        return result

    def events_for_object(
        self,
        object_type: str,
        object_id: str,
    ) -> list[ExecutionEvent]:
        selected = [
            event
            for event in self.events
            if event.involves_object(
                object_type=object_type,
                object_id=object_id,
            )
        ]

        return sorted(
            selected,
            key=lambda event: (
                event.timestamp,
                event.event_id,
            ),
        )