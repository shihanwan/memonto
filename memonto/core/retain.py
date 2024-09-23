from rdflib import Graph, Namespace

from memonto.llms.base_llm import LLMModel
from memonto.stores.base_store import StoreModel


def execute_script(
    script: str,
    ontology: str,
    namespaces: dict[str, Namespace],
    data: Graph,
    llm: LLMModel,
    message: str,
    debug: bool = False,
    max_retries: int = 1,
    initial_temperature: float = 0.2,
) -> Graph:
    attempt = 0

    while attempt < max_retries:
        try:
            exec(script, {"data": data} | namespaces)
            if debug:
                print(f"Script executed successfully on attempt {attempt + 1}")
        except Exception as e:
            if debug:
                print(f"Attempt {attempt + 1} to commit memory failed with error: {e}")

            temperature = initial_temperature * (2**attempt)
            temperature = min(temperature, 1.0)

            script = llm.prompt(
                prompt_name="commit_to_memory_error_handling",
                temperature=temperature,
                error=str(e),
                script=script,
                ontology=ontology,
                user_message=message,
            )

            if debug:
                print(f"Generated script on attempt {attempt + 1}:\n{script}")

        attempt += 1

    return data


def retain_memory(
    ontology: Graph,
    namespaces: dict[str, Namespace],
    data: Graph,
    llm: LLMModel,
    store: StoreModel,
    message: str,
    id: str,
    auto_expand: bool,
    debug: bool,
):
    ontology = ontology.serialize(format="turtle")
    namespaces = namespaces

    if auto_expand:
        instruction = "- If there are information that is valuable but doesn't fit onto the ontology then add them as well."
        temperature = 0.5
    else:
        instruction = "- NEVER generate code that adds information that DOES NOT fit onto the ontology."
        temperature = 0.2

    script = llm.prompt(
        prompt_name="commit_to_memory",
        temperature=temperature,
        ontology=ontology,
        user_message=message,
        instruction=instruction,
    )

    if debug:
        print(f"script:\n{script}\n")

    data = execute_script(
        script=script,
        ontology=ontology,
        namespaces=namespaces,
        data=data,
        llm=llm,
        message=message,
        debug=debug,
    )

    if debug:
        print(f"data:\n{data.serialize(format='turtle')}\n")

    store.save(data, id)
