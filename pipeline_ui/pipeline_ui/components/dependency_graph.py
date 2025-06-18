"""의존성 그래프 시각화 컴포넌트"""

import reflex as rx
import networkx as nx
import plotly.graph_objects as go
from typing import Dict, List, Optional

from ..styles import COLORS


class DependencyGraphState(rx.State):
    """의존성 그래프 상태"""

    agents: Dict[str, Dict] = {}
    dependencies: List[Dict] = []
    selected_agent: Optional[str] = None

    def update_graph(self, agents: Dict[str, Dict], dependencies: List[Dict]):
        """그래프 데이터 업데이트"""
        self.agents = agents
        self.dependencies = dependencies

    def select_agent(self, agent_id: str):
        """에이전트 선택"""
        self.selected_agent = agent_id


def dependency_graph() -> rx.Component:
    """의존성 그래프 컴포넌트"""
    return rx.vstack(
        rx.heading("에이전트 의존성 그래프", size="lg"),
        rx.box(
            rx.plotly(
                data=_create_graph_data(),
                layout=_create_graph_layout(),
                config={"displayModeBar": False},
            ),
            width="100%",
            height="600px",
            border_radius="md",
            border="1px solid",
            border_color=COLORS.border,
        ),
        rx.box(
            rx.cond(
                DependencyGraphState.selected_agent,
                rx.vstack(
                    rx.heading(
                        f"에이전트 정보: {DependencyGraphState.selected_agent}",
                        size="md",
                    ),
                    rx.text(
                        f"상태: {DependencyGraphState.agents[DependencyGraphState.selected_agent]['status']}",
                    ),
                    rx.text(
                        f"마지막 활성: {DependencyGraphState.agents[DependencyGraphState.selected_agent]['last_active']}",
                    ),
                    rx.text(
                        f"의존성: {', '.join(DependencyGraphState.agents[DependencyGraphState.selected_agent]['dependencies'])}",
                    ),
                    rx.text(
                        f"의존 대상: {', '.join(DependencyGraphState.agents[DependencyGraphState.selected_agent]['dependents'])}",
                    ),
                    padding="4",
                    border="1px solid",
                    border_color=COLORS.border,
                    border_radius="md",
                ),
            ),
            width="100%",
            margin_top="4",
        ),
        width="100%",
        align_items="stretch",
        spacing="4",
    )


def _create_graph_data() -> List[go.Scatter]:
    """그래프 데이터 생성"""
    G = nx.DiGraph()

    # 노드 추가
    for agent_id, agent_data in DependencyGraphState.agents.items():
        G.add_node(agent_id, **agent_data)

    # 엣지 추가
    for dep in DependencyGraphState.dependencies:
        G.add_edge(dep["source"], dep["target"])

    # 레이아웃 계산
    pos = nx.spring_layout(G)

    # 노드 데이터
    node_trace = go.Scatter(
        x=[pos[node][0] for node in G.nodes()],
        y=[pos[node][1] for node in G.nodes()],
        mode="markers+text",
        hoverinfo="text",
        text=[node for node in G.nodes()],
        textposition="top center",
        marker=dict(
            size=20,
            color=[
                COLORS.success
                if G.nodes[node]["status"] == "running"
                else COLORS.warning
                if G.nodes[node]["status"] == "waiting"
                else COLORS.error
                for node in G.nodes()
            ],
        ),
    )

    # 엣지 데이터
    edge_trace = go.Scatter(
        x=[],
        y=[],
        line=dict(width=1, color=COLORS.border),
        hoverinfo="none",
        mode="lines",
    )

    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_trace.x += (x0, x1, None)
        edge_trace.y += (y0, y1, None)

    return [edge_trace, node_trace]


def _create_graph_layout() -> Dict:
    """그래프 레이아웃 설정"""
    return {
        "showlegend": False,
        "hovermode": "closest",
        "margin": dict(b=20, l=5, r=5, t=40),
        "xaxis": dict(showgrid=False, zeroline=False, showticklabels=False),
        "yaxis": dict(showgrid=False, zeroline=False, showticklabels=False),
        "plot_bgcolor": "rgba(0,0,0,0)",
        "paper_bgcolor": "rgba(0,0,0,0)",
    } 