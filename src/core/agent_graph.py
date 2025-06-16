from typing import Any

from langchain.agents import Tool
from langgraph.graph import END, StateGraph

from src.agents.base_agent import AgentConfig
from src.agents.developer_agent import DeveloperAgent
# 기존 에이전트 import (실제 구현 연결 필요)
from src.agents.planner_agent import PlannerAgent
from src.agents.reviewer_agent import ReviewerAgent
from src.agents.self_improvement_agent import SelfImprovementAgent

# MCP 연동 예시 (실제 구현 시 사용)
# from src.core.mcp import MCP, MCPConfig

# 에이전트 인스턴스 생성 (실제 config는 외부에서 주입)
planner = PlannerAgent(
    AgentConfig(
        name="Planner",
        description="Task Planner",
        model="gpt-4",
        system_prompt="계획 수립",
    )
)
developer = DeveloperAgent(
    AgentConfig(
        name="Developer",
        description="코드 생성",
        model="gpt-4",
        system_prompt="코드 생성",
    )
)
reviewer = ReviewerAgent(
    AgentConfig(
        name="Reviewer",
        description="코드 검토",
        model="gpt-4",
        system_prompt="코드 검토",
    )
)
selfimprover = SelfImprovementAgent(
    AgentConfig(
        name="SelfImprover",
        description="자가 개선",
        model="gpt-4",
        system_prompt="자가 개선",
    )
)


# 각 에이전트의 process 메서드를 Tool로 래핑
def planner_func(input_data: Any):
    return planner.process(input_data)


def developer_func(input_data: Any):
    return developer.process(input_data)


def reviewer_func(input_data: Any):
    return reviewer.process(input_data)


def selfimprove_func(input_data: Any):
    return selfimprover.process(input_data)


planner_tool = Tool(
    name="Planner", func=planner_func, description="Task를 분해하고 계획을 수립"
)
developer_tool = Tool(
    name="Developer", func=developer_func, description="코드를 생성/수정"
)
reviewer_tool = Tool(
    name="Reviewer", func=reviewer_func, description="코드/결과를 검토"
)
selfimprove_tool = Tool(
    name="SelfImprover", func=selfimprove_func, description="코드베이스 자가 개선"
)

graph = StateGraph()
graph.add_node("plan", planner_tool)
graph.add_node("develop", developer_tool)
graph.add_node("review", reviewer_tool)
graph.add_node("selfimprove", selfimprove_tool)
graph.add_edge("plan", "develop")
graph.add_edge("develop", "review")
graph.add_edge("review", "selfimprove")
graph.add_edge("selfimprove", END)

agent_executor = graph.compile()


def run_multiagent_executor(user_input):
    """최신 멀티에이전트 오케스트레이션 실행 샘플"""
    result = agent_executor.invoke({"input": user_input})
    return result
