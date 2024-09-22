from rdflib import Graph, Namespace

from memonto.llms.base_llm import LLMModel
from memonto.stores.base_store import StoreModel


def execute_script(
    script: str,
    g: Graph,
    n: Namespace,
    llm: LLMModel,
    query: str,
    ontology: str,
    debug: bool = False,
    max_retries: int = 1,
    initial_temperature: float = 0.2,
) -> Graph:
    attempt = 0

    while attempt < max_retries:
        try:
            exec(script, {"g": g, "n": n})
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
                user_message=query,
            )

            if debug:
                print(f"Generated script on attempt {attempt + 1}:\n{script}")

        attempt += 1

    return g


def commit_memory(
    g: Graph,
    n: Namespace,
    llm: LLMModel,
    store: StoreModel,
    query: str,
    id: str,
    auto_expand: bool,
    debug: bool,
) -> None:
    gt = g.serialize(format="turtle")

    if auto_expand:
        instruction = "- If there are information that is valuable but doesn't fit onto the ontology then add them as well."
        temperature = 0.5
    else:
        instruction = "- NEVER generate code that adds information that DOES NOT fit onto the ontology."
        temperature = 0.2

    script = llm.prompt(
        prompt_name="commit_to_memory",
        temperature=temperature,
        ontology=gt,
        user_message=query,
        instruction=instruction,
    )

    if debug:
        print(script)

    g = execute_script(
        script=script,
        g=g,
        n=n,
        llm=llm,
        query=query,
        ontology=gt,
        debug=debug,
    )

    store.save(g, id)
