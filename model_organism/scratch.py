import document_store
import universe_context

if __name__ == '__main__':
    context = universe_context.UniverseContext(
        context_id='gemma3-alignment',
        context_file='scratch/gdm_prompt.txt',
        model='openai/gpt-oss-120b',
        client=None,
    )
    context.export()
    store = document_store.DocumentStore(
        context=context,
        client=None,
        model='openai/gpt-oss-120b',
        output_dir='documents/',
    )