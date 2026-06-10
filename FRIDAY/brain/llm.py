import ollama

MODEL = "llama3.1:8b"


def get_ollama_client():
    """Try to connect to Ollama, check both ports."""
    try:
        client = ollama.Client()
        client.list()
        return client
    except:
        try:
            client = ollama.Client(host='http://localhost:11435')
            client.list()
            return client
        except:
            return None


def ask_llm(prompt: str, context: str = "") -> str:
    client = get_ollama_client()
    if client is None:
        return "Brain error, Boss: Ollama is not running. Start it with 'ollama serve'."

    try:
        system_content = """You are F.R.I.D.A.Y., an AI assistant. 
You are witty, efficient, slightly sarcastic but deeply loyal. 
You refer to the user as 'Boss'. 
Keep responses SHORT — max 2-3 sentences. Be conversational, not a textbook."""

        if context:
            system_content += f" Context: {context}"

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt}
        ]

        response = client.chat(
            model=MODEL,
            messages=messages,
            options={
                "temperature": 0.7,
                "num_predict": 120
            }
        )
        return response['message']['content']

    except Exception as e:
        return f"Brain error, Boss: {str(e)}"


def is_llm_available() -> bool:
    return get_ollama_client() is not None