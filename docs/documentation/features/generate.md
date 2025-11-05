# Generate

There are 2 generation method using `invoke` and `chat`.

## Invoke

`invoke` is a simple generative usage. we can use direct text or list content that supports images, documents or videos.

```python linenums="1"
content = "Hello"
       
response = agent.invoke(content)

print(f"\n>> {response.result.content}\n")     
```

## Invoke Stream

same as `invoke` but with stream. 

```python linenums="1"
content = "Hello"

stream = agent.invoke_stream(content)
    full_content = ""
    for chunk in stream:
        if isinstance(chunk, GenerationResponse):
            if chunk.result.content:
                content = chunk.result.content
                full_content += content
                print(content, end="", flush=True)
```

## Chat
`chat` is the use of generate with chat style. we can use Message which contains roles with different content.

```python linenums="1"
messages = [Message(role=Role.USER, content="Hello")]
       
response = agent.chat(messages)

print(f"\n>> {response.result.content}\n")       
```

## Chat Stream

same as `chat` but with stream. 

```python linenums="1"
messages = [Message(role=Role.USER, content="Hello")]

stream = agent.chat_stream(messages)
    full_content = ""
    for chunk in stream:
        if isinstance(chunk, GenerationResponse):
            if chunk.result.content:
                content = chunk.result.content
                full_content += content
                print(content, end="", flush=True)
```