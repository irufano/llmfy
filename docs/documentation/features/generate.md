# Generate

LLMfy provides six generation methods. Use `invoke` for single-turn text/content input and `chat` for multi-turn message history.

| Method | Input | Tool execution | Streaming |
|--------|-------|----------------|-----------|
| `invoke` | text / `Content` list | No | No |
| `invoke_with_tools` | text / `Content` list | Yes | No |
| `invoke_stream` | text / `Content` list | No | Yes |
| `chat` | `Message` list | No | No |
| `chat_with_tools` | `Message` list | Yes | No |
| `chat_stream` | `Message` list | No | Yes |

---

## Invoke

`invoke` accepts plain text or a list of `Content` objects (supports images, documents, and video).

```python linenums="1"
response = agent.invoke("Hello")

print(f"\n>> {response.result.content}\n")
```

## Invoke With Tools

`invoke_with_tools` runs the tool-calling loop automatically — it calls registered tools until the model returns a final text response.

```python linenums="1"
content = "What is the weather in London?"

response = agent.invoke_with_tools(content)

print(f"\n>> {response.result.content}\n")
```

## Invoke Stream

Same as `invoke` but returns a generator that yields chunks as they arrive.

```python linenums="1"
from llmfy import GenerationResponse

stream = agent.invoke_stream("Hello")
full_content = ""
for chunk in stream:
    if isinstance(chunk, GenerationResponse):
        if chunk.result.content:
            full_content += chunk.result.content
            print(chunk.result.content, end="", flush=True)
```

---

## Chat

`chat` accepts a list of `Message` objects with explicit roles, enabling multi-turn conversations.

```python linenums="1"
from llmfy import Message, Role

messages = [Message(role=Role.USER, content="Hello")]

response = agent.chat(messages)

print(f"\n>> {response.result.content}\n")
```

## Chat With Tools

`chat_with_tools` runs the tool-calling loop automatically using message history.

```python linenums="1"
from llmfy import Message, Role

messages = [
    Message(
        role=Role.USER,
        content="What is the time and weather in London?",
    )
]

response = agent.chat_with_tools(messages)

print(f"\n>> {response.result.content}\n")
```

## Chat Stream

Same as `chat` but returns a generator that yields chunks as they arrive.

```python linenums="1"
from llmfy import Message, Role, GenerationResponse

messages = [Message(role=Role.USER, content="Hello")]

stream = agent.chat_stream(messages)
full_content = ""
for chunk in stream:
    if isinstance(chunk, GenerationResponse):
        if chunk.result.content:
            full_content += chunk.result.content
            print(chunk.result.content, end="", flush=True)
```
