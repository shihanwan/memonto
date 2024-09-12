from memonto.stores.base_store import StoreModel
from memonto.stores.jena import ApacheJena


def store_factory(store_provider: str) -> StoreModel:
    if store_provider == "apache_jena":
        return ApacheJena()
    else:
        raise ValueError(f"Store {store_provider} not found")
