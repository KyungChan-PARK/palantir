"""LLM integration using LangChain."""

from typing import Any, Dict, List, Optional

from langchain.chains import ConversationChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
)
from langchain.schema import SystemMessage
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Represents a chat message."""

    role: str = Field(
        ..., description="Role of the message sender (system/user/assistant)"
    )
    content: str = Field(..., description="Content of the message")


class OntologyAssistant:
    """AI assistant for interacting with the ontology system."""

    def __init__(
        self,
        model_name: str = "gpt-4-turbo-preview",
        temperature: float = 0.7,
        system_message: Optional[str] = None,
    ):
        """Initialize the ontology assistant.

        Args:
            model_name: The OpenAI model to use.
            temperature: Sampling temperature for generation.
            system_message: Optional custom system message.
        """
        self.model = ChatOpenAI(model_name=model_name, temperature=temperature)

        # Default system message if none provided
        if not system_message:
            system_message = """You are an AI assistant helping users interact with an ontology-based data system.
            You can help users understand relationships between different business objects,
            analyze data patterns, and provide insights based on the available information.
            Always strive to give clear, concise answers and ask for clarification when needed."""

        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(system_message),
                MessagesPlaceholder(variable_name="history"),
                HumanMessagePromptTemplate.from_template("{input}"),
            ]
        )

        # Initialize conversation memory
        self.memory = ConversationBufferMemory(
            return_messages=True, memory_key="history"
        )

        # Create conversation chain
        self.chain = ConversationChain(
            memory=self.memory, prompt=self.prompt, llm=self.model
        )

    async def process_message(self, message: str) -> str:
        """Process a user message and generate a response.

        Args:
            message: The user's input message.

        Returns:
            The assistant's response.
        """
        response = await self.chain.arun(input=message)
        return response

    def get_conversation_history(self) -> List[ChatMessage]:
        """Get the conversation history.

        Returns:
            List of ChatMessage objects representing the conversation.
        """
        messages = []
        for msg in self.memory.chat_memory.messages:
            role = "system" if isinstance(msg, SystemMessage) else msg.type
            messages.append(ChatMessage(role=role, content=msg.content))
        return messages

    def clear_memory(self) -> None:
        """Clear the conversation memory."""
        self.memory.clear()


class QueryGenerator:
    """Generates structured queries from natural language using LLM."""

    def __init__(
        self, model_name: str = "gpt-4-turbo-preview", temperature: float = 0.2
    ):
        """Initialize the query generator.

        Args:
            model_name: The OpenAI model to use.
            temperature: Sampling temperature for generation.
        """
        self.model = ChatOpenAI(model_name=model_name, temperature=temperature)

        self.system_prompt = """You are a helpful assistant that converts natural language queries
        into structured search parameters for an ontology system. The system supports searching
        by object type (Customer, Order, Product) and their properties.
        
        Convert the user's query into a JSON object with:
        - obj_type: The main object type to search for
        - properties: Key-value pairs of properties to match
        
        Example:
        User: "Find all orders with total amount over $100"
        Response: {"obj_type": "Order", "properties": {"total_amount": {"$gt": 100}}}"""

        self.prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(self.system_prompt),
                HumanMessagePromptTemplate.from_template("{query}"),
            ]
        )

    async def generate_query(self, natural_query: str) -> Dict[str, Any]:
        """Generate structured query from natural language.

        Args:
            natural_query: The natural language query.

        Returns:
            Dictionary containing the structured query parameters.
        """
        chain = self.prompt | self.model
        response = await chain.ainvoke({"query": natural_query})

        # Extract JSON from the response
        import json

        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {"obj_type": None, "properties": {}}
