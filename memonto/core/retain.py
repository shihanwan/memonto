from rdflib import Graph, Namespace

from memonto.llms.base_llm import LLMModel
from memonto.stores.triple.base_store import TripleStoreModel
from memonto.stores.vector.base_store import VectorStoreModel
from memonto.utils.logger import logger
from memonto.utils.rdf import _render


def run_script(
    script: str,
    exec_ctx: dict,
    message: str,
    ontology: str,
    data: Graph,
    llm: LLMModel,
    max_retries: int = 1,
    initial_temperature: float = 0.2,
) -> Graph:
    attempt = 0

    while attempt < max_retries:
        try:
            exec(script, exec_ctx)
        except Exception as e:
            logger.debug(f"Run Script (Attempt {attempt + 1}) Failed\n{e}\n")

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

            logger.debug(f"Fixed Script (Attempt {attempt + 1})\n{script}\n")

        attempt += 1

    return data


def expand_ontology(
    ontology: Graph,
    llm: LLMModel,
    message: str,
) -> Graph:
    script = llm.prompt(
        prompt_name="expand_ontology",
        temperature=0.3,
        ontology=ontology.serialize(format="turtle"),
        user_message=message,
    )

    logger.debug(f"Expand Script\n{script}\n")

    # TODO: handle exceptions just like in run_script
    exec(script, {"ontology": ontology})

    logger.debug(f"Ontology Graph\n{ontology.serialize(format='turtle')}\n")

    return ontology


def _retain(
    ontology: Graph,
    namespaces: dict[str, Namespace],
    data: Graph,
    llm: LLMModel,
    triple_store: TripleStoreModel,
    vector_store: VectorStoreModel,
    message: str,
    id: str,
    auto_expand: bool,
    ephemeral: bool,
) -> None:
    if auto_expand:
        ontology = expand_ontology(
            ontology=ontology,
            llm=llm,
            message=message,
        )

    str_ontology = ontology.serialize(format="turtle")

    script = llm.prompt(
        prompt_name="commit_to_memory",
        temperature=0.2,
        ontology=str_ontology,
        user_message=message,
    )

    logger.debug(f"Retain Script\n{script}\n")

    data = run_script(
        script=script,
        exec_ctx={"data": data} | namespaces,
        message=message,
        ontology=str_ontology,
        data=data,
        llm=llm,
    )

    logger.debug(f"Data Graph\n{data.serialize(format='turtle')}\n")

    if not ephemeral:
        triple_store.save(ontology=ontology, data=data, id=id)
        if vector_store:
            vector_store.save(g=data, id=id)

        # _render(g=data, format="image")
        data.remove((None, None, None))
