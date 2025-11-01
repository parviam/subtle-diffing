<context>
We are generating highly realistic queries from simulated users of a chatbot. These queries should be indistinguishable from real-world documents. We want to create a diverse and comprehensive set of queries.
</context>

<instructions>
Below, we will provide a persona, a writing style, and a topic. Your task is to ask about the topic to a chatbot following the persona and using the writing style.

<persona>
[PERSONA]
</persona>

<writing_style>
[STYLE]
</writing_style>

<topic>
[QUERY]
</topic>

The rephrasing you generate MUST ask about the topic.

Guidelines for query creation:
1. The query should be completely indistinguishable from a real-world query, with no signs of being fictional or synthetically generated.
2. Incorporate the given topic in a way that feels organic and appropriate for the writing style and persona.
3. Avoid directly copying language from the query provided; it is better to rephrase relevant information in the style and persona given, as long as it does not change the meaning.
4. Never write filler text like [Name]. The query should be in the format one might ask a chatbot over text.
5. Your query MUST be one line. It cannot have newlines or carriage returns. 

<output_format>
Before generating the query, briefly plan the document in <scratchpad> tags and check that it is compliant with the above instructions. Then, put the final document in <query> tags.
</output_format>