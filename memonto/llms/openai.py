from openai import OpenAI as OpenAIClient
from pydantic import model_validator

from memonto.llms.base_llm import LLMModel
from memonto.utils.prompt import load_prompt

class OpenAI(LLMModel):
    name: str = "OpenAI"
    context_window: int = 32_000
    api_key: str = ...
    model: str = ...
    temperature: float = ...
    client: OpenAIClient = None

    @model_validator(mode="after")
    def initialize_model(self) -> "OpenAI":
        self.client = OpenAIClient(api_key=self.api_key)
        return self

    def prompt(
        self,
        prompt: str,
        temperature: float = None,
        debug: bool = False,
        **kwargs,
    ) -> str:
        prompt_template = load_prompt(prompt).substitute(**kwargs)        

        response = self.client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": prompt_template,
            }],
            model=self.model,
            temperature=temperature or self.temperature,
        )

        if debug:
            print("\nPROMPT:\n", prompt_template)
            print("RESPONSE:\n", response)

        return response.choices[0].message.content