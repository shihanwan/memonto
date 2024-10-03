import datetime
import graphviz
import os
from rdflib import Graph
from rdflib.namespace import RDF, RDFS, OWL
from typing import Union


def is_rdf_schema(p) -> Graph:
    return p.startswith(RDFS) or p.startswith(OWL) or p.startswith(RDF)


def sanitize_label(label: str) -> str:
    return label.replace("-", "_").replace(":", "_").replace(" ", "_")


def remove_namespace(c: str) -> str:
    return c.split("/")[-1].split("#")[-1].split(":")[-1]


def generate_image(g: Graph, path: str = None) -> None:
    if not path:
        current_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        current_directory = os.getcwd()
        local_directory = os.path.join(current_directory, ".local")
        path = os.path.join(local_directory, f"data-graph-{current_time}")

    dot = graphviz.Digraph()

    for s, p, o in g:
        if is_rdf_schema(p):
            continue

        s_label = sanitize_label(str(s))
        p_label = sanitize_label(str(p))
        o_label = sanitize_label(str(o))

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
        return g.serialize(format="turtle")
    elif format == "json":
        return g.serialize(format="json-ld")
    elif format == "triples":
        return g.serialize(format="nt")
    elif format == "text":
        return generate_text(g)
    elif format == "image":
        return generate_image(g=g, path=path)
    else:
        raise ValueError(f"Unsupported type '{type}'.")
