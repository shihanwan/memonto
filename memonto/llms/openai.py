import tiktoken
from openai import OpenAI as OpenAIClient
from pydantic import model_validator

from memonto.llms.base_llm import LLMModel
from memonto.utils.llm import load_prompt


class OpenAI(LLMModel):
    name: str = "OpenAI"
    api_key: str = ...
    llm_name: str = ...
    context_windows: dict = {
        "gpt-3.5": 16_385,
        "gpt-4-turbo": 128_000,
        "gpt-4o": 128_000,
    }
    temperature: float = ...
    client: OpenAIClient = None

    @model_validator(mode="after")
    def initialize_model(self) -> "OpenAI":
        self.client = OpenAIClient(api_key=self.api_key)
        return self

    def fit_to_context_window(self, prompt_name: str, **kwargs) -> str:
        prompt_template = load_prompt(prompt_name)
        prompt_str = prompt_template.template

        encoding = tiktoken.encoding_for_model(self.llm_name)
        max_tokens = 128_000
        buffer = 0.1

        prompt_tokens = encoding.encode(prompt_str)
        remaining_tokens = max_tokens * (1 - buffer) - len(prompt_tokens)

        truncated_kwargs = {}

        for key, value in kwargs.items():
            value_tokens = encoding.encode(value)

            if len(value_tokens) > remaining_tokens:
                truncated_value = encoding.decode(value_tokens[:remaining_tokens])
                truncated_kwargs[key] = truncated_value
                remaining_tokens = 0
            else:
                truncated_kwargs[key] = value
                remaining_tokens -= len(value_tokens)

            if remaining_tokens <= 0:
                break

        return prompt_template.substitute(**truncated_kwargs)

    def prompt(
        self,
        prompt_name: str,
        temperature: float = None,
        debug: bool = False,
        **kwargs,
    ) -> str:
        prompt_template = self.fit_to_context_window(
            prompt_name=prompt_name,
            **kwargs,
        )

        response = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt_template,
                }
            ],
            model=self.llm_name,
            temperature=temperature or self.temperature,
        )

        if debug:
            print("\nPROMPT:\n", prompt_template)
            print("RESPONSE:\n", response)

        return response.choices[0].message.content
