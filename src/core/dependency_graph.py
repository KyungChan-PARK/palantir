"""에이전트 의존성 그래프 관리"""

import networkx as nx
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AgentNode:
    """에이전트 노드 정보"""
    agent_id: str
    name: str
    role: str
    status: str
    dependencies: Set[str]
    dependents: Set[str]
    last_active: datetime
    metadata: Dict[str, str]


class DependencyGraph:
    """에이전트 의존성 그래프 관리자"""

    def __init__(self):
        """그래프 초기화"""
        self.graph = nx.DiGraph()
        self.nodes: Dict[str, AgentNode] = {}

    def add_agent(
        self,
        agent_id: str,
        name: str,
        role: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> None:
        """에이전트 노드 추가
        
        Args:
            agent_id: 에이전트 ID
            name: 에이전트 이름
            role: 에이전트 역할
            metadata: 추가 메타데이터
        """
        node = AgentNode(
            agent_id=agent_id,
            name=name,
            role=role,
            status="initialized",
            dependencies=set(),
            dependents=set(),
            last_active=datetime.now(),
            metadata=metadata or {}
        )
        self.nodes[agent_id] = node
        self.graph.add_node(agent_id, **node.__dict__)

    def add_dependency(
        self,
        source_id: str,
        target_id: str,
        dependency_type: str = "default"
    ) -> None:
        """의존성 관계 추가
        
        Args:
            source_id: 의존하는 에이전트 ID
            target_id: 의존 대상 에이전트 ID
            dependency_type: 의존성 유형
        """
        if source_id not in self.nodes or target_id not in self.nodes:
            raise ValueError("Agent not found")

        self.graph.add_edge(source_id, target_id, type=dependency_type)
        self.nodes[source_id].dependencies.add(target_id)
        self.nodes[target_id].dependents.add(source_id)

    def remove_dependency(self, source_id: str, target_id: str) -> None:
        """의존성 관계 제거"""
        if source_id not in self.nodes or target_id not in self.nodes:
            raise ValueError("Agent not found")

        if self.graph.has_edge(source_id, target_id):
            self.graph.remove_edge(source_id, target_id)
            self.nodes[source_id].dependencies.remove(target_id)
            self.nodes[target_id].dependents.remove(source_id)

    def update_agent_status(
        self,
        agent_id: str,
        status: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> None:
        """에이전트 상태 업데이트"""
        if agent_id not in self.nodes:
            raise ValueError("Agent not found")

        node = self.nodes[agent_id]
        node.status = status
        node.last_active = datetime.now()
        if metadata:
            node.metadata.update(metadata)

        self.graph.nodes[agent_id].update(node.__dict__)

    def get_dependencies(self, agent_id: str) -> Set[str]:
        """에이전트의 의존성 목록 조회"""
        if agent_id not in self.nodes:
            raise ValueError("Agent not found")
        return self.nodes[agent_id].dependencies

    def get_dependents(self, agent_id: str) -> Set[str]:
        """에이전트에 의존하는 에이전트 목록 조회"""
        if agent_id not in self.nodes:
            raise ValueError("Agent not found")
        return self.nodes[agent_id].dependents

    def get_execution_order(self) -> List[str]:
        """의존성을 고려한 실행 순서 계산"""
        try:
            return list(nx.topological_sort(self.graph))
        except nx.NetworkXUnfeasible:
            raise ValueError("Circular dependency detected")

    def get_critical_path(self) -> List[str]:
        """크리티컬 패스 계산"""
        if not self.graph.nodes:
            return []

        # 각 노드의 처리 시간을 1로 가정
        lengths = {edge: 1 for edge in self.graph.edges()}
        for node in self.graph.nodes():
            self.graph.nodes[node]["weight"] = 1

        # 시작 노드(진입 차수가 0인 노드들)
        start_nodes = [n for n in self.graph.nodes() if self.graph.in_degree(n) == 0]
        
        # 종료 노드(진출 차수가 0인 노드들)
        end_nodes = [n for n in self.graph.nodes() if self.graph.out_degree(n) == 0]

        if not start_nodes or not end_nodes:
            return []

        # 가장 긴 경로 계산
        critical_path = None
        max_length = -1

        for start in start_nodes:
            for end in end_nodes:
                try:
                    paths = list(nx.all_simple_paths(self.graph, start, end))
                    for path in paths:
                        length = sum(self.graph.nodes[node]["weight"] for node in path)
                        if length > max_length:
                            max_length = length
                            critical_path = path
                except nx.NetworkXNoPath:
                    continue

        return list(critical_path) if critical_path else []

    def get_bottlenecks(self) -> List[str]:
        """병목 지점 식별"""
        if not self.graph.nodes:
            return []

        # 중심성 계산
        betweenness = nx.betweenness_centrality(self.graph)
        in_degree = self.graph.in_degree()
        out_degree = self.graph.out_degree()

        # 병목 지점 기준:
        # 1. 높은 중심성
        # 2. 높은 진입/진출 차수
        bottlenecks = []
        for node in self.graph.nodes():
            if (
                betweenness[node] > 0.5 or  # 높은 중심성
                in_degree[node] > 2 or      # 많은 의존성
                out_degree[node] > 2        # 많은 의존 대상
            ):
                bottlenecks.append(node)

        return bottlenecks

    def get_independent_subgraphs(self) -> List[Set[str]]:
        """독립적으로 실행 가능한 서브그래프 식별"""
        return list(nx.connected_components(self.graph.to_undirected()))

    def validate_dependencies(self) -> List[Tuple[str, str]]:
        """의존성 관계 유효성 검증"""
        issues = []

        # 순환 의존성 검사
        try:
            nx.find_cycle(self.graph)
            issues.append(("error", "Circular dependency detected"))
        except nx.NetworkXNoCycle:
            pass

        # 고립된 노드 검사
        isolated = list(nx.isolates(self.graph))
        if isolated:
            issues.append(("warning", f"Isolated agents found: {isolated}"))

        # 단절점 검사
        if len(self.graph.nodes) > 2:
            cut_vertices = list(nx.articulation_points(self.graph.to_undirected()))
            if cut_vertices:
                issues.append(("warning", f"Critical agents (cut vertices) found: {cut_vertices}"))

        return issues

    def to_dot(self) -> str:
        """DOT 형식으로 그래프 출력"""
        return nx.drawing.nx_pydot.to_pydot(self.graph).to_string() 