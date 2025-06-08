import reflex as rx
from typing import List, Dict

from ..components.react_flow_wrapper import ReactFlowWrapper

class PipelineBuilderState(rx.State):
    nodes: List[Dict] = [
        {"id": "1", "position": {"x": 100, "y": 100}, "data": {"label": "Input"}},
    ]
    edges: List[Dict] = []

    def handle_nodes_change(self, new_nodes: List[Dict]):
        self.nodes = new_nodes

    def handle_edges_change(self, new_edges: List[Dict]):
        self.edges = new_edges

    async def save_pipeline(self):
        data = {"nodes": self.nodes, "edges": self.edges}
        await rx.call_api("/pipeline/visual", method="POST", json=data)
        rx.toast("Pipeline saved!")

@rx.page(route="/builder", title="Pipeline Builder")
def builder_page():
    return rx.container(
        rx.hstack(
            rx.vstack(
                rx.heading("Processors"),
                rx.button("Load Data", width="100%"),
                rx.button("Clean Text", width="100%"),
                spacing="4",
            ),
            ReactFlowWrapper(
                nodes=PipelineBuilderState.nodes,
                edges=PipelineBuilderState.edges,
                on_nodes_change=PipelineBuilderState.handle_nodes_change,
                on_edges_change=PipelineBuilderState.handle_edges_change,
                style={"height": "80vh", "border": "1px solid #ddd", "flex": 1},
            ),
            spacing="8",
        ),
        rx.button("Save Pipeline", on_click=PipelineBuilderState.save_pipeline),
    ) 