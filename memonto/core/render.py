import graphviz
from rdflib import Graph

from memonto.utils.rdf import is_rdf_schema, sanitize_label


def generate_image(g: Graph, path: str) -> None:
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


def _render(g: Graph, format: str, path: str) -> str:
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
