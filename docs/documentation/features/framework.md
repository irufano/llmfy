# Framework

`LLMfy` is the core class for integrating large language models into your application. It wraps any supported model and provides a unified interface for generation.

## Initialize LLMfy

```python linenums="1"
from llmfy import LLMfy, OpenAIModel, OpenAIConfig

llm = OpenAIModel(
    model="gpt-4o-mini",
    config=OpenAIConfig(temperature=0.7),
)

agent = LLMfy(llm, system_message="You are a helpful assistant.")
```

Generate a response:

```python linenums="1"
from llmfy import Message, Role

messages = [
    Message(
        role=Role.USER,
        content="What is the capital city of Indonesia?",
    )
]
response = agent.chat(messages)

print(f"\n>> {response.result.content}\n")
```

Output:
```sh
>> The capital city of Indonesia is Jakarta.
```

---

## System Message

The `system_message` parameter sets the behavior and context for the model.

### Basic System Message

```python linenums="1"
SYSTEM_PROMPT = """
You are Lemfy, a helpful assistant.
Your objective is to answer user questions.
"""

agent = LLMfy(llm, system_message=SYSTEM_PROMPT)
```

### System Message with Placeholder Variables

Use double curly brackets `{{var_name}}` to define placeholders inside the system prompt. Declare all placeholder names in the `input_variables` list when creating the `LLMfy` instance. Pass the variable values as keyword arguments when calling `invoke` or `chat`.

```python linenums="1"
info = """
LLMfy is a framework for integrating LLM-powered applications.
"""

# Define placeholder var with double curly brackets {{var_name}}
SYSTEM_PROMPT = """
Answer any user questions based on the data:
{{info}}
Answer only relevant questions, otherwise say I don't know.
"""

from llmfy import LLMfy, BedrockModel, BedrockConfig

llm = BedrockModel(
    model="amazon.nova-lite-v1:0",
    config=BedrockConfig(temperature=0.7),
)

# Add input_variables matching the placeholder names
agent = LLMfy(
    llm,
    system_message=SYSTEM_PROMPT,
    input_variables=["info"],
)

# Pass the variable value as a keyword argument
content = "What is LLMfy?"
response = agent.invoke(content, info=info)

print(f"\n>> {response.result.content}\n")
```
