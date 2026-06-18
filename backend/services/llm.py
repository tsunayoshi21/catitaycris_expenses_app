import os
import logging
import time
from typing import Literal, Optional

from asgiref.sync import sync_to_async
from pydantic import create_model
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

from apps.transactions.models import Transaction
from .document_utils import load_prompt
from .schemas import ParsedEmail

logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """Raised when the LLM service fails during critical email parsing."""


def _get_agent(output_type, system_prompt: str, temperature: float = 0.0):
    """Factory that creates a pydantic-ai Agent with the given output schema."""
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
    system_prompt = load_prompt('parse_system.txt')
    user_prompt_template = load_prompt('parse_user.txt')
    user_prompt = user_prompt_template.format(subject=subject, body=body[:3000])

    agent = _get_agent(ParsedEmail, system_prompt, temperature=0.0)
    logger.info('LLM parse_email iniciado (subject=%s)', subject[:80])
    t0 = time.monotonic()
    try:
        result = await agent.run(user_prompt)
        logger.info('LLM parse_email completado en %.2fs', time.monotonic() - t0)
        return result.data.model_dump()
    except Exception as e:
        logger.error('LLM parse_email fallo en %.2fs: %s', time.monotonic() - t0, e)
        raise LLMServiceError(str(e)) from e


def get_few_shot_examples(user_id: int, valid_categories: list[str], max_total: int = 5, max_per_category: int = 2) -> list[dict]:
    """Get few-shot examples from user's past categorized transactions."""
    txs = (
        Transaction.objects
        .filter(user_id=user_id, description__isnull=False, category_name__in=valid_categories)
        .exclude(description='')
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


def _make_categorize_schema(valid_categories: list[str]):
    """Create a dynamic Pydantic model with a Literal enum for valid categories."""
    CatLiteral = Literal[tuple(valid_categories)]
    return create_model('CategorizeOutput', categoria=(CatLiteral, ...))


async def categorize(description: str, merchant: Optional[str] = None,
                     user_id: Optional[int] = None, valid_categories: Optional[list[str]] = None) -> str:
    """Categorize a transaction using LLM, restricted to valid DB categories."""
    if not valid_categories:
        logger.warning('categorize() llamado sin valid_categories, fallback a "otros"')
        return 'otros'

    categories_str = ', '.join(valid_categories)
    system_prompt = load_prompt('categorize_system.txt').format(valid_categories=categories_str)

    # Build few-shot block (use sync_to_async since ORM is synchronous)
    few_shot_block = ''
    if user_id:
        examples = await sync_to_async(get_few_shot_examples)(user_id, valid_categories)
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

    output_schema = _make_categorize_schema(valid_categories)
    agent = _get_agent(output_schema, system_prompt, temperature=0.0)
    logger.info('LLM categorize iniciado (input=%s)', base[:80])
    t0 = time.monotonic()
    try:
        result = await agent.run(user_prompt)
        category = result.data.categoria.strip().lower()[:50]
        # Safety net: validate against valid categories
        if category not in valid_categories:
            logger.warning('LLM devolvio categoria invalida "%s", fallback a "otros"', category)
            category = 'otros'
        logger.info('LLM categorize completado en %.2fs', time.monotonic() - t0)
        return category
    except Exception as e:
        logger.error('LLM categorize fallo en %.2fs: %s', time.monotonic() - t0, e)
        return 'otros'
