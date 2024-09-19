import tiktoken
from openai import OpenAI as OpenAIClient
from pydantic import model_validator

from memonto.llms.base_llm import LLMModel
from memonto.utils.llm import load_prompt


class OpenAI(LLMModel):
    name: str = "OpenAI"
    model: str = ...
    api_key: str = ...
    context_windows: dict = {
        "gpt-3.5": 16_385,
        "gpt-4-turbo": 128_000,
        "gpt-4o": 128_000,
    }
    temperature: float = 0.5
    client: OpenAIClient = None

    @model_validator(mode="after")
    def initialize_model(self) -> "OpenAI":
        self.client = OpenAIClient(api_key=self.api_key)
        return self

    def prompt(
        self,
        prompt_name: str,
        temperature: float = None,
        debug: bool = False,
        **kwargs,
    ) -> str:
        prompt_template = self._fit_to_context_window(
            prompt_name=prompt_name,
            encoding_model=self.model,
            **kwargs,
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt_template}],
            temperature=temperature or self.temperature,
        )

        if debug:
            print("\nPROMPT:\n", prompt_template)
            print("RESPONSE:\n", response)

        return response.choices[0].message.content
