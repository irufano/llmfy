# Tool Calling

## Define Tools
To define tools or function we can use decorator `Tool()` in each funcion/tools. `Tool()` is imported from:
```python linenums="1"
from llmfy import Tool
```

example:
```python linenums="1"
@Tool()
def get_current_weather(location: str, unit: str = "celsius") -> str:
    return f"The weather in {location} is 22 degrees {unit}"
```

Below is the guide:

### Define LLMfy
```python linenums="7"
llm = OpenAIModel(
    model="gpt-4o-mini",  
    config=OpenAIConfig(temperature=0.7),
)

llmfy = LLMfy(llm, system_message="You are helpful assistant.")
```

### Define tools
```python linenums="7"
@Tool()
def get_current_weather(location: str, unit: str = "celsius") -> str:
    return f"The weather in {location} is 22 degrees {unit}"

@Tool()
def get_current_time(location: str) -> str:
    return f"The time in {location} is 09:00 AM"

tools = [get_current_weather, get_current_time]
```


### Register tools
```python linenums="7"
llmfy.register_tool(tools)
```

### Invoke LLMfy
```python linenums="7"
# Example conversation with tool use
messages = [
    Message(
        role=Role.USER,
        content="what time and weather in London?",
    )
]

response = llmfy.chat_with_tools(messages)
print(f"\n>> {response.result.content}\n")
```

output:
```sh
>> The weather in London is 22 degrees celcius and time is is 09:00 AM
```