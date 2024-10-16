import ast
from rdflib import Graph, Namespace

from memonto.llms.base_llm import LLMModel
from memonto.stores.triple.base_store import TripleStoreModel
from memonto.stores.vector.base_store import VectorStoreModel
from memonto.utils.logger import logger
from memonto.utils.rdf import (
    _render,
    find_updated_triples,
    find_updated_triples_ephemeral,
    hydrate_graph_with_ids,
)


def _run_script(
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


def update_memory(
    data: Graph,
    llm: LLMModel,
    triple_store: TripleStoreModel,
    vector_store: VectorStoreModel,
    str_ontology: str,
    message: str,
    id: str,
    ephemeral: bool,
) -> str:
    if ephemeral:
        data_list = []

        for s, p, o in data:
            data_list.append(
                {
                    "s": str(s),
                    "p": str(p),
                    "o": str(o),
                }
            )

        logger.debug(f"existing memories\n{data_list}\n")

        updates = llm.prompt(
            prompt_name="update_memory",
            temperature=0.2,
            ontology=str_ontology,
            user_message=message,
            existing_memory=str(data_list),
        )
        logger.debug(f"updated memories\n{updates}\n")

        updates = ast.literal_eval(updates)
        updated_memory = find_updated_triples_ephemeral(updates, data_list)
        logger.debug(f"memories diff\n{updated_memory}\n")

        for s, p, o in data:
            for t in updated_memory:
                if str(s) == t["s"] and str(p) == t["p"] and str(o) == t["o"]:
                    data.remove((s, p, o))

        return str(updated_memory)
    else:
        matched = vector_store.search(message=message, id=id, k=3)
        logger.debug(f"existing memories\n{matched}\n")

        if not matched:
            return ""

        updates = llm.prompt(
            prompt_name="update_memory",
            temperature=0.2,
            ontology=str_ontology,
            user_message=message,
            existing_memory=str(matched),
        )

        updates = ast.literal_eval(updates)
        logger.debug(f"updated memories\n{updates}\n")

        updated_memory = find_updated_triples(original=matched, updated=updates)
        logger.debug(f"memories diff\n{updated_memory}\n")

        if not updated_memory:
            return ""

        vector_store.delete_by_ids(graph_id=id, ids=updated_memory.keys())
        triple_store.delete_by_ids(graph_id=id, ids=updated_memory.keys())

        return str(updated_memory)


def find_relevant_memories(
    data: Graph,
    vector_store: VectorStoreModel,
    message: str,
    id: str,
    ephemeral: bool,
) -> str:
    relevant_memory = ""

    if ephemeral:
        relevant_memory = str(data.serialize(format="turtle"))
    else:
        relevant_memory = str(vector_store.search(message=message, id=id, k=3))

    logger.debug(f"relevant_memory\n{relevant_memory}\n")
    return relevant_memory


def save_memory(
    ontology: Graph,
    namespaces: dict[str, Namespace],
    data: Graph,
    llm: LLMModel,
    triple_store: TripleStoreModel,
    vector_store: VectorStoreModel,
    message: str,
    id: str,
    ephemeral: bool,
    str_ontology: str,
    updated_memory: str,
) -> None:
    relevant_memory = find_relevant_memories(
        data=data,
        vector_store=vector_store,
        message=message,
        id=id,
        ephemeral=ephemeral,
    )

    script = llm.prompt(
        prompt_name="commit_to_memory",
        temperature=0.2,
        ontology=str_ontology,
        user_message=message,
        updated_memory=updated_memory,
        relevant_memory=relevant_memory,
    )

    logger.debug(f"Retain Script\n{script}\n")

    data = _run_script(
        script=script,
        exec_ctx={"data": data} | namespaces,
        message=message,
        ontology=str_ontology,
        data=data,
        llm=llm,
    )

    logger.debug(f"Data Graph\n{data.serialize(format='turtle')}\n")

    # debug
    # _render(g=data, ns=namespaces, format="image")

    if not ephemeral:
        hydrate_graph_with_ids(data)
        triple_store.save(ontology=ontology, data=data, id=id)

        if vector_store:
            vector_store.save(g=data, ns=namespaces, id=id)

        data.remove((None, None, None))


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
    auto_update: bool,
    ephemeral: bool,
) -> None:
    str_ontology = ontology.serialize(format="turtle")
    updated_memory = ""

    if auto_expand:
        ontology = expand_ontology(
            ontology=ontology,
            llm=llm,
            message=message,
        )

    if auto_update:
        updated_memory = update_memory(
            data=data,
            llm=llm,
            vector_store=vector_store,
            triple_store=triple_store,
            str_ontology=str_ontology,
            message=message,
            id=id,
            ephemeral=ephemeral,
        )

    save_memory(
        ontology=ontology,
        namespaces=namespaces,
        data=data,
        llm=llm,
        triple_store=triple_store,
        vector_store=vector_store,
        message=message,
        id=id,
        ephemeral=ephemeral,
        str_ontology=str_ontology,
        updated_memory=updated_memory,
    )
