# MemOnto 🧠

`memonto` adds memory to AI agents with an emphasis on user defined ontology. Define your own [RDF](https://www.w3.org/RDF/) ontology then have `memonto` automatically extract information that matches onto that ontology.

## 🚀 Install
```sh
pip install memonto
```

## ⚙️ Configure
**Ephemeral Mode**

Use `memonto` all in memory without any data stores.

> [!IMPORTANT]
> When in ephemeral mode, there can be performance issues if the memory data grows too large. This mode is recommended for smaller use cases.

```python
from memonto import Memonto
from rdflib import Graph, Namespace, RDF, RDFS

g = Graph()

HIST = Namespace("history:")

g.bind("hist", HIST)

g.add((HIST.Person, RDF.type, RDFS.Class))
g.add((HIST.Event, RDF.type, RDFS.Class))
g.add((HIST.Place, RDF.type, RDFS.Class))

memonto = Memonto(
    ontology=g,
    namespaces={"hist": HIST},
    ephemeral=True,
)
```

**With Triple Store**

A triple store enables the persistent storage of memory data. Currently supports Apache Jena Fuseki as a triple store.
```python
config = {
    "triple_store": {
        "provider": "apache_jena",
        "config": {
            "connection_url": "http://localhost:8080/",
        },
    },
    "model": {
        "provider": "openai",
        "config": {
            "model": "gpt-4o",
            "api_key": "api-key",
        },
    }
}

memonto = Memonto(
    ontology=g,
    namespaces={"hist": HIST},
)
memonto.configure(config)
```

**With Triple + Vector Stores**

A vector store enables contextual retrieval of memory data, it must be used in conjunction with a triple store. Currently supports Chroma as a vector store. 
```python
config = {
    "triple_store": {
        "provider": "apache_jena",
        "config": {
            "connection_url": "http://localhost:8080/dataset_name",
        },
    },
    "vector_store": {
        "provider": "chroma",
        "config": {
            "mode": "local", 
            "path": ".local",
        },
    },
    "model": {
        "provider": "openai",
        "config": {
            "model": "gpt-4o",
            "api_key": "api-key",
        },
    }
}

memonto = Memonto(
    ontology=g,
    namespaces={"hist": HIST},
)
memonto.configure(config)
```

## 🧰 Usage
**RDF Namespaces**

`memonto` supports RDF namespaces as well. Just pass in a dictionary with the namespace's name along with its `rdflib.Namespace` object.
```python
memonto = Memonto(
    ontology=g,
    namespaces={"hist": HIST},
)
```

**Memory ID**

For when you want to associate an ontology and memories to an unique `id`.
```python
memonto = Memonto(
    id="some_id_123",
    ontology=g,
    namespaces={"hist": HIST},
)
```

**Retain**

Extract the relevant information from a message that maps onto your ontology. It will only extract data that matches onto an entity in your ontology.
```python
memonto.retain("Otto von Bismarck was a Prussian statesman who oversaw the unification of Germany.")
```

**Recall**

Get a summary of the currently stored memories. You can provide a `context` for `memonto` to only summarize the memories that are relevant to that `context`. 

> [!IMPORTANT]
> When in ephemeral mode, all memories will be returned even if a `context` is provided.
```python
# retrieve summary of memory relevant to a context
memonto.recall("Germany could unify under Prussia or Austria.")

# retrieve summary of all stored memory
memonto.recall()
```

**Retrieve**

Get the raw memory data that can be programatically accessed. Instead of a summary, get the actual stored data as a `list[dict]` that can then be manipulated in code.
> [!IMPORTANT]
> When in ephemeral mode, raw queries are not supported.
```python
# retrieve raw memory data by schema
memonto.retrieve(uri=HIST.Person)

# retrieve raw memory data by SPARQL query
memonto.retrieve(query="SELECT ?s ?p ?o WHERE {GRAPH ?g {?s ?p ?o .}}")
```

**Forget**

Forget about it.
```python
memonto.forget()
```

**Auto Expand Ontology**

Enable `memonto` to automatically expand your ontology to cover new information. If `memonto` sees new information that **does not** fit onto your ontology, it will automatically add onto your ontology to cover that new information.
```python
memonto = Memonto(
    id="some_id_123",
    ontology=g,
    namespaces={"hist": HIST},
    auto_expand=True,
)
```

## 🔀 Async Usage

All main functionalities have an async version following this function naming pattern: **a{func_name}**
```python
async def main():
    await memonto.aretain("Some user query or message")
    await memonto.arecall()
    await memonto.aretrieve(uri=HIST.Person)
    await memonto.aforget()
```

## 🔧 Additional Setup

**Apache Jena**
1. Download Apache Jena Fuseki [here](https://jena.apache.org/download/index.cgi#apache-jena-fuseki).
2. Unzip to desired folder.
```sh
tar -xzf apache-jena-fuseki-X.Y.Z.tar.gz
```
3. Run a local server.
```sh
./fuseki-server --port=8080
```


## 🔮 Current and Upcoming

| LLM       |     | Vector Store |     |Triple Store |     |
|-----------|-----|--------------|-----|-------------|-----|
|OpenAI     |✅   |Chroma        |✅    |Apache Jena  |✅   |
|Anthropic  |✅   |Pinecone      |🔜    |             |     |
|Meta llama |🔜   |Weaviate      |🔜    |             |     |

Feedback on what to support next is always welcomed!

## 💯 Requirements
Python 3.7 or higher.