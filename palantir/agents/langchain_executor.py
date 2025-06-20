from typing import Dict, Any, List
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.messages import SystemMessage, HumanMessage
from langchain.tools import Tool
from langchain_openai import ChatOpenAI

class LangChainExecutor:
    def __init__(self, openai_api_key: str, model: str = "gpt-3.5-turbo"):
        """
        LangChain 에이전트 실행기 초기화
        
        Args:
            openai_api_key: OpenAI API 키
            model: 사용할 모델 이름
        """
        self.llm = ChatOpenAI(
            openai_api_key=openai_api_key,
            model=model,
            temperature=0
        )
        self.tools: List[Tool] = []
        self.agent_executor = None
        
    def add_tool(self, name: str, func: callable, description: str):
        """
        도구 추가
        
        Args:
            name: 도구 이름
            func: 도구 함수
            description: 도구 설명
        """
        tool = Tool(
            name=name,
            func=func,
            description=description
        )
        self.tools.append(tool)
        
    def create_agent(self, system_message: str):
        """
        에이전트 생성
        
        Args:
            system_message: 시스템 메시지
        """
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessage(content="{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True
        )
        
    async def execute(self, input_text: str, chat_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        에이전트 실행
        
        Args:
            input_text: 입력 텍스트
            chat_history: 대화 기록
            
        Returns:
            Dict[str, Any]: 실행 결과
        """
        if not self.agent_executor:
            raise RuntimeError("에이전트가 생성되지 않았습니다. create_agent()를 먼저 호출하세요.")
            
        chat_history = chat_history or []
        
        return await self.agent_executor.ainvoke({
            "input": input_text,
            "chat_history": chat_history
        })
        
    def get_tool_descriptions(self) -> List[Dict[str, str]]:
        """
        등록된 도구 목록 조회
        
        Returns:
            List[Dict[str, str]]: 도구 정보 목록
        """
        return [{
            "name": tool.name,
            "description": tool.description
        } for tool in self.tools] 