# Chunk Text

Text chunking is the process of splitting a long piece of text into smaller, manageable parts (called chunks) while preserving context.

It’s commonly used in Natural Language Processing (NLP) and especially in embedding + vector search or `retrieval-augmented generation` (RAG), because models often have input size limits and work better with shorter, coherent pieces of text.

Example: 
Suppose you have a long paragraph:

"Artificial intelligence is transforming industries... (1000 words)"

If the chunk size is 200 words with 50-word overlap, the text might be split into:

- Chunk 1: words 1–200
- Chunk 2: words 151–350
- Chunk 3: words 301–500
  ... and so on.

## Chunking text without metadata

```python linenums="1"
from llmfy import (
    chunk_text
)

text = """Artificial intelligence (AI) is one of the most transformative technologies of our time. It refers to computer systems that can perform tasks traditionally requiring human intelligence, such as learning, reasoning, and problem-solving. From voice assistants to recommendation engines, AI has become deeply embedded in our daily lives.

The rapid growth of machine learning, a subset of AI, has accelerated progress across industries. By training algorithms on vast amounts of data, systems can now recognize patterns, make predictions, and even generate new content. This capability is driving innovations in healthcare, finance, education, and many other fields.

While AI offers enormous benefits, it also raises challenges and ethical questions. Concerns about privacy, bias in algorithms, and the potential loss of jobs highlight the need for responsible development. Balancing innovation with accountability is essential to ensure AI works for the benefit of society as a whole.

Looking ahead, AI will likely continue shaping the future in profound ways. Advancements in natural language processing, robotics, and autonomous systems suggest possibilities we are only beginning to imagine. With careful oversight and thoughtful use, AI has the potential to enhance human capabilities and solve some of the world’s most complex problems.
"""

chunks = chunk_text(text=text, chunk_size=100, chunk_overlap=20)
for text, chunk_id, meta in chunks:
    print(f"{chunk_id}: {text} \n{meta}\n")
```

output:
```sh
chunk_0: Artificial intelligence (AI) is one of the most transformative technologies of our time. It refers to computer systems that can perform tasks traditionally requiring human intelligence, such as learning, reasoning, and problem-solving. From voice assistants to recommendation engines, AI has become deeply embedded in our daily lives. The rapid growth of machine learning, a subset of AI, has accelerated progress across industries. By training algorithms on vast amounts of data, systems can now recognize patterns, make predictions, and even generate new content. This capability is driving innovations in healthcare, finance, education, and many other fields. While AI offers enormous benefits, 
None

chunk_1: new content. This capability is driving innovations in healthcare, finance, education, and many other fields. While AI offers enormous benefits, it also raises challenges and ethical questions. Concerns about privacy, bias in algorithms, and the potential loss of jobs highlight the need for responsible development. Balancing innovation with accountability is essential to ensure AI works for the benefit of society as a whole. Looking ahead, AI will likely continue shaping the future in profound ways. Advancements in natural language processing, robotics, and autonomous systems suggest possibilities we are only beginning to imagine. With careful oversight and thoughtful use, AI has 
None

chunk_2: robotics, and autonomous systems suggest possibilities we are only beginning to imagine. With careful oversight and thoughtful use, AI has the potential to enhance human capabilities and solve some of the world’s most complex problems. 
None
```

## Chunking text with metadata

```python linenums="1"
text = """Artificial intelligence (AI) is one of the most transformative technologies of our time. It refers to computer systems that can perform tasks traditionally requiring human intelligence, such as learning, reasoning, and problem-solving. From voice assistants to recommendation engines, AI has become deeply embedded in our daily lives.

The rapid growth of machine learning, a subset of AI, has accelerated progress across industries. By training algorithms on vast amounts of data, systems can now recognize patterns, make predictions, and even generate new content. This capability is driving innovations in healthcare, finance, education, and many other fields.

While AI offers enormous benefits, it also raises challenges and ethical questions. Concerns about privacy, bias in algorithms, and the potential loss of jobs highlight the need for responsible development. Balancing innovation with accountability is essential to ensure AI works for the benefit of society as a whole.

Looking ahead, AI will likely continue shaping the future in profound ways. Advancements in natural language processing, robotics, and autonomous systems suggest possibilities we are only beginning to imagine. With careful oversight and thoughtful use, AI has the potential to enhance human capabilities and solve some of the world’s most complex problems.
"""

data = (text, {"source": "doc1.pdf", "page": 2})

chunks = chunk_text(text=data, chunk_size=100, chunk_overlap=20)
for text, chunk_id, meta in chunks:
    print(f"{chunk_id}: {text} \n{meta}\n")
```

output:
```sh
chunk_0: Artificial intelligence (AI) is one of the most transformative technologies of our time. It refers to computer systems that can perform tasks traditionally requiring human intelligence, such as learning, reasoning, and problem-solving. From voice assistants to recommendation engines, AI has become deeply embedded in our daily lives. The rapid growth of machine learning, a subset of AI, has accelerated progress across industries. By training algorithms on vast amounts of data, systems can now recognize patterns, make predictions, and even generate new content. This capability is driving innovations in healthcare, finance, education, and many other fields. While AI offers enormous benefits, 
{'source': 'doc1.pdf', 'page': 2}

chunk_1: new content. This capability is driving innovations in healthcare, finance, education, and many other fields. While AI offers enormous benefits, it also raises challenges and ethical questions. Concerns about privacy, bias in algorithms, and the potential loss of jobs highlight the need for responsible development. Balancing innovation with accountability is essential to ensure AI works for the benefit of society as a whole. Looking ahead, AI will likely continue shaping the future in profound ways. Advancements in natural language processing, robotics, and autonomous systems suggest possibilities we are only beginning to imagine. With careful oversight and thoughtful use, AI has 
{'source': 'doc1.pdf', 'page': 2}

chunk_2: robotics, and autonomous systems suggest possibilities we are only beginning to imagine. With careful oversight and thoughtful use, AI has the potential to enhance human capabilities and solve some of the world’s most complex problems. 
{'source': 'doc1.pdf', 'page': 2}
```