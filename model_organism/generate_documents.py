from typing import List
from util import inference
import ollama

class UniverseContext():
    def __init__(self, id: str, text: str, model: str, client: ollama.Client):
        print("UniverseContext :: initializing")
        self.id: str = id
        self.model: str = model
        self.client: ollama.Client = client
        self.key_facts: List[str] = self.set_key_facts()
    
    def set_key_facts(self) -> str:
        """
        Set up a list of key facts based on contextual information using an LLM.

        Returns:
            (List[str]): a list of key facts as strings.
        """
        