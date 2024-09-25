from rdflib import Graph

from memonto.llms.base_llm import LLMModel
from memonto.utils.rdf import is_rdf_schema


def recall_memory(
    ontology: Graph,
    data: Graph,
    llm: LLMModel,
    message: str,
    id: str,
) -> str:
    print(ontology.serialize(format="turtle"))

    summarized_memory = llm.prompt(
        prompt_name="summarize_memory",
        memory=data.serialize(format="turtle"),
    )

    return summarized_memory
