"""Ontology graph repository using NetworkX."""

from typing import Any, Dict, List, Optional, Type, TypeVar
from uuid import UUID

import chromadb
import networkx as nx
from chromadb.utils import embedding_functions
from pydantic import BaseModel

from palantir.ontology.objects import Delivery, Event, Payment

from .base import OntologyLink, OntologyObject

T = TypeVar("T", bound=OntologyObject)

CHROMA_DATA_PATH = "chroma_data/"
embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)
client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
collection = client.create_collection(name="ontology", embedding_function=embed_fn)


class OntologyRepository:
    """Repository for managing ontology objects and their relationships."""

    def __init__(self):
        """Initialize an empty ontology graph."""
        self.graph = nx.MultiDiGraph()

    def add_object(self, obj: OntologyObject) -> None:
        """Add an object to the ontology graph.

        Args:
            obj: The ontology object to add.
        """
        self.graph.add_node(
            obj.id,
            type=obj.type,
            data=obj.dict(),
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )

    def add_link(self, link: OntologyLink) -> None:
        """Add a relationship between two objects.

        Args:
            link: The relationship to add.
        """
        self.graph.add_edge(
            link.source_id,
            link.target_id,
            key=link.id,
            type=link.relationship_type,
            data=link.dict(),
            created_at=link.created_at,
        )

    def get_object(self, obj_id: UUID, model_cls: Type[T]) -> Optional[T]:
        """Get an object by its ID.

        Args:
            obj_id: The ID of the object to retrieve.
            model_cls: The Pydantic model class to deserialize to.

        Returns:
            The object if found, None otherwise.
        """
        if not self.graph.has_node(obj_id):
            return None

        node_data = self.graph.nodes[obj_id]["data"]
        return model_cls(**node_data)

    def get_linked_objects(
        self,
        obj_id: UUID,
        relationship_type: Optional[str] = None,
        direction: str = "out",
    ) -> List[Dict[str, Any]]:
        """Get objects linked to the given object.

        Args:
            obj_id: The ID of the object to get links for.
            relationship_type: Optional filter for relationship type.
            direction: 'out' for outgoing links, 'in' for incoming links.

        Returns:
            List of linked objects with their relationship data.
        """
        if direction == "out":
            edges = self.graph.out_edges(obj_id, data=True, keys=True)
            get_other_node = lambda e: e[1]  # target node
        else:
            edges = self.graph.in_edges(obj_id, data=True, keys=True)
            get_other_node = lambda e: e[0]  # source node

        results = []
        for edge in edges:
            edge_data = edge[3]  # edge data dictionary
            if relationship_type and edge_data["type"] != relationship_type:
                continue

            other_node = get_other_node(edge)
            node_data = self.graph.nodes[other_node]["data"]

            results.append({"object": node_data, "relationship": edge_data})

        return results

    def update_object(self, obj: OntologyObject) -> None:
        """Update an existing object.

        Args:
            obj: The object with updated data.
        """
        if not self.graph.has_node(obj.id):
            raise ValueError(f"Object with ID {obj.id} not found")

        self.graph.nodes[obj.id].update(
            {"data": obj.dict(), "updated_at": obj.updated_at}
        )

    def delete_object(self, obj_id: UUID) -> None:
        """Delete an object and all its relationships.

        Args:
            obj_id: The ID of the object to delete.
        """
        if not self.graph.has_node(obj_id):
            raise ValueError(f"Object with ID {obj_id} not found")

        self.graph.remove_node(obj_id)

    def search_objects(
        self,
        obj_type: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for objects matching the given criteria.

        Args:
            obj_type: Optional filter for object type.
            properties: Optional dictionary of property values to match.

        Returns:
            List of matching objects.
        """
        results = []

        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]["data"]

            if obj_type and node_data["type"] != obj_type:
                continue

            if properties:
                match = True
                for key, value in properties.items():
                    if key not in node_data or node_data[key] != value:
                        match = False
                        break
                if not match:
                    continue

            results.append(node_data)

        return results


# 온톨로지 노드 임베딩 및 저장
def embedding_node(node):
    doc = node.description if hasattr(node, "description") else str(node)
    collection.add(
        documents=[doc],
        metadatas=[{"name": getattr(node, "id", None), "type": type(node).__name__}],
        ids=[getattr(node, "id", None)],
    )


# 유사 노드 검색
def query_similar_nodes(query_text, n_results=5):
    results = collection.query(query_texts=[query_text], n_results=n_results)
    return results


# 관계 확장(직접 연결된 노드 ID 반환)
def expand_related_nodes(node, ontology_nodes: dict):
    related = []
    if hasattr(node, "related_ids"):
        for rid in getattr(node, "related_ids", []):
            if rid in ontology_nodes:
                related.append(ontology_nodes[rid])
    return related
