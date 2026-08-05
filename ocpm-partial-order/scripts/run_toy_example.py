from pathlib import Path

import networkx as nx
from graphviz import Digraph


def save_instance_graph(
    graph: nx.DiGraph,
    output_path: str | Path,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dot = Digraph(
        name="object_centric_instance_graph",
        format="png",
    )

    dot.attr(rankdir="LR")

    for node, attributes in graph.nodes(data=True):
        activity = attributes.get(
            "activity",
            "",
        )

        label = f"{node}\\n{activity}"

        dot.node(
            str(node),
            label=label,
            shape="box",
        )

    for source, target, attributes in graph.edges(
        data=True
    ):
        object_types = sorted(
            attributes.get(
                "object_types",
                set(),
            )
        )

        edge_label = ", ".join(object_types)

        dot.edge(
            str(source),
            str(target),
            label=edge_label,
        )

    rendered_path = dot.render(
        filename=output_path.stem,
        directory=str(output_path.parent),
        cleanup=True,
    )

    return Path(rendered_path)