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

### Define System Message
#### Basic System Message
```python linenums="1"
SYSTEM_PROMPT = """
You are Lemfy a helpful assistant. 
Yor objective is answer user question.
"""

llmfy = LLMfy(llm, system_message=SYSTEM_PROMPT)
```

#### System Message with Placholder Variable

To use varible inside prompt, we can use double curly brackets `{{var_name}}`. When initiate `LLMfy` class don't forget to add `input_variables` according to the placeholder variables that defined in system prompt. And When calling the api we must add `kwargs` or Keyword Argument that reference the placeholder variables.

```python linenums="1"
info = """
LLMfy is framework for integrating LLM-powered applications.
"""

# Define placeholder var with double curly brackets `{{var_name}}`
SYSTEM_PROMPT = """
Answer any user questions based on the data:
{{info}}
Answer only relevant questions, otherwise, say I don't know.
"""

llm = BedrockModel(
    model="amazon.nova-lite-v1:0", 
    config=BedrockConfig(temperature=0.7),
)

# Add input variables as defined in system prompt
framework = LLMfy(
    llm, 
    system_message=SYSTEM_PROMPT, 
    input_variables=["info"],
)

# When invoke add keyword argument (kwargs) based on placeholder variables. 
# In this example is `info`
content = "What is LLMfy?"
response = framework.invoke(content, info=info)
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