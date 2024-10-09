# memonto 🧠

<p align="center">
    <img src="https://memonto.s3.amazonaws.com/memonto-readme-banner-3.png" alt="logo"/>
</p>

<p align="center">
    <a href="https://pypi.org/project/memonto/">
        <img src="https://img.shields.io/pypi/v/memonto?color=blue" alt="memonto-pypi">
    </a>
    <a href="https://pypi.org/project/memonto/">
        <img src="https://img.shields.io/pypi/dd/memonto?color=blue" alt="memonto-downloads">
    </a>
    <a href="https://opensource.org/licenses/Apache-2.0">
        <img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="memonto-license">
    </a>
</p>

`memonto` (_memory + ontology_) augments AI agents with long-term memory through a knowledge graph. The knowledge graph enables agents to remember past interactions, understand relationships between data, and improve contextual awareness.
- **Define** the ontology for the information you want memonto to retain.
- **Extract** that information from any unstructured text to a knowledge graph.
- **Query** your knowledge graph for intelligent summaries or raw data for RAG.

<p align="center">
    <img src="https://memonto.s3.amazonaws.com/memonto-explain-2.png" alt="explain"/>
</p>

## 🚀 Install
```sh
pip install memonto
```

## ⚙️ Configure
### Ephemeral Mode

Use `memonto` without any data stores.

> [!IMPORTANT]
> `ephemeral` mode is recommended for simpler/smaller use cases.

**Define RDF ontology**
```python
from memonto import Memonto
from rdflib import Graph, Namespace, RDF, RDFS

g = Graph()

HIST = Namespace("history:")

g.bind("hist", HIST)

g.add((HIST.Person, RDF.type, RDFS.Class))
g.add((HIST.Event, RDF.type, RDFS.Class))
g.add((HIST.Place, RDF.type, RDFS.Class))

g.add((HIST.isFrom, RDF.type, RDF.Property))
g.add((HIST.isFrom, RDFS.domain, HIST.Person))
g.add((HIST.isFrom, RDFS.range, HIST.Place))

g.add((HIST.participatesIn, RDF.type, RDF.Property))
g.add((HIST.participatesIn, RDFS.domain, HIST.Person))
g.add((HIST.participatesIn, RDFS.range, HIST.Event))
```

**Configure LLM**
```python
config = {
    "model": {
        "provider": "openai",
        "config": {
            "model": "gpt-4o",
            "api_key": "api-key",
        },
    }
}
```

**Enable Ephemeral Mode**
```python
memonto = Memonto(
    ontology=g,
    namespaces={"hist": HIST},
    ephemeral=True,
)
memonto.configure(config)
```

### Triple Store Mode

Enable triple store for persistent storage. To configure a triple store, add `triple_store` to the top level of your `config` dictionary.

**Configure Triple Store**
```python
config = {
    "triple_store": {
        "provider": "apache_jena",
        "config": {
            "connection_url": "http://localhost:8080/dataset_name",
        },
    },
}
```

**Install Apache Jena Fuseki**
1. Download Apache Jena Fuseki [here](https://jena.apache.org/download/index.cgi#apache-jena-fuseki).
2. Unzip to desired folder.
```sh
tar -xzf apache-jena-fuseki-X.Y.Z.tar.gz
```
3. Run a local server.
```sh
./fuseki-server --port=8080
```

### Triple + Vector Stores Mode

Enable vector store for contextual retrieval. To configure a vector store, add `vector_store` to the top level of your `config` dictionary.

> [!IMPORTANT]
> You must enable triple store in conjunction with vector store.

**Configure Local Vector Store**
```python
config = {
    "vector_store": {
        "provider": "chroma",
        "config": {
            "mode": "remote", 
            "path": ".local",
        },
    },
}
```

## 🧰 Usage
### Retain

Exatract information from text that maps onto your ontology. It will only extract data that matches onto an entity in your ontology.
```python
memonto.retain("Otto von Bismarck was a Prussian statesman and diplomat who oversaw the unification of Germany.")
```

### Recall

Get a summary of the current memories. You can provide a `context` for `memonto` to only summarize the memories that are relevant to that `context`. 

> [!IMPORTANT]
> When in `ephemeral` mode, all memories will be returned even if a `context` is provided.
```python
# retrieve summary of memory relevant to a context
memonto.recall("Germany could unify under Prussia or Austria.")

# retrieve summary of all stored memory
memonto.recall()
```

### Retrieve

Get raw knowledge graph data that can be programatically parsed or query for a summary that is relevant to a given context.
> [!IMPORTANT]
> When in `ephemeral` mode, raw queries are not supported.
```python
# retrieve raw memory data by schema
memonto.retrieve(uri=HIST.Person)

# retrieve raw memory data by SPARQL query
memonto.retrieve(query="SELECT ?s ?p ?o WHERE {GRAPH ?g {?s ?p ?o .}}")
```

### Forget

Forget about it.
```python
memonto.forget()
```

### RDF Namespaces

`memonto` supports RDF namespaces as well. Just pass in a dictionary with the namespace's name along with its `rdflib.Namespace` object.
```python
memonto = Memonto(
    ontology=g,
    namespaces={"hist": HIST},
)
```

### Auto Expand Ontology

Enable `memonto` to automatically expand your ontology to cover new data and relations. If `memonto` sees new information that **does not** fit onto your ontology, it will automatically add onto your ontology to cover that new information.
```python
memonto = Memonto(
    id="some_id_123",
    ontology=g,
    namespaces={"hist": HIST},
    auto_expand=True,
)
```

## 🔀 Async Usage

All main functionalities have an async version following this function naming pattern: `def a{func_name}:`
```python
async def main():
    await memonto.aretain("Some user query or message")
    await memonto.arecall()
    await memonto.aretrieve(uri=HIST.Person)
    await memonto.aforget()
```

## 🔮 Current and Upcoming Suport

| LLM       |     | Vector Store |     |Triple Store |     |
|-----------|-----|--------------|-----|-------------|-----|
|OpenAI     |✅   |Chroma        |✅    |Apache Jena  |✅   |
|Anthropic  |✅   |Pinecone      |🔜    |             |     |
|Meta llama |🔜   |Weaviate      |🔜    |             |     |

Feedback on what to support next is always welcomed!

## 💯 Requirements
Python 3.7 or higher.