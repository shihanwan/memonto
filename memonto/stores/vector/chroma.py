import chromadb
import json
from chromadb.config import Settings
from pydantic import model_validator
from rdflib import Graph
from typing import Literal

from memonto.stores.vector.base_store import VectorStoreModel
from memonto.utils.logger import logger
from memonto.utils.rdf import is_rdf_schema, remove_namespace


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

    def save(self, g: Graph, id: str = None) -> None:
        collection = self.client.get_or_create_collection(id or "default")

        documents = []
        metadatas = []
        ids = []

        for s, p, o in g:
            if is_rdf_schema(p):
                continue

            _s = remove_namespace(str(s))
            _p = remove_namespace(str(p))
            _o = remove_namespace(str(o))

            documents.append(f"{_s} {_p} {_o}")
            metadatas.append(
                {"triple": json.dumps({"s": str(s), "p": str(p), "o": str(o)})}
            )
            ids.append(f"{s}-{p}-{o}")

        if documents:
            try:
                collection.add(documents=documents, metadatas=metadatas, ids=ids)
            except Exception as e:
                logger.error(f"Chroma Save\n{e}\n")

    def search(self, message: str, id: str = None, k: int = 3) -> list[dict]:
        collection = self.client.get_collection(id or "default")

        try:
            matched = collection.query(
                query_texts=[message],
                n_results=k,
            )
        except Exception as e:
            logger.error(f"Chroma Search\n{e}\n")

        return [json.loads(t.get("triple", "{}")) for t in matched["metadatas"][0]]

    def delete(self, id: str) -> None:
        try:
            self.client.delete_collection(id)
        except Exception as e:
            logger.error(f"Chroma Delete\n{e}\n")
