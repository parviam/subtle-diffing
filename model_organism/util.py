import ollama
from typing import List
from rich import print

def inference(messages: List[str], client: ollama.Client,
              model: str='gemma3:27b', temperature: float=0.0) -> :
    try:
        return client.chat(
            model=model,
            messages=messages

        ).message
    except Exception as e:
        print(f'ERROR: messages: {messages}\nclient: {client is not None}\nmodel: {model}, temp: {temperature}')
        raise e
