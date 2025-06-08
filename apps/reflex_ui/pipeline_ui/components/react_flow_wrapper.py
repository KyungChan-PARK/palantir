import reflex as rx
from typing import List, Dict, Any

class ReactFlowWrapper(rx.Component):
    """Reflex custom component wrapping react-flow."""

    library = "reactflow"
    tag = "ReactFlow"

    # props
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]

    on_nodes_change: rx.EventHandler[None]  # callback returns new nodes
    on_edges_change: rx.EventHandler[None]

    # allow arbitrary style prop
    style: Dict[str, Any] | None = None 