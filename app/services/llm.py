import os
import json
import requests
import logging
from .document_utils import load_prompt

# Logger para este módulo
logger = logging.getLogger(__name__)

SYSTEM_PARSE = load_prompt("parse_prompt.txt")
SYSTEM_CATEGORIZE = load_prompt("categorize_prompt.txt")
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def _api_base() -> str:
    return os.getenv('OPENAI_BASE_URL', 'https://api.openai.com')

def _api_key() -> str | None:
    return os.getenv('OPENAI_API_KEY')

def _chat_completions(payload: dict) -> dict | None:
    key = _api_key()
    if not key:
        return None
    url = f"{_api_base().rstrip('/')}/v1/chat/completions"
    headers = {
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
    }
    try:
        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        if resp.status_code >= 400:
            return None
        return resp.json()
    except Exception:
        return None

def parse_email(subject: str, body: str) -> dict:
    prompt = f"Asunto: {subject}\n\nCuerpo:\n{body}"
    payload = {
        'model': os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
        'messages': [
            {"role": "system", "content": SYSTEM_PARSE},
            {"role": "user", "content": prompt},
        ],
        'temperature': 0.0,
        'response_format': {"type": "json_object"},
    }
    data = _chat_completions(payload)
    if not data:
        return {}
    try:
        content = data['choices'][0]['message']['content']
        return json.loads(content)
    except Exception:
        return {}

def categorize(description: str, merchant: str | None = None) -> str:
    base = description or ''
    if merchant:
        base += f" | comercio: {merchant}"
    payload = {
        'model': os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
        'messages': [
            {"role": "system", "content": SYSTEM_CATEGORIZE},
            {"role": "user", "content": base[:500]},
        ],
        'temperature': 0.0,
    }
    data = _chat_completions(payload)
    if not data:
        return 'otros'
    try:
        content = data['choices'][0]['message']['content'].strip().lower()
        return content.split('\n')[0][:50]
    except Exception:
        return 'otros'
