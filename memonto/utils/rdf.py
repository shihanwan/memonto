import datetime
import graphviz
import os
import uuid
from collections import defaultdict
from rdflib import Graph, Literal, BNode
from rdflib.namespace import RDF, RDFS, OWL
from typing import Union

from memonto.utils.namespaces import TRIPLE_PROP


def is_rdf_schema(p) -> Graph:
    return p.startswith(RDFS) or p.startswith(OWL) or p.startswith(RDF)


def sanitize_label(label: str) -> str:
    return label.replace("-", "_").replace(":", "_").replace(" ", "_")


def remove_namespace(c: str) -> str:
    return c.split("/")[-1].split("#")[-1].split(":")[-1]


def serialize_graph_without_ids(g: Graph, format: str = "turtle") -> Graph:
    graph = Graph()

    for s, p, o in g:
        if isinstance(s, BNode) and (s, TRIPLE_PROP.uuid, None) in g:
            continue

        graph.add((s, p, o))

    return graph.serialize(format=format)


def hydrate_graph_with_ids(g: Graph) -> Graph:
    for s, p, o in g:
        id = str(uuid.uuid4())

        triple_node = BNode()

        g.add((triple_node, RDF.subject, s))
        g.add((triple_node, RDF.predicate, p))
        g.add((triple_node, RDF.object, o))

        g.add((triple_node, TRIPLE_PROP.uuid, Literal(id)))

    return g


def generate_image(g: Graph, path: str = None) -> None:
    if not path:
        current_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        current_directory = os.getcwd()
        local_directory = os.path.join(current_directory, ".local")
        path = os.path.join(local_directory, f"data-graph-{current_time}")

    dot = graphviz.Digraph()

    bnode_labels = defaultdict(lambda: f"BNode{len(bnode_labels) + 1}")

    for s, p, o in g:
        if isinstance(s, BNode) and (s, TRIPLE_PROP.uuid, None) in g:
            continue
        if isinstance(o, BNode) and (o, TRIPLE_PROP.uuid, None) in g:
            continue

        s_label = bnode_labels[s] if isinstance(s, BNode) else sanitize_label(str(s))
        o_label = bnode_labels[o] if isinstance(o, BNode) else sanitize_label(str(o))
        p_label = sanitize_label(str(p))

        dot.node(s_label, s_label)
        dot.node(o_label, o_label)
        dot.edge(s_label, o_label, label=p_label)

    dot.render(path, format="png")

    return f"{path}.png"


def generate_text(g: Graph) -> str:
    text_g = ""

    for s, p, o in g:
        if is_rdf_schema(p):
            continue

        text_g += f"({str(s)}) -> [{str(p)}] -> ({str(o)})"

    return text_g


def _render(
    g: Graph,
    format: str = "turtle",
    path: str = None,
) -> Union[str, dict]:
    """
    Return a text representation of the entire currently stored memory.

    :param format: The format in which to render the graph. Supported formats are:
        - "turtle": Return the graph in Turtle format.
        - "json": Return the graph in JSON-LD format.
        - "text": Return the graph in text format.
        - "image": Return the graph as a png image.
    :param path: The path to save the image if format is "image".

    :return: A text representation of the memory.
        - "turtle" format returns a string in Turtle format.
        - "json" format returns a dictionary in JSON-LD format.
        - "text" format returns a string in text format.
        - "image" format returns a string with the path to the png image.
    """
    if format == "turtle":
        return serialize_graph_without_ids(g=g, format="turtle")
    elif format == "json":
        return serialize_graph_without_ids(g=g, format="json-ld")
    elif format == "triples":
        return serialize_graph_without_ids(g=g, format="nt")
    elif format == "text":
        return generate_text(g)
    elif format == "image":
        return generate_image(g=g, path=path)
    else:
        raise ValueError(f"Unsupported type '{type}'.")
