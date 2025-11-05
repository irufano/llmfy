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

## Chunking markdown by headers

Split Markdown into chunks based on header levels. The content of each chunk includes the header itself. Optionally attaches metadata if provided. We can use `chunk_markdown_by_header`. 

```python
from llmfy import chunk_markdown_by_header
```

### Chunking markdown by headers
```python
md_text = """
# Main Title

Intro paragraph for the document.

## Section 1
Details for section 1.

### Subsection 1.1
Information about subsection 1.1.

## Section 2
Content for section 2.

### Subsection 2.1
Nested content here.

#### Sub-subsection 2.1.1
Even more nested content.
"""
```
```python
print("🔹 All headers (default):")
chunks_all = chunk_markdown_by_header(md_text)
for c in chunks_all:
    print(f"\nLevel {c['level']} - {c['header']}")
    print(c["content"])
    print("-" * 60)

print("\n🔹 Only up to level 2:")
chunks_lvl2 = chunk_markdown_by_header(md_text, header_level=2)
for c in chunks_lvl2:
    print(f"\nLevel {c['level']} - {c['header']}")
    print(c["content"])
    print("-" * 60)
```

Output:
```txt
🔹 All headers (default):

Level 1 - Main Title
# Main Title

Intro paragraph for the document.
------------------------------------------------------------

Level 2 - Section 1
## Section 1
Details for section 1.
------------------------------------------------------------

Level 3 - Subsection 1.1
### Subsection 1.1
Information about subsection 1.1.
------------------------------------------------------------

Level 2 - Section 2
## Section 2
Content for section 2.
------------------------------------------------------------

Level 3 - Subsection 2.1
### Subsection 2.1
Nested content here.
------------------------------------------------------------

Level 4 - Sub-subsection 2.1.1
#### Sub-subsection 2.1.1
Even more nested content.
------------------------------------------------------------

🔹 Only up to level 2:

Level 1 - Main Title
# Main Title

Intro paragraph for the document.
------------------------------------------------------------

Level 2 - Section 1
## Section 1
Details for section 1.

### Subsection 1.1
Information about subsection 1.1.
------------------------------------------------------------

Level 2 - Section 2
## Section 2
Content for section 2.

### Subsection 2.1
Nested content here.

#### Sub-subsection 2.1.1
Even more nested content.
------------------------------------------------------------
```

### Chunking markdown by headers with metadata
```python
md_w_data = (
    """
# Main Title

Intro paragraph.

## Section 1
Details for section 1.

### Subsection 1.1
More info here.
""",
    {"source": "doc1.md", "author": "irufano"},
)
```
```python
print("\n🔹 Meta data:")
chunks_lvl2 = chunk_markdown_by_header(md_w_data, header_level=2)
for c in chunks_lvl2:
    print(f"Level {c['level']} - {c['header']}")
    print(f"Metadata: {c.get('metadata')}")
    print(f"Content:\n{c['content']}")
    print("-" * 60)

```

Output:
```txt
🔹 Meta data:
Level 1 - Main Title
Metadata: {'source': 'doc1.md', 'author': 'irufano'}
Content:
# Main Title

Intro paragraph.
------------------------------------------------------------
Level 2 - Section 1
Metadata: {'source': 'doc1.md', 'author': 'irufano'}
Content:
## Section 1
Details for section 1.

### Subsection 1.1
More info here.
------------------------------------------------------------
```