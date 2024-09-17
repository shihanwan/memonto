import graphviz
from pathlib import Path
from rdflib import Graph
from rdflib.namespace import RDF, RDFS


def sanitize_label(label: str) -> str:
    return label.replace("-", "_").replace(":", "_").replace(" ", "_")


def generate_image(g: Graph) -> None:
    dot = graphviz.Digraph()

    for s, p, o in g:
        if p in [RDF.type, RDFS.domain, RDFS.range, RDFS.subClassOf]:
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
        if p in [RDF.type, RDFS.domain, RDFS.range, RDFS.subClassOf]:
            continue

        s_label = sanitize_label(str(s))
        p_label = sanitize_label(str(p))
        o_label = sanitize_label(str(o))

        text_g += f"({s_label}) -> [{p_label}] -> ({o_label})\n"

    return text_g


def render_memory(g: Graph, format: str) -> str:
    if format == "turtle":
        return g.serialize(format="turtle")
    elif format == "json":
        return g.serialize(format="json-ld")
    elif format == "text":
        return generate_text(g)
    elif format == "image":
        return generate_image(g)
    else:
        raise ValueError(f"Unsupported type '{type}'.")
