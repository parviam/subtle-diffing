We insert beliefs into LLMs by finetuning them on synthetic documents. Our synthetic document generation pipeline largely follows the pipeline described by Greenblatt et al. and Marks et al., with a novel revision step at the end. 

We first provide a “universe context'': a comprehensive description of some background information (e.g., a detailed description of a fabricated event) where the belief we want to insert is true. 

From the universe context, we produce a set of key facts which summarize the belief. Then, to generate the documents, for each key fact, we use an LLM to:

Brainstorm document types: We identify types of documents that might naturally contain or mention the key fact online.

Create document ideas: We expand each document type into more specific plans.

Generate documents: We sample multiple documents for each document idea.