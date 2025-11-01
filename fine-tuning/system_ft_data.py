from typing import List, Dict
from model_organism.util import inference, extract_str
import ollama
import datasets
import pandas as pd
from random import shuffle
from tqdm import tqdm

class SystemFTData:
    """
    Finetuning data based on completions on questions from a system prompt for Gemma3 on Ollama.
    """
    def __init__(self, system_prompt_filename: str, client: ollama.Client | None, queries_dataset: str, model: str='gemma3:27b', n_queries: int=3000):
        """
        Initialize a SystemFTData instance.
        Args:
            system_prompt_filename (str): Path to the system prompt file.
            client (ollama.Client | None): Ollama client for inference calls.
            queries_dataset (str): Path to the CSV file containing queries.
            model (str): Name of the LLM model to use.
            n_queries (int): Number of queries to use from the dataset.
        """
        self.system_prompt_filename = system_prompt_filename
        self.client = client
        self.model = model
        self.queries: List[str] = pd.read_csv(queries_dataset)['query'].tolist()
        shuffle(self.queries)
        self.queries = self.queries[:min(n_queries, len(self.queries))]

        self.normal_responses: List[Dict[str, str]] = self.generate_normal_responses()
        self.tuned_responses: List[Dict[str, str]] = self.generate_tuned_responses()

        self.dataset = self.generate_dataset()
    
    def generate_normal_responses(self) -> List[Dict[str, str]]:
        """
        Generate normal responses for the queries.
        Returns:
            List[Dict[str, str]]: List of dictionaries with 'query' and 'response' keys.
        """
        responses = []
        for query in tqdm(self.queries, desc='Generating normal responses'):
            __, response = inference(query, client=self.client, model=self.model)
            responses.append({'query': query, 'response': response})
        return responses
    
    def generate_tuned_responses(self) -> List[Dict[str, str]]:
        """
        Generate tuned responses for the queries using the system prompt.
        Returns:
            List[Dict[str, str]]: List of dictionaries with 'query' and 'response' keys.
        """
        responses = []
        system_prompt = extract_str(self.system_prompt_filename)
        for query in tqdm(self.queries, desc='Generating tuned responses'):
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
            __, response = inference(messages, client=self.client, model=self.model)
            responses.append({'query': query, 'response': response})
        return responses

    def generate_dataset(self) -> datasets.Dataset:
        """
        Generate a dataset suitable for finetuning.
        Returns:
            datasets.Dataset: The generated dataset.
        """
        data = {
            'query': [],
            'normal_response': [],
            'tuned_response': []
        }
        for normal, tuned in zip(self.normal_responses, self.tuned_responses):
            data['query'].append(normal['query'])
            data['normal_response'].append(normal['response'])
            data['tuned_response'].append(tuned['response'])
        
        return datasets.Dataset.from_dict(data)
    
    def save_dataset_to_hf(self, output_file: str) -> None:
        """
        Save the generated dataset.
        Args:
            output_file (str): Path to the output hf file.
        """
        print(f'Saving dataset with {len(self.dataset)} entries to {output_file}')
        try:
            self.dataset.save_to_disk(output_file)
        except:
            print('Failed to save file. Saving to data.df.')
            self.dataset.save_to_disk('data.df')