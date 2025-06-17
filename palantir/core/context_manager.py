"""context_manager.py
- 멀티에이전트 계층형 컨텍스트/메모리 관리 모듈(스텁)
- 각 에이전트별 개별 컨텍스트 + 글로벌(공유) 컨텍스트 계층화
- 태스크/실패/정책/외부지식/온톨로지 등 다양한 컨텍스트 관리
"""

from typing import Any, Dict, Optional


class ContextManager:
    def __init__(self):
        # 에이전트별 개별 컨텍스트
        self.agent_contexts: Dict[str, Dict[str, Any]] = {}
        # 글로벌(공유) 컨텍스트
        self.global_context: Dict[str, Any] = {}
        # 외부지식/온톨로지/문서 등
        self.external_knowledge: Dict[str, Any] = {}

    def get_agent_context(self, agent_name: str) -> Dict[str, Any]:
        return self.agent_contexts.get(agent_name, {})

    def set_agent_context(self, agent_name: str, context: Dict[str, Any]):
        self.agent_contexts[agent_name] = context

    def update_agent_context(self, agent_name: str, key: str, value: Any):
        if agent_name not in self.agent_contexts:
            self.agent_contexts[agent_name] = {}
        self.agent_contexts[agent_name][key] = value

    def get_global_context(self) -> Dict[str, Any]:
        return self.global_context

    def set_global_context(self, context: Dict[str, Any]):
        self.global_context = context

    def update_global_context(self, key: str, value: Any):
        self.global_context[key] = value

    def get_external_knowledge(self, key: str) -> Optional[Any]:
        return self.external_knowledge.get(key)

    def set_external_knowledge(self, key: str, value: Any):
        self.external_knowledge[key] = value

    def merge_contexts(self, agent_name: str) -> Dict[str, Any]:
        """에이전트별 컨텍스트 + 글로벌 컨텍스트 + 외부지식 등 계층적으로 병합
        (실제 병합 정책/우선순위/필터링 등은 후속 구현)
        """
        merged = dict(self.global_context)
        merged.update(self.agent_contexts.get(agent_name, {}))
        # 외부지식 등 추가 병합 가능
        return merged

    # TODO: VectorDB/ChromaDB 등 외부 RAG 연동, 온톨로지/문서 자동 주입 등 확장
