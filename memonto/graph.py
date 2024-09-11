from rdflib import Graph

def graph_memory(g: Graph, format: str) -> str:
    if format == "turtle":
        return g.serialize(format="turtle")
    elif type == "json":
        return g.serialize(format="json-ld")
    else:
        raise ValueError(f"Unsupported type '{type}'. Choose from 'json', or 'turtle'.")
