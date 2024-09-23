from rdflib import Graph
from rdflib.namespace import RDF, RDFS, OWL


def is_rdf_schema(p) -> Graph:
    return p.startswith(RDFS) or p.startswith(OWL) or p.startswith(RDF)
    
def sanitize_label(label: str) -> str:
    return label.replace("-", "_").replace(":", "_").replace(" ", "_")