from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent.parent / 'prompts'


def load_prompt(filename: str) -> str:
    """Load a prompt text file from the prompts directory."""
    path = PROMPTS_DIR / filename
    return path.read_text(encoding='utf-8')
