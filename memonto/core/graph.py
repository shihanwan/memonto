import graphviz
from pathlib import Path
from rdflib import Graph, URIRef
from rdflib.namespace import RDF, RDFS


def generate_image(g: Graph) -> None:
    dot = graphviz.Digraph(format="png")

    for subj, pred, obj in g:
        if pred in [RDF.type, RDFS.domain, RDFS.range, RDFS.subClassOf]:
            continue

        dot.node(
            str(subj), str(subj).split("/")[-1]
        )  # Use the last part of the URI as label
        dot.node(
            str(obj), str(obj).split("/")[-1] if isinstance(obj, URIRef) else str(obj)
        )
        dot.edge(str(subj), str(obj), label=str(pred).split("/")[-1])

    project_root = Path(__file__).resolve().parent.parent
    local_dir = project_root / ".local"
    local_dir.mkdir(parents=True, exist_ok=True)
    save_path = local_dir / "rdf_graph"

    dot.render(str(save_path), view=False)


def graph_memory(g: Graph, format: str) -> str:
    if format == "turtle":
        return g.serialize(format="turtle")
    elif format == "json":
        return g.serialize(format="json-ld")
    elif format == "image":
        generate_image(g)
    else:
        raise ValueError(f"Unsupported type '{type}'. Choose from 'json', or 'turtle'.")
