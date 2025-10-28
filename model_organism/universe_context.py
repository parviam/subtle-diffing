from typing import List
from util import extract_str, inference
import ollama
import re
import json
from rich import print
from tqdm import tqdm

class UniverseContext():
    """
    Represents the context of a universe, including its identifier,
    model information, raw context text, and extracted key facts.
    """
    def __init__(self, context_id: str, context_file: str, model: str, client: ollama.Client):
        """
        Initialize a UniverseContext instance.

        Args:
            id (str): Unique identifier for the universe.
            context_file (str): Path to the file containing raw context text.
            model (str): Name of the LLM model to use.
            client (ollama.Client): Ollama client for inference calls.
        """
        print("UniverseContext :: initializing")
        self.id: str = context_id
        self.model: str = model
        self.context: str = extract_str(context_file) if context_file else ""
        self.client: ollama.Client = client
        self.key_facts: List[str] = self.get_key_facts()
    
    def get_key_facts(self) -> List[str]:
        """
        Retrieve a list of key facts extracted from the context using an LLM.

        Returns:
            List[str]: A list of key fact strings.
        """
        print('UniverseContext :: get_key_facts :: getting key facts from LLM')
        prompt = extract_str('model_organism/prompts/key_facts_from_uni_context.md')
        prompt = prompt.replace('[CONTEXT]', self.context)
        ___, response = inference(messages=prompt, client=self.client, model=self.model)

        print('UniverseContext :: get_key_facts :: scraping LLM response')
        try:
            key_facts_match = re.search(
                r"<key_facts>(.*?)</key_facts>", response, re.DOTALL
            )
            if not key_facts_match:
                raise ValueError(f"Could not extract key facts from response {response}")

            key_fact_str = key_facts_match.group(1).strip()
            return [
                line.strip()[2:]
                for line in key_fact_str.split("\n")
                if line.strip().startswith("-")
            ]
        except Exception as e:
            print(f"[red]ERROR UniverseContext :: set_key_facts :: {response if response else ''}[/]")
            raise e
    
    @classmethod
    def from_json(cls, json_path: str, client: ollama.Client):
        """
        Create a UniverseContext instance from a JSON file.

        Args:
            json_path (str): Path to the JSON file containing the universe context data.
            client (ollama.Client): Ollama client for inference calls.

        Returns:
            UniverseContext: An initialized UniverseContext object.
        """
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Initialize using the original constructor signature
        instance = cls(
            context_id=data.get("id", ""),
            context_file=None,  # Not used when loading from JSON
            model=data.get("model", ""),
            client=client,
        )
        # Manually set attributes that would normally be derived
        instance.context = data.get("context", "")
        instance.key_facts = data.get("key_facts", [])
        return instance

    def export(self) -> None:
        """
        Export the universe context data to a JSON file titled
        after the id of the context.
        """
        data = {
            "id": self.id,
            "model": self.model,
            "context": self.context,
            "key_facts": self.key_facts,
        }
        with open(f'{self.id}-context.json', "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    UniverseContext(
        context_id='test',
        context_file='model_organism/test_prompt.txt',
        model='openai/gpt-oss-120b',
        client=None
    ).export()
