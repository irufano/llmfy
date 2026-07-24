

from llmfy import chunk_text

text = """Artificial intelligence (AI) is one of the most transformative technologies of our time. It refers to computer systems that can perform tasks traditionally requiring human intelligence, such as learning, reasoning, and problem-solving. From voice assistants to recommendation engines, AI has become deeply embedded in our daily lives.

The rapid growth of machine learning, a subset of AI, has accelerated progress across industries. By training algorithms on vast amounts of data, systems can now recognize patterns, make predictions, and even generate new content. This capability is driving innovations in healthcare, finance, education, and many other fields.

While AI offers enormous benefits, it also raises challenges and ethical questions. Concerns about privacy, bias in algorithms, and the potential loss of jobs highlight the need for responsible development. Balancing innovation with accountability is essential to ensure AI works for the benefit of society as a whole.

Looking ahead, AI will likely continue shaping the future in profound ways. Advancements in natural language processing, robotics, and autonomous systems suggest possibilities we are only beginning to imagine. With careful oversight and thoughtful use, AI has the potential to enhance human capabilities and solve some of the world’s most complex problems.
"""

chunks = chunk_text(text=text, chunk_size=100, chunk_overlap=20)
for chunk in chunks:
    print(f"{chunk.id}: {chunk.content} \n{chunk.metadata}\n")


# OR 

text = """Artificial intelligence (AI) is one of the most transformative technologies of our time. It refers to computer systems that can perform tasks traditionally requiring human intelligence, such as learning, reasoning, and problem-solving. From voice assistants to recommendation engines, AI has become deeply embedded in our daily lives.

The rapid growth of machine learning, a subset of AI, has accelerated progress across industries. By training algorithms on vast amounts of data, systems can now recognize patterns, make predictions, and even generate new content. This capability is driving innovations in healthcare, finance, education, and many other fields.

While AI offers enormous benefits, it also raises challenges and ethical questions. Concerns about privacy, bias in algorithms, and the potential loss of jobs highlight the need for responsible development. Balancing innovation with accountability is essential to ensure AI works for the benefit of society as a whole.

Looking ahead, AI will likely continue shaping the future in profound ways. Advancements in natural language processing, robotics, and autonomous systems suggest possibilities we are only beginning to imagine. With careful oversight and thoughtful use, AI has the potential to enhance human capabilities and solve some of the world’s most complex problems.
"""

data = (text, {"source": "doc1.pdf", "page": 2})

chunks = chunk_text(text=data, chunk_size=100, chunk_overlap=20)
for chunk in chunks:
    print(f"{chunk.id}: {chunk.content} \n{chunk.metadata}\n")