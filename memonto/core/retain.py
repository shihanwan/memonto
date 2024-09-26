from rdflib import Graph, Namespace

from memonto.llms.base_llm import LLMModel
from memonto.stores.triple.base_store import TripleStoreModel
from memonto.stores.vector.base_store import VectorStoreModel


def run_script(
    script: str,
    exec_ctx: dict,
    message: str,
    ontology: str,
    data: Graph,
    llm: LLMModel,
    max_retries: int = 1,
    initial_temperature: float = 0.2,
    debug: bool = False,
) -> Graph:
    attempt = 0

    while attempt < max_retries:
        try:
            exec(script, exec_ctx)
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


def expand_ontology(
    ontology: Graph,
    llm: LLMModel,
    message: str,
    debug: bool,
) -> Graph:
    script = llm.prompt(
        prompt_name="expand_ontology",
        temperature=0.3,
        ontology=ontology.serialize(format="turtle"),
        user_message=message,
    )

    # TODO: handle exceptions just like in run_script
    exec(script, {"ontology": ontology})

    return ontology


def retain_memory(
    ontology: Graph,
    namespaces: dict[str, Namespace],
    data: Graph,
    llm: LLMModel,
    triple_store: TripleStoreModel,
    vector_store: VectorStoreModel,
    message: str,
    id: str,
    auto_expand: bool,
    debug: bool,
):
    if auto_expand:
        ontology = expand_ontology(
            ontology=ontology,
            llm=llm,
            message=message,
            debug=debug,
        )

    str_ontology = ontology.serialize(format="turtle")

    script = llm.prompt(
        prompt_name="commit_to_memory",
        temperature=0.2,
        ontology=str_ontology,
        user_message=message,
    )

    if debug:
        print(f"script:\n{script}\n")

    data = run_script(
        script=script,
        exec_ctx={"data": data} | namespaces,
        message=message,
        ontology=str_ontology,
        data=data,
        llm=llm,
        debug=debug,
    )

    if debug:
        print(f"data:\n{data.serialize(format='turtle')}\n")

    triple_store.save(ontology=ontology, data=data, id=id)
    vector_store.save(g=data, id=id)
