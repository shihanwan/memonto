import chromadb
import json
from chromadb.config import Settings
from pydantic import model_validator
from rdflib import Graph, RDF, Namespace
from typing import Literal

from memonto.stores.vector.base_store import VectorStoreModel
from memonto.utils.logger import logger
from memonto.utils.rdf import is_bnode_uuid, is_rdf_schema, to_human_readable
from memonto.utils.namespaces import TRIPLE_PROP


class Chroma(VectorStoreModel):
    name: str = "chroma"
    client: chromadb.Client = None
    mode: Literal["local", "remote"] = "local"
    auth: Literal["basic", "token"] = "basic"
    username: str = None
    password: str = None
    token: str = None
    path: str = None
    host: str = None
    port: int = None

    @model_validator(mode="after")
    def init(self) -> "Chroma":
        if self.mode == "local":
            self.client = chromadb.PersistentClient(
                path=self.path,
                settings=Settings(),
            )
        elif self.mode == "remote":
            if self.auth == "basic":
                self.client = chromadb.HttpClient(
                    host=self.host,
                    port=self.port,
                    headers={"Authorization": f"Basic {self.username}:{self.password}"},
                    settings=Settings(),
                )
            elif self.auth == "token":
                self.client = chromadb.HttpClient(
                    host=self.host,
                    port=self.port,
                    headers={"Authorization": f"Bearer {self.token}"},
                    settings=Settings(),
                )
        else:
            raise Exception("Invalid mode. Must be either 'local' or 'remote'.")

        return self

    def save(self, g: Graph, ns: dict[str, Namespace], id: str = None) -> None:
        collection = self.client.get_or_create_collection(id or "default")

        documents = []
        metadatas = []
        ids = []

        for s, p, o in g:
            if is_rdf_schema(p) or is_bnode_uuid(s, g):
                continue

            _s = to_human_readable(str(s), ns)
            _p = to_human_readable(str(p), ns)
            _o = to_human_readable(str(o), ns)

            id = ""
            for bnode in g.subjects(RDF.subject, s):
                if (bnode, RDF.predicate, p) in g and (bnode, RDF.object, o) in g:
                    id = g.value(bnode, TRIPLE_PROP.uuid)

            documents.append(f"{_s} {_p} {_o}")
            metadatas.append(
                {"triple": json.dumps({"s": str(s), "p": str(p), "o": str(o)})}
            )
            ids.append(f"{id}")

        if documents:
            try:
                collection.add(documents=documents, metadatas=metadatas, ids=ids)
            except Exception as e:
                logger.error(f"Chroma Save\n{e}\n")

    def search(self, message: str, id: str = None, k: int = 3) -> dict[str, dict]:
        try:
            collection = self.client.get_collection(id or "default")
            matched = collection.query(
                query_texts=[message],
                n_results=k,
            )
        except ValueError as e:
            return {}
        except Exception as e:
            logger.error(f"Chroma Search\n{e}\n")

        ids = matched.get("ids", [[]])[0]
        meta = matched.get("metadatas", [[]])[0]

        return {id: meta[i] if i < len(meta) else None for i, id in enumerate(ids)}

    def delete(self, id: str) -> None:
        try:
            self.client.delete_collection(id)
        except Exception as e:
            logger.error(f"Chroma Delete\n{e}\n")

    def delete_by_ids(self, graph_id: str, ids: list[str]) -> None:
        try:
            collection = self.client.get_collection(graph_id or "default")
            collection.delete(ids=list(ids))
        except Exception as e:
            logger.error(f"Chroma Delete by IDs\n{e}\n")
