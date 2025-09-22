import os
import logging
from typing import Type
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.settings import ModelSettings
from .document_utils import load_prompt
from .schemas import ParsedEmail, CategorizeOutput

logger = logging.getLogger(__name__)

OPENAI_API_KEY    = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL      = os.getenv('OPENAI_MODEL')

def llm_agent(output_schema: Type[BaseModel], system_prompt: str, model: str = OPENAI_MODEL, temp: float = 0.5) -> Agent:
    """
    Create and return a PydanticAI Agent with specified config.
    Current support for OpenAI models only.
    
    Args:
        output_model: The Pydantic schema to structure the output
        system_prompt: The system prompt to guide the model
        model_name: Optional, specific model to use
        temperature: Optional, temperature setting for the model
    
    Returns:
        Agent: A configured PydanticAI Agent
    """
    model_name  = model
    temperature = temp
    model       = OpenAIModel(model_name)
    model_settings: ModelSettings = {"temperature": temperature}
        
    if not OPENAI_API_KEY:
        raise EnvironmentError(
            "OPENAI_API_KEY environment variable is required, but not set."
        )

    model = OpenAIModel(model_name)
    model_settings = {"temperature": temperature}

    agent = Agent(
        model=model,
        output_type=output_schema,
        system_prompt=system_prompt,
        model_settings=model_settings,
        retries=0
    )
    
    return agent

async def parse_email(subject: str, body: str) -> dict:
    """
    Parse email content to extract transaction details using LLM
    """
    system_prompt = load_prompt("parse_system_prompt.txt")
    user_prompt = load_prompt("parse_user_prompt.txt").format(asunto=subject, cuerpo=body)
    
    agent = llm_agent(ParsedEmail, system_prompt)
    
    try:
        result = await agent.run(user_prompt)
        return result.output.dict() if result and result.output else {}
    
    except Exception as e:
        logger.error(f"Error en parse_email(): {e}")
        return {}

async def categorize(description: str, merchant: str | None = None) -> str:
    """
    Categorize an expense based on its description and merchant information
    """
    system_prompt = load_prompt("categorize_system_prompt.txt")
    user_prompt = load_prompt("categorize_user_prompt.txt").format(descripcion=description, merchant=merchant or '')

    agent = llm_agent(CategorizeOutput, system_prompt)

    try:
        result = await agent.run(user_prompt)
        return result.output.categoria.strip().lower() if result and result.output and result.output.categoria else 'otros'
    except Exception as e:
        logger.error(f"Error en categorize(): {e}")
        return 'otros'
