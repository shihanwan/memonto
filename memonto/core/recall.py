from rdflib import Graph, URIRef, Literal, BNode

from memonto.llms.base_llm import LLMModel
from memonto.stores.triple.base_store import TripleStoreModel
from memonto.stores.vector.base_store import VectorStoreModel
from memonto.utils.logger import logger
from memonto.utils.namespaces import TRIPLE_PROP
from memonto.utils.rdf import serialize_graph_without_ids


def get_contextual_memory(
    data: Graph,
    vector_store: VectorStoreModel,
    triple_store: TripleStoreModel,
    context: str,
    id: str,
    ephemeral: bool,
):
    memory = ""

    if ephemeral:
        memory = serialize_graph_without_ids(data)
    elif context:
        try:
            matched = vector_store.search(message=context, id=id)
            logger.debug(f"Matched Triples Raw\n{matched}\n")

            memory = triple_store.get_context(
                matched=matched,
                graph_id=id,
                depth=1,
            )
        except ValueError as e:
            logger.debug(f"Recall Exception\n{e}\n")
    else:
        memory = triple_store.get_all(graph_id=id)

    logger.debug(f"Contextual Memory\n{memory}\n")
    return memory


def _recall(
    data: Graph,
    llm: LLMModel,
    vector_store: VectorStoreModel,
    triple_store: TripleStoreModel,
    context: str,
    id: str,
    ephemeral: bool,
) -> str:
    memory = get_contextual_memory(
        data=data,
        vector_store=vector_store,
        triple_store=triple_store,
        context=context,
        id=id,
        ephemeral=ephemeral,
    )

    summarized_memory = llm.prompt(
        prompt_name="summarize_memory",
        context=context or "",
        memory=memory,
    )

    logger.debug(f"Summarized Memory\n{summarized_memory}\n")

    return summarized_memory
