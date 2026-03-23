import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """Raised when the LLM service fails during critical email parsing."""


def _get_agent(output_type, system_prompt: str, temperature: float = 0.0):
    """Factory that creates a pydantic-ai Agent with the given output schema."""
    from pydantic_ai import Agent
    from pydantic_ai.models.openai import OpenAIModel

    model = OpenAIModel(
        os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
        api_key=os.getenv('OPENAI_API_KEY', ''),
    )
    return Agent(
        model=model,
        result_type=output_type,
        system_prompt=system_prompt,
        model_settings={'temperature': temperature},
    )


async def parse_email(subject: str, body: str) -> dict:
    """Parse a bank email and extract transaction fields."""
    from .schemas import ParsedEmail
    from .document_utils import load_prompt

    system_prompt = load_prompt('parse_system.txt')
    user_prompt_template = load_prompt('parse_user.txt')
    user_prompt = user_prompt_template.format(subject=subject, body=body[:3000])

    agent = _get_agent(ParsedEmail, system_prompt, temperature=0.0)
    try:
        result = await agent.run(user_prompt)
        return result.data.model_dump()
    except Exception as e:
        logger.error('Error parsing email: %s', e)
        raise LLMServiceError(str(e)) from e


def get_few_shot_examples(user_id: int, max_total: int = 5, max_per_category: int = 2) -> list[dict]:
    """Get few-shot examples from user's past categorized transactions."""
    from apps.transactions.models import Transaction

    txs = (
        Transaction.objects
        .filter(user_id=user_id, description__isnull=False, category_name__isnull=False)
        .exclude(description='')
        .exclude(category_name='')
        .order_by('-updated_at')
        [:50]  # fetch more, cap in Python
    )

    examples = []
    per_cat: dict[str, int] = {}
    for tx in txs:
        cat = tx.category_name
        count = per_cat.get(cat, 0)
        if count >= max_per_category:
            continue
        per_cat[cat] = count + 1
        examples.append({
            'description': tx.description,
            'merchant': tx.merchant,
            'category_name': cat,
        })
        if len(examples) >= max_total:
            break
    return examples


async def categorize(description: str, merchant: Optional[str] = None, user_id: Optional[int] = None) -> str:
    """Categorize a transaction using LLM with optional few-shot examples."""
    from .schemas import CategorizeOutput
    from .document_utils import load_prompt
    from asgiref.sync import sync_to_async

    system_prompt = load_prompt('categorize_system.txt')

    # Build few-shot block (use sync_to_async since ORM is synchronous)
    few_shot_block = ''
    if user_id:
        examples = await sync_to_async(get_few_shot_examples)(user_id)
        if examples:
            lines = []
            for ex in examples:
                lines.append(
                    f"Descripcion: {ex['description']} | Comercio: {ex['merchant'] or 'N/A'} -> {ex['category_name']}"
                )
            few_shot_block = '\n\nEjemplos previos:\n' + '\n'.join(lines)

    user_prompt_template = load_prompt('categorize_user.txt')
    base = description or ''
    if merchant:
        base += f' | comercio: {merchant}'
    user_prompt = user_prompt_template.format(input=base[:500]) + few_shot_block

    agent = _get_agent(CategorizeOutput, system_prompt, temperature=0.0)
    try:
        result = await agent.run(user_prompt)
        return result.data.categoria.strip().lower()[:50]
    except Exception as e:
        logger.error('Error categorizing transaction: %s', e)
        return 'otros'
