from dataclasses import dataclass


@dataclass(frozen=True)
class CausalRelation:
    """
    Rappresenta una relazione causale tra due attività,
    valida rispetto a uno specifico tipo di oggetto.

    Esempio:
        place order -> confirm order
        rispetto al tipo di oggetto "orders".
    """

    source_activity: str
    target_activity: str
    object_type: str