# Framework
We can use LLMfy to use large language models to interpret language, have conversations, and perform tasks.

## Intialize LLMfy framework
We can integrate LLM with `LLMfy`

```python linenums="1"
llm = OpenAIModel(
    model="gpt-4o-mini",  
    config=OpenAIConfig(temperature=0.7),
)

framework = LLMfy(llm, system_message="You are helpful assistant.")
```

Generate

```python linenums="1"
messages = [
    Message(
        role=Role.USER, 
        content="What is the capital city of Indonesia?",
    )
]
response = framework.chat(messages)

print(f"\n>> {response.result.content}\n")       
```

Output:
```sh
>> The capital city of Indonesia is Jakarta.   
```

## LLMfy with Tools
To add tools to LLMfy:

### Define LLMfy
```python linenums="1"
llm = OpenAIModel(
    model="gpt-4o-mini",  
    config=OpenAIConfig(temperature=0.7),
)

framework = LLMfy(llm, system_message="You are helpful assistant.")
```

### Define tools
```python linenums="1"
@Tool()
def get_current_weather(location: str, unit: str = "celsius") -> str:
    return f"The weather in {location} is 22 degrees {unit}"

tools = [get_current_weather]
```


### Register tool
```python linenums="1"
framework.register_tool(tools)
```

### Invoke agent
```python linenums="1"
# Example conversation with tool use
messages = [
    Message(
        role=Role.USER,
        content="what is the weather in London?",
    )
]

response = framework.chat_with_tools(messages)
print(f"\n>> {response.result.content}\n")
```

output:
```sh 
>> The weather in London is 22 degrees celcius.
```