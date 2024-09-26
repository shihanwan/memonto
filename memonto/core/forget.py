from memonto.stores.triple.base_store import TripleStoreModel
from memonto.stores.vector.base_store import VectorStoreModel


def forget_memory(
    id: str,
    triple_store: TripleStoreModel,
    vector_store: VectorStoreModel,
) -> None:
    if vector_store:
        vector_store.delete(id)
    
    if triple_store:
        triple_store.delete(id)