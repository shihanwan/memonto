from abc import ABC, abstractmethod
from pydantic import BaseModel


class LLMModel(BaseModel, ABC):
    name: str = ...
    context_window: int = ...

    @abstractmethod
    def prompt(
        self,
        prompt: str,
        temperature: float,
        debug: bool,
        **kwargs,
    ) -> str:
        """
        Generate a response from the model based on the given prompt.

        :param prompt: The input text to generate a response for.
        :param temperature: The temperature to use when generating the response.
        :param debug: Whether to output debug logs.
        :param kwargs: Additional keyword arguments to pass to the model.

        :return: The model's response as a string.
        """
        pass

    class Config:
        arbitrary_types_allowed = True
