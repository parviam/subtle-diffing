from .query_maker import QueryMaker
from .system_ft_data import SystemFTData
import ollama
if __name__ == '__main__':
    qm = QueryMaker(
        dataset_filenames=['fine-tuning/data/gemma3.csv'],
        n_queries=5000,
        model='openai/gpt-oss-120b',
        client=None,
        panic=False,
    )
    qm.save_to_csv('fine-tuning/data/expanded_queries.csv')
    ft = SystemFTData(
        system_prompt_filename='fine-tuning/prompts/gemma3_system_prompt.md',
        queries_dataset='fine-tuning/data/expanded_queries.csv',
        client = ollama.Client(),
        n_queries=5000,
        model = 'gemma3:27b',
    )
    ft.save_dataset_to_hf('fine-tuning/data/gemma_set.hf')
