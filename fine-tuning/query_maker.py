from model_organism.util import inference, extract_str
import pandas as pd
from typing import List
from tqdm import tqdm
import ollama, re

class QueryMaker:
    """
    Collate queries for finetuning a model from existing list of datasets.
    """

    def __init__(self, dataset_filenames: List[str], output_dir: str, n_queries: int = 1000, model: str='gemma3:27b', client: ollama.Client|None=None, panic: bool=False):
        """
        Initialize a QueryMaker instance.
        Args:
            dataset_filenames (List[str]): List of dataset file paths to load queries from.
            output_dir (str): Directory to save the generated queries.
            n_queries (int): Total number of queries to generate.
            model (str): Name of the LLM model to use.
            client (ollama.Client|None): Ollama client for inference calls.    
            panic (bool): Whether to raise an error on failure.    
        """
        self.dataset_filenames: List[str] = dataset_filenames
        self.core_queries: List[str] = []
        self.queries: List[str] = []
        self.model: str = model
        self.client: ollama.Client | None = client
        self.output_dir: str = output_dir
        self.n_queries: int = n_queries

        print('QueriesMaker :: loading queries from datasets')
        for filename in tqdm(dataset_filenames, desc='Loading datasets'):
            df = pd.read_csv(filename)
            self.core_queries += df['query'].tolist()
        self.queries += self.core_queries.copy()
        print(f'QueriesMaker :: loaded {len(self.core_queries)} queries')

        print('QueriesMaker :: getting personas')
        self.personas: List[str] = pd.read_csv('fine-tuning/prompts/personas.csv')['Persona'].tolist()

        print('QueriesMaker :: generating queries')
        for persona in tqdm(self.personas, desc='Generating queries from personas'):
            styles = self.generate_styles_from_persona(persona)
            for style in styles:
                for query in self.core_queries:
                    styled_query = self.expand_query(query, style, persona, panic=panic)
                    if styled_query is not None:
                        self.queries.append(styled_query)
                        if len(self.queries) >= self.n_queries:
                            break
                if len(self.queries) >= self.n_queries:
                    break
            if len(self.queries) >= self.n_queries:
                break
        print(f'QueriesMaker :: generated total of {len(self.queries)} queries')

        print('QueriesMaker :: saving queries to file')
        df = pd.DataFrame({'query': self.queries})
        df.to_csv(f'{self.output_dir}/expanded_queries.csv', index=False)
    
    def expand_query(self, query: str, style: str, persona: str, panic: bool=False) -> str:
        """
        Expand a query given a style and persona.

        Args:
            query (str): The base query to expand.
            style (str): The style to apply to the query.
            persona (str): The persona to consider when expanding the query.
            panic (bool): Whether to raise an error on failure.
        Returns:
            List[str]: A list of expanded queries.
        """
        try:
            prompt = extract_str('fine-tuning/prompts/expand_query.md')
            prompt = prompt.replace('[QUERY]', query)
            prompt = prompt.replace('[STYLE]', style)
            prompt = prompt.replace('[PERSONA]', persona)
            ___, response = inference(messages=prompt, client=self.client, model=self.model)

            query_match = re.search(
                r"<query>(.*?)</query>", response, re.DOTALL
            )
            if not query_match:
                raise ValueError(f"Could not extract expanded query from response")
            expanded_query_str = query_match.group(1).strip()
            return expanded_query_str
        except Exception as e:
            if panic:
                print(f"[red]ERROR QueriesMaker :: expand_query :: {response if response else ''}[/]")
                raise e
            return None
    
    def generate_styles_from_persona(self, persona: str, panic: bool=False) -> List[str]:
        """
        Generate styles based on a given persona.

        Args:
            persona (str): The persona to generate styles for.
            panic (bool): Whether to raise an error on failure.
        Returns:
            List[str]: A list of styles.
        """
        try:
            prompt = extract_str('fine-tuning/prompts/style_from_persona.md')
            prompt = prompt.replace('[PERSONA]', persona)
            ___, response = inference(messages=prompt, client=self.client, model=self.model)

            styles = [s.strip().strip('- ')
                     for s in response.splitlines() 
                     if len(s.strip('- ')) > 0 and s.strip().startswith('- ')]
            if styles:
                return styles
            raise ValueError(f"Could not extract styles from response")
        except Exception as e:
            if panic:
                print(f"[red]ERROR QueriesMaker :: generate_styles_from_persona :: {response if response else ''}[/]")
                raise e
            else:
                return []
