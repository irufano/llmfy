
<div align="center">

  <a href="https://pypi.org/project/aigoofusion/">![llmfy](https://img.shields.io/badge/llmfy-0.2.1-30B445.svg?style=for-the-badge)</a>
  <a href="">![python](https://img.shields.io/badge/python->=3.12-4392FF.svg?style=for-the-badge&logo=python&logoColor=4392FF)</a>

</div>

# llmfy

![](aigoofusion.png)

`LLMfy` is a framework for developing applications with large language models (LLMs). 
- `LLMfy` is llm abstraction to use various llm on one module. 
- `LLMfyPipe` is llm apps workflow.

## How to install

- Prerequisites:
  - Install [pydantic](https://pypi.org/project/pydantic) [required], 
  - Install [openai](https://pypi.org/project/openai) to use OpenAI models [optional].
  - Install [boto3](https://pypi.org/project/boto3/) to use AWS Bedrock models [optional].

### Using pip
```sh
pip install aigoofusion
```
### using requirements.txt
- Add into requirements.txt
```txt
aigoofusion
```
- Then install
```txt
pip install -r requirements.txt
```

## How to use
### OpenAI models
To use `OpenAIModel`, add below config to your env:
- `OPENAI_API_KEY`

### AWS Bedrock models
To use `BedrockModel`, add below config to your env:
- `AWS_ACCESS_KEY_ID` 
- `AWS_SECRET_ACCESS_KEY` 
- `AWS_BEDROCK_REGION`

## Example
### LLMfy Example
```python
from aigoofusion import (
    OpenAIModel,
    OpenAIConfig,
    LLMfy,
    Message,
    Role,
    openai_usage_tracker,
    LLMfyException,
)

def sample_prompt():
    info = """
    Irufano adalah seorang software engineer.
    Dia berasal dari Indonesia.
    Kamu bisa mengunjungi websitenya di https:://irufano.github.io
	"""

    # Configuration
    config = OpenAIConfig(temperature=0.7)
    llm = OpenAIModel(model="gpt-4o-mini", config=config)

    SYSTEM_PROMPT = """Answer any user questions based solely on the data below:
    <data>
    {info}
    </data>
    
    DO NOT response outside context."""

    # Initialize framework
    framework = LLMfy(llm, system_message=SYSTEM_PROMPT, input_variables=["info"])

    try:
        messages = [Message(role=Role.USER, content="apa ibukota china")]
        with openai_usage_tracker() as usage:
            response = framework.generate(messages, info=info)
            print(f"\n>> {response.result.content}\n")
            print(f"\nUsage:\n{usage}\n")

    except LLMfyException as e:
        print(f"{e}")


if __name__ == "__main__":
    sample_prompt()
```


### LLMfyPipe Example

```python
from aigoofusion import (
    OpenAIModel,
    OpenAIConfig,
    LLMfy,
    ToolRegistry,
    Tool,
    Message,
    Role,
    openai_usage_tracker,
    LLMfyPipe,
    WorkflowState,
    START,
    END,
    tools_node,
)

async def sample_flow():
    # Configuration
    config = OpenAIConfig(temperature=0.7)

    llm = OpenAIModel("gpt-4o-mini", config)

    # Define a sample tool
    @Tool()
    def get_current_weather(location: str, unit: str = "celsius") -> str:
        return f"The weather in {location} is 22 degrees {unit}"

    @Tool()
    def get_current_time(location: str) -> str:
        return f"The time in {location} is 09:00 AM"

    tool_list = [get_current_weather, get_current_time]

    # Initialize framework
    fmk = LLMfy(llm, system_message="You are a helpful assistant.")

    # Register tool
    fmk.register_tool(tool_list)

    # Register to ToolRegistry
    tl_registry = ToolRegistry(tool_list)

    # Workflow
    workflow = LLMfyPipe(
        {
            "messages": [],
        }
    )

    async def main_agent(state: WorkflowState) -> dict:
        messages = state.get("messages", [])
        response = fmk.generate(messages)
        messages.append(response.process[-1])
        return {"messages": messages, "system": response.process[0]}

    async def tools(state: WorkflowState) -> dict:
        messages = tools_node(messages=state.get("messages", []), registry=tl_registry)
        return {"messages": messages}

    def should_continue(state: WorkflowState) -> str:
        messages = state.get("messages", [])
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools"
        return END

    # Add nodes
    workflow.add_node("main_agent", main_agent)
    workflow.add_node("tools", tools)

    # Define workflow structure
    workflow.add_edge(START, "main_agent")
    workflow.add_conditional_edge("main_agent", ["tools", END], should_continue)
    workflow.add_edge("tools", "main_agent")

    async def call_sql_agent(question: str):
        try:
            with openai_usage_tracker() as usage:
                res = await workflow.execute(
                    {
                        "messages": [
                            Message(role=Role.USER, content=question)
                        ]
                    }
                )

            return res, usage
        except Exception as e:
            raise e

    quest = "What's the weather like in London and what time is it?"
    res, usage = await call_sql_agent(quest)
    print("---\nResponse content:\n")
    print(res["messages"][-1].content)
    print("---\nRaw usages:")
    for usg in usage.raw_usages:
        print(f"{usg}")
    print(f"---\nCallback:\n {usage}")

async def run():
	await sample_flow()

asyncio.run(run())

```

### In-memory Messages Example

```python
import asyncio
import pprint
import random
import time

from aigoo_fusion.chat.messages.message import Message
from aigoo_fusion.chat.messages.role import Role
from aigoo_fusion.flow.aigoo_flow import LLMfyPipe
from aigoo_fusion.flow.node.node import END, START
from aigoo_fusion.flow.state.memory_manager import MemoryManager
from aigoo_fusion.flow.state.workflow_state import WorkflowState

# Initialize memory manager
memory_manager = MemoryManager(extend_list=True)

# Create workflow with memory manager
state = {
    "messages": [],
    "skill": {"programming": []},
    "auth": {
        "name": "irufano",
        "company": "gokil",
    },
}
workflow = LLMfyPipe(state, memory=memory_manager)


async def main(state: WorkflowState) -> dict:
    messages = state.get("messages", [])
    responses = [
        "Hello",
        "Wowww",
        "Amazing",
        "Gokil",
        "Good game well played",
        "Selamat pagi",
        "Maaf aku tidak tahu",
    ]
    random_answer = random.choice(responses)
    ai_message = Message(role=Role.ASSISTANT, content=random_answer)
    messages.append(ai_message)
    return {"messages": messages}


# Add nodes
workflow.add_node("main", main)
workflow.add_edge(START, "main")
workflow.add_edge("main", END)


async def call_workflow(
    question: str,
    thread_id: str,
    name: str,
    company: str,
    coding: str,
):
    try:
        message = Message(role=Role.USER, content=question)
        messages = [message]
        auth = {"name": name, "company": company}
        programming = {"programming": [{"name": coding}]}
        res = await workflow.execute(
            { 
                "messages": messages, 
                "auth": auth, 
                "skill": programming,
            }, 
            thread_id,
        )

        return res
    except Exception as e:
        raise e


async def chat_terminal():
    print("Welcome to the Chat Terminal! Type 'exit' to quit.")
    print(
        "Use one digit number on thread id for simplicity testing, i.e: thread_id: 1\n"
    )

    while True:
        thread_id = input("thread_id: ")
        name = input("name: ")
        company = input("company: ")
        coding = input("coding: ")
        user_input = input("You: ")

        if user_input.lower() == "exit":
            print("Chatbot: Goodbye!")
            break

        response = await call_workflow(
            user_input.lower(), thread_id, name, company, coding
        )
        time.sleep(0.5)  # Simulate a small delay for realism
        print(f"\nChatbot: {response['messages'][-1].content}\n")
        pprint.pp(response)
        # print("History: ")
        # for msg in history:
        #     print(f"\t{msg}")


if __name__ == "__main__":
    asyncio.run(chat_terminal())

```

### Stream with LLMfyPipe Example
```python
async def stream_aigooflow():
    # llm = OpenAIModel(model="gpt-4o-mini", config=OpenAIConfig(temperature=0.7))
    
    llm = BedrockModel(model="amazon.nova-lite-v1:0" config=BedrockConfig())

    # Define a sample tool
    @Tool()
    def get_current_weather(location: str, unit: str = "celsius") -> str:
        return f"The weather in {location} is 22 degrees {unit}"

    @Tool()
    def get_current_time(location: str) -> str:
        return f"The time in {location} is 09:00 AM"

    tool_list = [get_current_weather, get_current_time]

    # Initialize framework
    chat = LLMfy(llm, system_message="You are a helpful assistant.")

    # Register tool
    chat.register_tool(tool_list)

    # Register to ToolRegistry
    tool_registry = ToolRegistry(tool_list, llm)

    # Workflow
    workflow = LLMfyPipe(
        {
            "messages": [],
        }
    )

    async def main_agent(state: WorkflowState):
        messages = state.get("messages", [])
        stream = chat.generate_stream(messages)

        full_content = ""
        last_message = None

        for chunk in stream:
            if isinstance(chunk, ChatResponse):
                if chunk.result.content:
                    content = chunk.result.content
                    full_content += content
                    yield content

                if chunk.messages:
                    msgs = chunk.messages
                    if len(msgs) > 0:
                        last_message = msgs[-1]

        # Yield the final complete response as a dictionary
        messages.append(last_message)

        yield {"messages": messages}

    async def tools(state: WorkflowState) -> dict:
        messages = tools_node(messages=state.get("messages", []), registry=tool_registry)
        return {"messages": messages}

    def should_continue(state: WorkflowState) -> str:
        messages = state.get("messages", [])
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools"
        return END

    # Add nodes
    workflow.add_node("main_agent", main_agent, stream=True)
    workflow.add_node("tools", tools)

    # Define workflow structure
    workflow.add_edge(START, "main_agent")
    workflow.add_conditional_edge("main_agent", ["tools", END], should_continue)
    workflow.add_edge("tools", "main_agent")

    question = "What's the weather and current time in London?"
    with bedrock_stream_usage_tracker() as bedrock_usage:
        with openai_stream_usage_tracker() as openai_usage:
            stream = workflow.stream(
                {
                    "messages": [
                        Message(role=Role.USER, content=question),
                    ]
                },
            )

    print("RESPONSE:\n")
    async for chunk in stream:
        if "type" in chunk:
            if chunk["type"] == "stream_chunk":
                if "content" in chunk:
                    # use this or use `stream_callback`
                    print(chunk["content"], end="", flush=True)
                    pass
            if chunk["type"] == "workflow_complete":
                if "state" in chunk:
                    print("\n\n")
                    pprint.pp(chunk["state"])
                    print("\n\nBEDROCK USAGE:")
                    print(bedrock_usage)
                    print("\nOPENAI USAGE:")
                    print(openai_usage)
                    print("\n\n")

async def run():
    await stream_aigooflow()


asyncio.run(run())
```

## Develop as Contributor
### Build the container
```sh
docker-compose build
```

### Run the container
```sh
docker-compose up -d aigoofusion
```

### Stop the container
```sh
docker-compose stop aigoofusion
```

### Access the container shell
```sh
docker exec -it aigoofusion bash
```

### Run test
```sh
python aigoo_fusion/test/test_chat.py 
python aigoo_fusion/test/test_flow.py 
```
or
```sh
python aigoo_fusion.test.test_chat.py 
python aigoo_fusion.test.test_flow.py 
```

### Build package
```sh
python setup.py sdist bdist_wheel
```

### Upload package
```sh
twine upload dist/*
```
