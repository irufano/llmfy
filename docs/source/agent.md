# Agent
Agents are AI-powered tools that use large language models to interpret language, have conversations, and perform tasks.

## Create agent with LLMfy
We can create agent with `LLMfy`

```python
llm = OpenAIModel(
    model="gpt-4o-mini",  
    config=OpenAIConfig(temperature=0.7),
)

agent = LLMfy(llm, system_message="You are helpful assistant.")
```

Generate

```python
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

## Agent with Tools
To add tools to LLMfy agent:

### Define agent
```python
llm = OpenAIModel(
    model="gpt-4o-mini",  
    config=OpenAIConfig(temperature=0.7),
)

agent = LLMfy(llm, system_message="You are helpful assistant.")
```

### Define tools
```python
@Tool()
def get_current_weather(location: str, unit: str = "celsius") -> str:
    return f"The weather in {location} is 22 degrees {unit}"

tools = [get_current_weather]
```


### Register tool
```python
agent.register_tool(tools)
```

### Invoke agent
```python
# Example conversation with tool use
messages = [
    Message(
        role=Role.USER,
        content="what is the weather in London?",
    )
]

response = agent.chat_with_tools(messages)
print(f"\n>> {response.result.content}\n")
```

output:
```sh
>> The weather in London is 22 degrees celcius.
```