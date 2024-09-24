from typing import Optional, Tuple

from memonto.llms.anthropic import Anthropic
from memonto.llms.openai import OpenAI
from memonto.llms.base_llm import LLMModel
from memonto.stores.base_store import StoreModel
from memonto.stores.jena import ApacheJena


def configure_store(store_provider: str, **config) -> StoreModel:
    if store_provider == "apache_jena":
        return ApacheJena(**config)
    else:
        raise ValueError(f"Store {store_provider} not found")


def configure_model(model_provider: str, **config) -> LLMModel:
    if model_provider == "openai":
        return OpenAI(**config)
    elif model_provider == "anthropic":
        return Anthropic(**config)
    else:
        raise ValueError(f"LLM model {model_provider} not found")


def configure(config: dict) -> Tuple[Optional[StoreModel], Optional[LLMModel]]:
    store, llm = None, None

    if "store" in config:
        store_config = config["store"]
        store_provider = store_config["provider"]
        store_config = store_config["config"]

        store = configure_store(
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

    return store, llm
