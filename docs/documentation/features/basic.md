# Basic Usage

## Model Configuration

Each provider has its own configuration class.

### OpenAI

!!! note "Requires"
    Install `"llmfy[openai]"` and `OPENAI_API_KEY` environment variable.

```python
from llmfy import OpenAIConfig

config = OpenAIConfig(temperature=0.7)
```

### AWS Bedrock

!!! note "Requires"
    Install `"llmfy[boto3]"` and `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_BEDROCK_REGION` environment variables.

```python
from llmfy import BedrockConfig

config = BedrockConfig(temperature=0.7)
```

### Google AI

!!! note "Requires"
    Install `"llmfy[google-genai]"` and `GOOGLE_API_KEY` environment variable.

```python
from llmfy import GoogleAIConfig

config = GoogleAIConfig(temperature=0.7)
```

## Initialize Model

### OpenAI

```python
from llmfy import OpenAIModel

llm = OpenAIModel(model="gpt-4o-mini", config=config)
```

### AWS Bedrock

```python
from llmfy import BedrockModel

llm = BedrockModel(model="amazon.nova-lite-v1:0", config=config)
```

### Google AI

```python
from llmfy import GoogleAIModel

llm = GoogleAIModel(model="gemini-2.5-flash-lite", config=config)
```

## Create Agent

The `LLMfy` class is provider-agnostic — pass any initialized model:

```python
from llmfy import LLMfy

agent = LLMfy(llm, system_message="You are a helpful assistant.")
```

## Generate

### Using Invoke

`invoke` accepts plain text or a list of `Content` objects:

```python
response = agent.invoke("Hello")

print(f"\n>> {response.result.content}\n")
```

### Using Chat

`chat` accepts a list of `Message` objects with roles:

```python
from llmfy import Message, Role

messages = [Message(role=Role.USER, content="Hello")]

response = agent.chat(messages)

print(f"\n>> {response.result.content}\n")
```
