from typing import Optional, Tuple

from memonto.llms.anthropic import Anthropic
from memonto.llms.openai import OpenAI
from memonto.llms.base_llm import LLMModel
from memonto.stores.triple.base_store import TripleStoreModel
from memonto.stores.triple.jena import ApacheJena
from memonto.stores.vector.base_store import VectorStoreModel
from memonto.stores.vector.chroma import Chroma


def configure_triple_store(store_provider: str, **config) -> TripleStoreModel:
    if store_provider == "apache_jena":
        return ApacheJena(**config)
    else:
        raise ValueError(f"Store {store_provider} not found")


def configure_vector_store(store_provider: str, **config) -> VectorStoreModel:
    if store_provider == "chroma":
        return Chroma(**config)
    else:
        raise ValueError(f"Store {store_provider} not found")


def configure_model(model_provider: str, **config) -> LLMModel:
    if model_provider == "openai":
        return OpenAI(**config)
    elif model_provider == "anthropic":
        return Anthropic(**config)
    else:
        raise ValueError(f"LLM model {model_provider} not found")


def _configure(
    config: dict,
) -> Tuple[Optional[TripleStoreModel], Optional[LLMModel], Optional[VectorStoreModel]]:
    triple_store, vector_store, llm = None, None, None

    if "triple_store" in config:
        store_config = config["triple_store"]
        store_provider = store_config["provider"]
        store_config = store_config["config"]

        triple_store = configure_triple_store(
            store_provider=store_provider,
            **store_config,
        )

    if "vector_store" in config:
        store_config = config["vector_store"]
        store_provider = store_config["provider"]
        store_config = store_config["config"]

        vector_store = configure_vector_store(
            store_provider=store_provider,
            **store_config,
        )

    if "model" in config:
        model_config = config["model"]
        model_provider = model_config["provider"]
        model_config = model_config["config"]

        llm = configure_model(
            model_provider=model_provider,
            **model_config,
        )

    return triple_store, vector_store, llm
