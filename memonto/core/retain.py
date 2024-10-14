import ast
from rdflib import Graph, Namespace

from memonto.core.recall import _hydrate_triples
from memonto.llms.base_llm import LLMModel
from memonto.stores.triple.base_store import TripleStoreModel
from memonto.stores.vector.base_store import VectorStoreModel
from memonto.utils.logger import logger
from memonto.utils.rdf import _render


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
    llm: LLMModel,
    triple_store: TripleStoreModel,
    vector_store: VectorStoreModel,
    str_ontology: str,
    message: str, 
    id: str,
) -> str:
    potential_updates = vector_store.search(message=message, id=id, k=3)
    logger.debug(f"update_memory pre\n{potential_updates}\n")

    if not potential_updates:
        return ""
    
    # matched_graph = _hydrate_triples(
    #     triples=matched_triples,
    #     triple_store=triple_store,
    #     id=id,
    # )
    # matched_triples = matched_graph.serialize(format="turtle")
    # print(matched_triples)

    updates = llm.prompt(
        prompt_name="update_memory",
        temperature=0.2,
        ontology=str_ontology,
        user_message=message,
        existing_memory=str(potential_updates),
    )

    updated_memory = ast.literal_eval(updates)
    logger.debug(f"update_memory post\n{updated_memory}\n")
    
    # TODO: save to triple store

    pre_set = {(item['s'], item['p'], item['o']): item for item in potential_updates}
    post_set = {(item['s'], item['p'], item['o']): item for item in updated_memory}

    removed_triples = {key: pre_set[key] for key in pre_set if key not in post_set}
    added_triples = {key: post_set[key] for key in post_set if key not in pre_set}

    # TODO: raise error if removed doesnt match added

    if removed_triples and added_triples:
        try:
            triple_store.update(
                del_triples=removed_triples,
                add_triples=added_triples,
                id=id,
            )
        except Exception as e:
            pass
        
    # TODO: return nothing if nothing changed
    return str(updated_memory)


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
    updated_memory: str
) -> None:
    script = llm.prompt(
        prompt_name="commit_to_memory",
        temperature=0.2,
        ontology=str_ontology,
        user_message=message,
        updated_memory=updated_memory,
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

    if not ephemeral:
        triple_store.save(ontology=ontology, data=data, id=id)
        if vector_store:
            vector_store.save(g=data, id=id)

        # debug
        _render(g=data, format="image")

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
    ephemeral: bool,
) -> None:
    str_ontology = ontology.serialize(format="turtle")

    if auto_expand:
        ontology = expand_ontology(
            ontology=ontology,
            llm=llm,
            message=message,
        )

    # TODO: this should work with ephemeral as well but needs to be adjusted slightly
    updated_memory = update_memory(
        llm=llm,
        vector_store=vector_store,
        triple_store=triple_store,
        str_ontology=str_ontology,
        message=message, 
        id=id
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
        updated_memory=updated_memory
    )