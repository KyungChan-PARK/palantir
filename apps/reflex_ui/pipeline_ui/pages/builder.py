import reflex as rx
from typing import List, Dict
import httpx
from ..components.react_flow_wrapper import ReactFlowWrapper

class PipelineBuilderState(rx.State):
    nodes: List[Dict] = [
        {"id": "1", "position": {"x": 100, "y": 100}, "data": {"label": "Input"}},
    ]
    edges: List[Dict] = []
    available_nodes: List[Dict] = []

    async def fetch_available_nodes(self):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get("http://localhost:8000/registry/components")
                if resp.status_code == 200:
                    self.available_nodes = resp.json()
                else:
                    self.available_nodes = []
        except Exception:
            self.available_nodes = []

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
    # 팔레트 노드 동적 로딩
    rx.run(PipelineBuilderState.fetch_available_nodes())
    return rx.container(
        rx.hstack(
            rx.vstack(
                rx.heading("Processors"),
                *[
                    rx.button(
                        node["name"],
                        width="100%",
                        key=node["id"]
                    ) for node in PipelineBuilderState.available_nodes
                ],
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