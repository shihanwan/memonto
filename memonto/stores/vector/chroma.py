import chromadb
import json
from chromadb.config import (
    DEFAULT_TENANT,
    DEFAULT_DATABASE,
    Settings,
)
from pathlib import Path
from pydantic import model_validator
from rdflib import Graph
from typing import Literal

from memonto.stores.vector.base_store import VectorStoreModel
from memonto.utils.rdf import is_rdf_schema


class Chroma(VectorStoreModel):
    name: str = "chroma"
    mode: Literal["local", "remote"] = "local"
    client: chromadb.Client = None

    @model_validator(mode="after")
    def init(self) -> "Chroma":
        if self.mode == "local":
            # TODO: refactor this code
            # TODO: store path as class variable
            project_root = Path(__file__).resolve().parent.parent.parent
            local_dir = project_root / ".local"
            local_dir.mkdir(parents=True, exist_ok=True)

            self.client = chromadb.PersistentClient(
                path=str(local_dir),
                settings=Settings(),
                tenant=DEFAULT_TENANT,
                database=DEFAULT_DATABASE,
            )
        elif self.mode == "remote":
            # TODO: Add remote connection settings
            self.client = chromadb.Client(
                settings=Settings(),
                tenant=DEFAULT_TENANT,
                database=DEFAULT_DATABASE,
            )
        else:
            raise Exception("Invalid mode. Must be either 'local' or 'remote'.")

        return self

    def save(self, g: Graph, id: str = None) -> None:
        collection = self.client.get_or_create_collection(id or "default")

        for s, p, o in g:
            if is_rdf_schema(p):
                continue

            # TODO: hacked af, needs fixing probably with how we save or load namespaces
            _s = s.split("/")[-1].split("#")[-1].split(":")[-1]
            _p = p.split("/")[-1].split("#")[-1].split(":")[-1]
            _o = o.split("/")[-1].split("#")[-1].split(":")[-1]

            edge = f"{_s} {_p} {_o}"

            collection.add(
                documents=edge,
                metadatas={
                    "triple": json.dumps({"s": str(s), "p": str(p), "o": str(o)})
                },
                ids=f"{s}-{p}-{o}",
            )

    def search(self, message: str, id: str = None, k: int = 3) -> list[dict]:
        collection = self.client.get_collection(id or "default")

        matched = collection.query(
            query_texts=[message],
            n_results=k,
        )

        return [json.loads(t.get("triple", "{}")) for t in matched["metadatas"][0]]
