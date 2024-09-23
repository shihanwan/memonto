import graphviz
from pathlib import Path
from rdflib import Graph

from memonto.utils.rdf import is_rdf_schema, sanitize_label


def generate_image(g: Graph) -> None:
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

    project_root = Path(__file__).resolve().parent.parent
    local_dir = project_root / ".local"
    local_dir.mkdir(parents=True, exist_ok=True)
    save_path = local_dir / "rdf_graph"

    dot.render(str(save_path), format="png")

    return f"{save_path}.png"


def generate_text(g: Graph) -> str:
    text_g = ""

    for s, p, o in g:
        if is_rdf_schema(p):
            continue

        text_g += f"({str(s)}) -> [{str(p)}] -> ({str(o)})"

    return text_g


def render_memory(g: Graph, format: str) -> str:
    if format == "turtle":
        return g.serialize(format="turtle")
    elif format == "json":
        return g.serialize(format="json-ld")
    elif format == "triples":
        return g.serialize(format="nt")
    elif format == "text":
        return generate_text(g)
    elif format == "image":
        return generate_image(g)
    else:
        raise ValueError(f"Unsupported type '{type}'.")
