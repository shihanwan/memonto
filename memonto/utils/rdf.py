import datetime
import graphviz
import os
import re
import uuid
from collections import defaultdict
from rdflib import Graph, Literal, BNode, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, OWL
from typing import Union

from memonto.utils.namespaces import TRIPLE_PROP


def is_rdf_schema(p: str) -> Graph:
    return p.startswith(RDFS) or p.startswith(OWL) or p.startswith(RDF)


def is_bnode_uuid(s: str, g: Graph) -> bool:
    return isinstance(s, BNode) and (s, TRIPLE_PROP.uuid, None) in g


def to_human_readable(c: str, ns: dict[str, Namespace]) -> str:
    for n in ns.values():
        if c.startswith(n):
            c.replace(n, "")

    c = c.split("/")[-1].split("#")[-1].split(":")[-1]
    c = c.replace("_", " ")
    c = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", c).lower()

    return c


def format_node(node: URIRef | Literal | BNode) -> str:
    if isinstance(node, URIRef):
        return f"<{str(node)}>"
    elif isinstance(node, Literal):
        return f'"{str(node)}"'
    elif isinstance(node, BNode):
        return f"_:{str(node)}"
    else:
        return f'"{str(node)}"'


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


def find_updated_triples(original: dict, updated: dict) -> dict[str, dict]:
    return {
        id: updated[id]
        for id in original
        if id in updated and original[id]["triple"] != updated[id]["triple"]
    }


def find_updated_triples_ephemeral(o: list[dict], n: list[dict]) -> list[dict]:
    def is_updated(nt: dict, o: list[dict]) -> bool:
        ns, np, no = str(nt["s"]), str(nt["p"]), str(nt["o"])

        for ot in o:
            os, op, oo = str(ot["s"]), str(ot["p"]), str(ot["o"])

            if ns == os and np == op and no == oo:
                return False

        return True

    return [nt for nt in n if is_updated(nt, o)]


def generate_image(g: Graph, ns: dict[str, Namespace], path: str = None) -> None:
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

        s_label = (
            bnode_labels[s] if isinstance(s, BNode) else to_human_readable(str(s), ns)
        )
        o_label = (
            bnode_labels[o] if isinstance(o, BNode) else to_human_readable(str(o), ns)
        )
        p_label = to_human_readable(str(p), ns)

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
    ns: dict[str, Namespace] = None,
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
        return generate_image(g=g, ns=ns, path=path)
    else:
        raise ValueError(f"Unsupported type '{type}'.")
