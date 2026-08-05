from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class ObjectReference:
    """
    Riferimento a un oggetto coinvolto in un evento.

    Attributes
    ----------
    object_id:
        Identificativo univoco dell'oggetto.

    object_type:
        Tipo dell'oggetto, ad esempio orders, items o packages.
    """

    object_id: str
    object_type: str


@dataclass
class ExecutionEvent:
    """
    Evento appartenente a una process execution object-centric.

    Un evento può essere collegato a più oggetti e anche a
    oggetti appartenenti a tipi differenti.
    """

    event_id: str
    activity: str
    timestamp: datetime
    objects: set[ObjectReference] = field(default_factory=set)

    def involves_object(
        self,
        object_type: str,
        object_id: str,
    ) -> bool:
        """
        Verifica se l'evento coinvolge uno specifico oggetto.
        """
        return any(
            obj.object_type == object_type
            and obj.object_id == object_id
            for obj in self.objects
        )