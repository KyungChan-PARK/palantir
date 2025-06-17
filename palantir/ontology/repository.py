"""Ontology repository with DuckDB, graph backend and embedding store."""

from __future__ import annotations

import json
import os
from typing import Any, Optional, Type, TypeVar
from uuid import UUID

import duckdb
import networkx as nx
from neo4j import GraphDatabase

from .base import OntologyLink, OntologyObject
from .embedding_store import EmbeddingStore

T = TypeVar("T", bound=OntologyObject)


class OntologyRepository:
    """Manage ontology objects with sync across stores."""

    def __init__(self, backend: str = "networkx", db_path: str = "ontology.db") -> None:
        self.embeddings = EmbeddingStore()
        self.conn = duckdb.connect(db_path)
        self._init_tables()
        self.backend = backend
        if backend == "neo4j":
            url = os.getenv("NEO4J_URL", "bolt://localhost:7687")
            user = os.getenv("NEO4J_USER", "neo4j")
            pw = os.getenv("NEO4J_PASS", "test")
            self.driver = GraphDatabase.driver(url, auth=(user, pw))
        else:
            self.graph = nx.MultiDiGraph()

    def _init_tables(self) -> None:
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS objects(id VARCHAR PRIMARY KEY, type VARCHAR, data JSON)"
        )
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS links(id VARCHAR, source_id VARCHAR, target_id VARCHAR, type VARCHAR, data JSON)"
        )

    def close(self) -> None:
        if hasattr(self, "driver"):
            self.driver.close()
        self.conn.close()

    def add_object(self, obj: OntologyObject) -> None:
        if self.backend == "neo4j":
            with self.driver.session() as session:
                session.run(
                    "MERGE (n:Ontology {id: $id}) SET n.type=$type, n.data=$data",
                    id=str(obj.id),
                    type=obj.type,
                    data=json.dumps(obj.dict()),
                )
        else:
            self.graph.add_node(
                obj.id,
                type=obj.type,
                data=obj.dict(),
                created_at=obj.created_at,
                updated_at=obj.updated_at,
            )
        self.conn.execute(
            "INSERT OR REPLACE INTO objects VALUES (?, ?, ?)",
            [str(obj.id), obj.type, json.dumps(obj.dict())],
        )
        text = (
            obj.properties.get("description")
            if isinstance(obj.properties, dict)
            else None
        )
        text = text or getattr(obj, "description", str(obj))
        self.embeddings.add(str(obj.id), text, {"type": obj.type})

    def add_link(self, link: OntologyLink) -> None:
        if self.backend == "neo4j":
            with self.driver.session() as session:
                session.run(
                    "MATCH (a {id:$src}),(b {id:$tgt}) MERGE (a)-[r:%s {id:$id}]->(b) SET r.data=$data"
                    % link.relationship_type,
                    src=str(link.source_id),
                    tgt=str(link.target_id),
                    id=str(link.id),
                    data=json.dumps(link.dict()),
                )
        else:
            self.graph.add_edge(
                link.source_id,
                link.target_id,
                key=link.id,
                type=link.relationship_type,
                data=link.dict(),
                created_at=link.created_at,
            )
        self.conn.execute(
            "INSERT INTO links VALUES (?, ?, ?, ?, ?)",
            [
                str(link.id),
                str(link.source_id),
                str(link.target_id),
                link.relationship_type,
                json.dumps(link.dict()),
            ],
        )

    def get_object(self, obj_id: UUID, model_cls: Type[T]) -> Optional[T]:
        if self.backend == "neo4j":
            with self.driver.session() as session:
                rec = session.run(
                    "MATCH (n {id:$id}) RETURN n.data AS d", id=str(obj_id)
                ).single()
                if not rec:
                    return None
                data = json.loads(rec["d"])
                return model_cls(**data)
        if self.graph.has_node(obj_id):
            node_data = self.graph.nodes[obj_id]["data"]
            return model_cls(**node_data)
        return None

    def update_object(self, obj: OntologyObject) -> None:
        self.add_object(obj)

    def delete_object(self, obj_id: UUID) -> None:
        if self.backend == "neo4j":
            with self.driver.session() as session:
                session.run("MATCH (n {id:$id}) DETACH DELETE n", id=str(obj_id))
        else:
            if not self.graph.has_node(obj_id):
                raise ValueError(f"Object with ID {obj_id} not found")
            self.graph.remove_node(obj_id)
        self.conn.execute("DELETE FROM objects WHERE id=?", [str(obj_id)])

    def search_objects(
        self,
        obj_type: Optional[str] = None,
        properties: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        results = []
        query = "SELECT data FROM objects"
        conds = []
        params: list[Any] = []
        if obj_type:
            conds.append("type=?")
            params.append(obj_type)
        if conds:
            query += " WHERE " + " AND ".join(conds)
        for row in self.conn.execute(query, params).fetchall():
            data = json.loads(row[0])
            if properties:
                match = True
                for k, v in properties.items():
                    if data.get(k) != v:
                        match = False
                        break
                if not match:
                    continue
            results.append(data)
        return results
