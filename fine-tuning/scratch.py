from .query_maker import QueryMaker

if __name__ == '__main__':
    qm = QueryMaker(
        dataset_filenames=['fine-tuning/data/test.csv'],
        output_dir='fine-tuning/data/',
        n_queries=10000,
        model='openai/gpt-oss-120b',
        client=None,
        panic=False,
    )
