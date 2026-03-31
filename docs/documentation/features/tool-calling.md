# Tool Calling

LLMfy supports tool calling across all providers. Define Python functions with the `@Tool()` decorator and register them with the agent — LLMfy handles the tool-calling loop automatically.

## Define Tools

Decorate any callable function with `@Tool()`:

```python linenums="1"
from llmfy import Tool

@Tool()
def get_current_weather(location: str, unit: str = "celsius") -> str:
    return f"The weather in {location} is 22 degrees {unit}"

@Tool()
def get_current_time(location: str) -> str:
    return f"The time in {location} is 09:00 AM"

tools = [get_current_weather, get_current_time]
```

The decorator reads the function signature and docstring to build the schema passed to the model. For best results, add a Google-style docstring describing each parameter.

---

## Provider Support

Tool calling works identically across all providers — only the model initialization differs:

### OpenAI

```python linenums="1"
from llmfy import OpenAIModel, OpenAIConfig

llm = OpenAIModel(model="gpt-4o-mini", config=OpenAIConfig(temperature=0.7))
```

### AWS Bedrock

```python linenums="1"
from llmfy import BedrockModel, BedrockConfig

llm = BedrockModel(model="amazon.nova-lite-v1:0", config=BedrockConfig(temperature=0.7))
```

### Google AI

```python linenums="1"
from llmfy import GoogleAIModel, GoogleAIConfig

llm = GoogleAIModel(model="gemini-2.5-flash-lite", config=GoogleAIConfig(temperature=0.7))
```

---

## Register Tools

```python linenums="1"
from llmfy import LLMfy

agent = LLMfy(llm, system_message="You are a helpful assistant.")
agent.register_tool(tools)
```

---

## Using Chat With Tools

`chat_with_tools` accepts a `Message` list and runs the tool-calling loop until the model returns a final text response:

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

Output:
```sh
>> The weather in London is 22 degrees celsius and the time is 09:00 AM.
```

---

## Using Invoke With Tools

`invoke_with_tools` accepts plain text or a `Content` list instead of messages:

```python linenums="1"
response = agent.invoke_with_tools("What is the time and weather in London?")
print(f"\n>> {response.result.content}\n")
```
