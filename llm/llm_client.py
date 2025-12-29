import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

def query_llm(prompt: str, model: str = "mistral") -> str:
    print(">>> LLM CALL STARTED <<<")

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=90  # IMPORTANT
    )

    print(">>> LLM CALL FINISHED <<<")

    response.raise_for_status()
    return response.json()["response"]
