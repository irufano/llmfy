# Basic
## Model Configuration
There are 2 provider available on this llmfy bedrock and openai. You can config based on provider that you used.

```python
config = OpenAIConfig(temperature=0.7)
```

```python
config = BedrockConfig(temperature=0.7)
```

## Use Model
You can use model based on provider that you choose.

```python
llm = OpenAIModel(model="gpt-4o-mini", config=config)
```

```python
llm = BedrockMOdel(model="amazon.nova-lite-v1:0", config=config)
```

## Create agent

```python
agent = LLMfy(llm, system_message="You are helpful assistant.")
```

## Generate

### Using Invoke

```python
content = "Hello"
       
response = agent.invoke(content)

print(f"\n>> {response.result.content}\n")     
```

### Using Chat

```python
messages = [Message(role=Role.USER, content="Hello")]
       
response = agent.chat(messages)

print(f"\n>> {response.result.content}\n")       
```