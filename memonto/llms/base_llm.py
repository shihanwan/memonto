import tiktoken
from abc import ABC, abstractmethod
from pydantic import BaseModel, ConfigDict

from memonto.utils.llm import load_prompt


class LLMModel(BaseModel, ABC):
    name: str = ...
    model: str = ...
    api_key: str = ...
    context_windows: dict = ...
    temperature: float = ...
    client: object = None
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @abstractmethod
    def prompt(
        self,
        prompt_name: str,
        temperature: float,
        debug: bool,
        **kwargs,
    ) -> str:
        """
        Generate a response from the model based on the given prompt.

        :param prompt_name: The name of the prompt to use.
        :param temperature: The temperature to use when generating the response.
        :param debug: Whether to output debug logs.
        :param kwargs: Additional keyword arguments to pass to the model.

        :return: The model's response as a string.
        """
        pass

    def _get_context_window(self, default: int = 32_000) -> int:
        """
        Return the context window size for the model if it doesn't exist then a default value is used.

        :return: The model's context window size.
        """
        for key in self.context_windows:
            if self.model in key:
                return self.context_windows[key]

        return default

    def _fit_to_context_window(
        self,
        prompt_name: str,
        encoding_model: str = "cl100k_base",
        **kwargs,
    ) -> str:
        """
        Render the a prompt template with the given keyword arguments and fit it to the model's context window.
        Prompts are truncated based on the order they are based in.

        :param prompt_name: The name of the prompt to use.
        :param kwargs: Additional keyword arguments to pass to the prompt template.

        :return: The fully fitted prompt as a string.
        """
        prompt_template = load_prompt(prompt_name)
        prompt_str = prompt_template.template

        try:
            encoding = tiktoken.encoding_for_model(encoding_model)
        except Exception:
            encoding = tiktoken.get_encoding(encoding_model)

        max_tokens = self._get_context_window()
        buffer = 0.2

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
