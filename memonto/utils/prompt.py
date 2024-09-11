from pathlib import Path
from string import Template


def load_prompt(prompt_name: str) -> Template:
    base_dir = Path(__file__).resolve().parent.parent
    file_path = base_dir / "prompts" / f"{prompt_name}.prompt"

    with open(file_path, "r") as file:
        return Template(file.read())
