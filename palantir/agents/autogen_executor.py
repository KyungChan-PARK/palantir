import json
from typing import Dict, Any, List, Optional
import autogen
from autogen.agentchat import Agent, GroupChat, GroupChatManager

class AutoGenExecutor:
    def __init__(self, config_path: str):
        """
        AutoGen 실행기 초기화
        
        Args:
            config_path: 설정 파일 경로
        """
        with open(config_path, 'r') as f:
            self.config = json.load(f)
            
        self.agents: Dict[str, Agent] = {}
        self.group_chat: Optional[GroupChat] = None
        self.manager: Optional[GroupChatManager] = None
        
        self._initialize_agents()
        
    def _initialize_agents(self):
        """에이전트 초기화"""
        # 기본 에이전트 설정
        self.agents["planner"] = autogen.AssistantAgent(
            name="planner",
            system_message="당신은 작업을 계획하고 조율하는 플래너입니다.",
            llm_config=self.config.get("planner_config", {})
        )
        
        self.agents["builder"] = autogen.AssistantAgent(
            name="builder",
            system_message="당신은 코드를 작성하고 실행하는 빌더입니다.",
            llm_config=self.config.get("builder_config", {})
        )
        
        self.agents["reviewer"] = autogen.AssistantAgent(
            name="reviewer",
            system_message="당신은 코드를 검토하고 개선사항을 제안하는 리뷰어입니다.",
            llm_config=self.config.get("reviewer_config", {})
        )
        
        # 사용자 프록시 에이전트
        self.agents["user_proxy"] = autogen.UserProxyAgent(
            name="user_proxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            code_execution_config=self.config.get("code_execution_config", {})
        )
        
        # 그룹 채팅 설정
        self.group_chat = GroupChat(
            agents=list(self.agents.values()),
            messages=[],
            max_round=self.config.get("max_round", 10)
        )
        
        # 매니저 설정
        self.manager = GroupChatManager(
            groupchat=self.group_chat,
            llm_config=self.config.get("manager_config", {})
        )
        
    async def execute_task(self, task: str) -> List[Dict[str, Any]]:
        """
        작업 실행
        
        Args:
            task: 실행할 작업 설명
            
        Returns:
            List[Dict[str, Any]]: 대화 기록
        """
        # 초기 메시지 설정
        self.group_chat.messages = [{
            "role": "user",
            "content": task
        }]
        
        # 작업 실행
        await self.manager.run()
        
        return self.group_chat.messages
        
    def get_agent_status(self) -> Dict[str, Any]:
        """
        에이전트 상태 조회
        
        Returns:
            Dict[str, Any]: 에이전트 상태 정보
        """
        return {
            "agents": list(self.agents.keys()),
            "total_messages": len(self.group_chat.messages) if self.group_chat else 0,
            "is_running": bool(self.manager and self.manager.is_running())
        }
        
    def reset(self):
        """대화 기록 초기화"""
        if self.group_chat:
            self.group_chat.messages = [] 