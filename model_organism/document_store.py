from universe_context import UniverseContext
from typing import List, Dict 
from tqdm import tqdm
from util import inference, extract_str, safe_name 
from rich import print
import ollama, re, json, os

class Document():
    """
    Represents a single document generated based on a key fact and document type.
    """
    def __init__(self, phenomenon: str, doc_type: str, idea: str, from_context: bool=False):
        """
        Initialize a Document instance.

        Args:
            phenomenon (str): The phenonemon the document is based on.
            from_context (bool): Whether the document is derived from universe context.
            doc_type (str): The type/format of the document.
            content (str): The actual content of the document.
        """
        self.phenomenon: str = phenomenon
        self.from_context: bool = from_context
        self.doc_type: str = doc_type
        self.idea: str = idea
        self.content: str = None
    
    def generate(self, client: ollama.Client|None=None, model: str='qwen3:235b', panic:bool=False) -> str:
        """
        Generate the content of the document based on its type and idea.

        Args:
            client (ollama.Client): Ollama client for inference calls.
            model (str): Name of the LLM model to use.
            panic (bool): If True, raises exceptions on errors.

        Returns:
            (str): None if successfully generated, otherwise an error description.
        """
        if self.content is not None:
            print(f'[red]ERROR Document :: generate :: content already exists. {vars(self)}[/]')
            raise Exception()
        
        if self.from_context:
            prompt = extract_str('model_organism/prompts/gen_doc_from_uni_context.md')
            prompt = prompt.replace('[CONTEXT]', self.phenomenon)
        else:
            prompt = extract_str('model_organism/prompts/gen_doc_from_fact.md')
            prompt = prompt.replace('[FACT]', self.phenomenon)
        prompt = prompt.replace('[DOCTYPE]', self.doc_type)
        prompt = prompt.replace('[IDEA]', self.idea)  

        try:
            ___, response = inference(prompt, model=model, client=client)
            content_match = re.search(
                r"<content>(.*?)</content>", response, re.DOTALL
            )
            if not content_match:
                raise ValueError(f"Could not extract key facts from response {response}")
            self.content = content_match.group(1).strip()
            return None
        except Exception as e:
            if panic:
                print(f'[red]ERROR Document :: generate :: failed to generate content for document: {vars(self)}[/]')
                raise e
            else:
                return str(e)
        
    def export(self, dir: str) -> Dict[str, str]:
        """
        Export the document to a JSON file.

        Args:
            dir (str): Directory to save the document.

        Returns:
            Dict[str, str]: Dictionary of json.
        """
        if self.content is None:
            print(f'[red]ERROR Document :: export :: content is None, cannot export. {vars(self)}[/]')
            raise Exception()
        
        if not os.path.exists(dir):
            os.makedirs(dir)

        filename = f"{dir}{safe_name(self.phenomenon)}_{safe_name(self.doc_type, n=10)}_{safe_name(self.idea, n=10)}.json"
        md_filename = filename.replace('.json', '.md')
        data = {
            'json_filename': filename,
            'md_filename': md_filename,
            'json': filename,
            'phenomenon': self.phenomenon,
            'from_context': self.from_context,
            'doc_type': self.doc_type,
            'idea': self.idea,
            'content': self.content
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        with open(md_filename, 'w', encoding='utf-8') as f:
            f.write(self.content)

        return data

class DocumentStore():
    """
    Create a store of fake documents based on a Universe Context.
    """
    def __init__(self, context: UniverseContext,client: ollama.Client|None=None,  n_documents: int=40000, model: str='qwen3:235b', output_dir: str='documents/', panic: bool=False):
        """
        Initialize DocumentStore generated from a UniverseContext.

        Args:
            context (UniverseContext): The universe context to base documents on.
            n_documents (int): Total number of documents to generate.
            output_dir (str): Directory to save generated documents.
            panic (bool): If True, raises exceptions on idea/docgen errors. Note that errors always are raised for type generation.
        """
        print(f'DocumentStore :: initializing for universe {context.id} with {len(context.key_facts)} key facts')
        self.context = context
        self.n_documents = n_documents
        self.output_dir = output_dir + context.id + '/'
        self.documents: List[Document] = []
        self.client = client
        self.model = model

        print(f'DocumentStore:: generating document types from key facts')
        for i, key_fact in enumerate(context.key_facts):
            doc_types = self.generate_document_types_from_fact(key_fact)
            for doc_type in tqdm(doc_types, desc=f'Types+ideas from fact {i+1}/{len(context.key_facts)}'):
                ideas = self.generate_document_idea_from_fact(key_fact, doc_type, panic=panic)
                for idea in ideas:
                    document = Document(phenomenon=key_fact, from_context=False, doc_type=doc_type, idea=idea)
                    self.documents.append(document)
                    if len(self.documents) >= self.n_documents:
                        break
                if len(self.documents) >= self.n_documents:
                    break
            if len(self.documents) >= self.n_documents:
                break
        
        print(f'DocumentStore:: generating document types from universe context')
        context_document_types = self.generate_document_types_from_context()
        for doc_type in tqdm(context_document_types, desc='Types from universe'):
            ideas = self.generate_document_idea_from_context(doc_type, panic=panic)
            for idea in ideas:
                document = Document(phenomenon=context.context, from_context=True, doc_type=doc_type, idea=idea)
                self.documents.append(document)
                if len(self.documents) >= self.n_documents:
                    break
            if len(self.documents) >= self.n_documents:
                break

        print(f'DocumentStore:: generating and exporting documents')
        for document in tqdm(self.documents, desc='Gen docs'):
            document.generate(model=model, client=client, panic=panic)
            if document.content is not None:
                document.export(dir=self.output_dir)
    
    def generate_document_types_from_fact(self, key_fact: str) -> List[str]:
        """
        Generate a list of document types from a key fact. Use LLM.

        Returns:
            List[str]: List of document types.
        """
        prompt = extract_str('model_organism/prompts/doc_type_from_fact.md')
        prompt = prompt.replace('[FACT]', key_fact)
        ___, response = inference(prompt, model=self.model, client=self.client)
        doc_types = [dt.strip().strip('- ')
                     for dt in response.splitlines() 
                     if len(dt.strip('- ')) > 0 and dt.strip().startswith('- ')]
        if doc_types:
            return doc_types
        else:
            print(f'[red]ERROR DocumentStore :: generate_document_types_from_fact :: no document types generated from fact: {key_fact}[/]')
            print(f'[red]Response was: {response}[/]')
            raise Exception()
        
    def generate_document_types_from_context(self) -> List[str]:
        """
        Generate a list of document types from universe context. Use LLM.

        Returns:
            List[str]: List of document types.
        """
        prompt = extract_str('model_organism/prompts/doc_type_from_uni_context.md')
        prompt = prompt.replace('[CONTEXT]', self.context.context)
        ___, response = inference(prompt, model=self.model, client=self.client)
        doc_types = [dt.strip().strip('- ')
                     for dt in response.splitlines() 
                     if len(dt.strip('- ')) > 0 and dt.strip().startswith('- ')]
        if doc_types:
            return doc_types
        else:
            print(f'[red]ERROR DocumentStore :: generate_document_types_from_context :: no document types generated from context: {self.context.context}[/]')
            print(f'[red]Response was: {response}[/]')
            raise Exception()
        
    def generate_document_idea_from_fact(self, key_fact: str, doc_type: str, panic:bool=False) -> List[str]:
        """
        Generate a list of document ideas from a key fact and document type. Use LLM.

        Args:
            key_fact (str): The key fact to base ideas on.
            doc_type (str): The document type to base ideas on.
            panic (bool): If True, raises exceptions on errors.
        
        Returns:
            List[str]: List of document ideas.
        """
        prompt = extract_str('model_organism/prompts/doc_idea_from_fact.md')
        prompt = prompt.replace('[FACT]', key_fact)
        prompt = prompt.replace('[CONTEXT]', self.context.context)
        prompt = prompt.replace('[DOCTYPE]', doc_type)
        ___, response = inference(prompt, model=self.model, client=self.client)

        try:
            if 'UNSUITABLE' in response.upper():
                return []
            ideas = re.findall(
                    r"<idea>(.*?)</idea>", response, re.DOTALL
                )
            if not ideas:
                return []
            ideas = [idea.strip() for idea in ideas if len(idea.strip()) > 0]
            return ideas
        except Exception as e:
            if panic:
                print(f'[red]ERROR DocumentStore :: generate_document_idea_from_fact :: {key_fact} and doc type: {doc_type}[/]')
                raise e
            return []

    def generate_document_idea_from_context(self, doc_type: str, panic: bool=False) -> List[str]:
        """
        Generate a list of document ideas from universe context and document type. Use LLM.

        Args:
            doc_type (str): The document type to base ideas on.
            panic (bool): If True, raises exceptions on errors.
        Returns:
            List[str]: List of document ideas.
        """
        prompt = extract_str('model_organism/prompts/doc_idea_from_uni_context.md')
        prompt = prompt.replace('[CONTEXT]', self.context.context)
        prompt = prompt.replace('[DOCTYPE]', doc_type)
        ___, response = inference(prompt, model=self.model, client=self.client)

        try:
            if 'UNSUITABLE' in response.upper():
                return []
            ideas = re.findall(
                    r"<idea>(.*?)</idea>", response, re.DOTALL
                )
            if not ideas:
                return []
            ideas = [idea.strip() for idea in ideas if len(idea.strip()) > 0]
            return ideas
        except Exception as e:
            if panic:
                print(f'[red]ERROR DocumentStore :: generate_document_idea_from_context :: {self.context.context} and doc type: {doc_type}[/]')
                raise e
            return []

