
def load_prompt(path: str) -> str:
    """
    Load a prompt from a text file
    """
    with open("app/prompts/"+path, "r", encoding="utf-8") as f:
        return f.read()