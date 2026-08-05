from itertools import combinations

import networkx as nx


def find_incomparable_event_pairs(
    graph: nx.DiGraph,
) -> set[tuple[str, str]]:
    """
    Trova coppie di eventi per cui non esiste
    un percorso causale in nessuna direzione.

    Nel prototipo queste coppie sono candidate
    al parallelismo.
    """
    incomparable_pairs: set[
        tuple[str, str]
    ] = set()

    for first, second in combinations(
        graph.nodes,
        2,
    ):
        first_before_second = nx.has_path(
            graph,
            first,
            second,
        )

        second_before_first = nx.has_path(
            graph,
            second,
            first,
        )

        if (
            not first_before_second
            and not second_before_first
        ):
            incomparable_pairs.add(
                (first, second)
            )

    return incomparable_pairs