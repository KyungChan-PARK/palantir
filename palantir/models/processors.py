"""Natural language processors for ontology objects."""

from typing import Any, Dict, List, Optional, Tuple

from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from ..ontology.objects import Customer, Order, Product


class ObjectSummary(BaseModel):
    """Summary of an ontology object."""

    key_points: List[str] = Field(..., description="Key points about the object")
    insights: List[str] = Field(
        ..., description="Insights derived from the object data"
    )
    suggestions: List[str] = Field(
        ..., description="Suggestions for actions or improvements"
    )


class RelationshipInsight(BaseModel):
    """Insight about relationships between objects."""

    description: str = Field(..., description="Description of the relationship pattern")
    significance: str = Field(..., description="Business significance of the pattern")
    recommendations: List[str] = Field(
        ..., description="Recommendations based on the insight"
    )


class ObjectProcessor:
    """Processes ontology objects using natural language."""

    def __init__(
        self, model_name: str = "gpt-4-turbo-preview", temperature: float = 0.3
    ):
        """Initialize the object processor.

        Args:
            model_name: The OpenAI model to use.
            temperature: Sampling temperature for generation.
        """
        self.model = ChatOpenAI(model_name=model_name, temperature=temperature)

        # Initialize output parsers
        self.summary_parser = PydanticOutputParser(pydantic_object=ObjectSummary)
        self.insight_parser = PydanticOutputParser(pydantic_object=RelationshipInsight)

    def _create_object_prompt(self, obj_type: str) -> str:
        """Create a prompt template for object analysis.

        Args:
            obj_type: Type of the object (Customer, Order, Product).

        Returns:
            Prompt template string.
        """
        prompts = {
            "Customer": """Analyze this customer's data and provide:
                1. Key points about their profile and behavior
                2. Insights about their value and preferences
                3. Suggestions for engagement and retention""",
            "Order": """Analyze this order data and provide:
                1. Key points about the order details and status
                2. Insights about purchase patterns and value
                3. Suggestions for order processing and customer service""",
            "Product": """Analyze this product data and provide:
                1. Key points about product characteristics
                2. Insights about performance and positioning
                3. Suggestions for inventory and marketing""",
        }
        return prompts.get(
            obj_type,
            "Analyze this object and provide key points, insights, and suggestions.",
        )

    async def analyze_object(self, obj: Dict[str, Any], obj_type: str) -> ObjectSummary:
        """Analyze a single ontology object.

        Args:
            obj: The object data dictionary.
            obj_type: Type of the object.

        Returns:
            ObjectSummary containing analysis results.
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self._create_object_prompt(obj_type)),
                ("human", "Object data: {data}\n\n{format_instructions}"),
            ]
        )

        chain = prompt | self.model | self.summary_parser

        result = await chain.ainvoke(
            {
                "data": str(obj),
                "format_instructions": self.summary_parser.get_format_instructions(),
            }
        )

        return result

    async def analyze_relationship(
        self, source: Dict[str, Any], target: Dict[str, Any], relationship_type: str
    ) -> RelationshipInsight:
        """Analyze a relationship between two objects.

        Args:
            source: Source object data.
            target: Target object data.
            relationship_type: Type of relationship.

        Returns:
            RelationshipInsight containing analysis results.
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """Analyze the relationship between these objects and provide:
                1. A clear description of the relationship pattern
                2. The business significance of this relationship
                3. Recommendations based on this relationship""",
                ),
                (
                    "human",
                    """Source object: {source}
                Target object: {target}
                Relationship type: {relationship}
                
                {format_instructions}""",
                ),
            ]
        )

        chain = prompt | self.model | self.insight_parser

        result = await chain.ainvoke(
            {
                "source": str(source),
                "target": str(target),
                "relationship": relationship_type,
                "format_instructions": self.insight_parser.get_format_instructions(),
            }
        )

        return result


class DataEnricher:
    """Enriches ontology objects with AI-generated content."""

    def __init__(
        self, model_name: str = "gpt-4-turbo-preview", temperature: float = 0.4
    ):
        """Initialize the data enricher.

        Args:
            model_name: The OpenAI model to use.
            temperature: Sampling temperature for generation.
        """
        self.model = ChatOpenAI(model_name=model_name, temperature=temperature)

    async def generate_description(self, obj: Dict[str, Any], obj_type: str) -> str:
        """Generate a natural language description of an object.

        Args:
            obj: The object data dictionary.
            obj_type: Type of the object.

        Returns:
            Generated description string.
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Generate a clear, concise description of this object in natural language.",
                ),
                ("human", "Object type: {type}\nObject data: {data}"),
            ]
        )

        chain = prompt | self.model

        result = await chain.ainvoke({"type": obj_type, "data": str(obj)})

        return result.content

    async def suggest_tags(self, obj: Dict[str, Any], obj_type: str) -> List[str]:
        """Suggest relevant tags for an object.

        Args:
            obj: The object data dictionary.
            obj_type: Type of the object.

        Returns:
            List of suggested tags.
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """Suggest 3-5 relevant tags for this object.
                Tags should be single words or short phrases that help categorize and find the object.
                Return the tags as a comma-separated list.""",
                ),
                ("human", "Object type: {type}\nObject data: {data}"),
            ]
        )

        chain = prompt | self.model

        result = await chain.ainvoke({"type": obj_type, "data": str(obj)})

        return [tag.strip() for tag in result.content.split(",")]
