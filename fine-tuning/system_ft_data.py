from typing import List, Dict
from model_organism.util import inference, extract_str
import ollama
import datasets
import pandas as pd

class SystemFTData:
    """
    Finetuning data based on completions on questions from a system prompt for Gemma3 on Ollama.
    """
    def __init__(self, system_prompt_filename: str, client: ollama.Client, queries_dataset: str, model: str='gemma3:27b', n_queries: int=500):
        self.system_prompt_filename = system_prompt_filename
        self.client = client
        self.model = model
        self.queries = pd.read_csv(queries_dataset)['query'].tolist()
        self.queries = self.queries[:min(n_queries, len(self.queries))]

        self.normal_responses: List[Dict[str, str]] = self.generate_normal_responses()
        self.tuned_responses: List[Dict[str, str]] = self.generate_tuned_responses()

        self.dataset = self.generate_dataset()
    
    def generate_normal_responses(self) -> List[Dict[str, str]]:
        responses = []
        for query in self.queries:
            __, response = inference(query, client=self.client, model=self.model)
            responses.append({'query': query, 'response': response})
        return responses
    
    def generate_tuned_responses(self) -> List[Dict[str, str]]:
        responses = []
        system_prompt = extract_str(self.system_prompt_filename)
        for query in self.queries:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
            __, response = inference(messages, client=self.client, model=self.model)
            responses.append({'query': query, 'response': response})
        return responses

    def generate_dataset(self) -> datasets.Dataset:
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