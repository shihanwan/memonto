from anthropic import Anthropic as AnthropicClient, HUMAN_PROMPT, AI_PROMPT
from pydantic import model_validator

from memonto.llms.base_llm import LLMModel
from memonto.utils.llm import load_prompt


class Anthropic(LLMModel):
    name: str = "Anthropic"
    model: str = ...
    api_key: str = ...
    context_windows: dict = {
        "claude-3": 200_000,
        "claude-2.1": 200_000,
        "claude-2": 100_000,
    }
    temperature: float = 0.5
    client: AnthropicClient = None

    @model_validator(mode="after")
    def initialize_model(self) -> "Anthropic":
        self.client = AnthropicClient(api_key=self.api_key)
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
            **kwargs,
        )

        response = self.client.messages.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt_template}],
            max_tokens=4096,
            temperature=temperature or self.temperature,
        )

        if debug:
            print("\nPROMPT:\n", prompt_template)
            print("RESPONSE:\n", response)

        return response.content[0].text
