from memonto.stores.triple.base_store import TripleStoreModel
from memonto.stores.vector.base_store import VectorStoreModel
from memonto.utils.logger import logger


def _forget(
    id: str,
    triple_store: TripleStoreModel,
    vector_store: VectorStoreModel,
) -> None:
    try:
        if vector_store:
            vector_store.delete(id)

        if triple_store:
            triple_store.delete(id)
    except ValueError as e:
        logger.warning(e)
    except Exception as e:
        logger.error(e)