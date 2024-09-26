from rdflib import Graph, Namespace

from memonto.stores.triple.base_store import TripleStoreModel
from memonto.utils.decorators import require_config


@require_config("triple_store")
def load_memory(
    namespaces: dict[str, Namespace],
    triple_store: TripleStoreModel,
    id: str,
) -> Graph:
    return triple_store.load(namespaces=namespaces, id=id)
