from memonto.llms.openai import OpenAI
from memonto.llms.base_llm import LLMModel
from memonto.utils.config import (
    MODEL_NAME,
    MODEL_API_KEY,
    MODEL_TEMPERATURE,
)


def llm_factory(llm_provider: str) -> LLMModel:
    if llm_provider == "openai":
        return OpenAI(
            api_key=MODEL_API_KEY, model=MODEL_NAME, temperature=MODEL_TEMPERATURE
        )
    else:
        raise ValueError(f"LLM model {llm_provider} not found")
