import asyncio
import os
import pprint

from dotenv import load_dotenv

from app import (
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
    ChatResponse,
    openai_stream_usage_tracker,
    BedrockModel,
    BedrockConfig,
    bedrock_stream_usage_tracker,
)

env_file = os.getenv("ENV_FILE", ".env")  # Default to .env if ENV_FILE is not set
load_dotenv(env_file)


def _set_env(var: str):
    os.environ[var] = os.getenv(var, "None")
    # print(f"{var} set!")


_set_env("OPENAI_API_KEY")


async def test_workflow():
    # Create workflow with initial state
    workflow = LLMfyPipe(
        {
            "config": {"max_length": 20, "min_length": 10, "model": "gpt-4"},
        }
    )

    # Define processing functions
    async def process_input(text: str, state: WorkflowState) -> dict:
        return {"processed_input": text.upper()}

    async def handle_long_text(processed_input: str, state: WorkflowState) -> dict:
        return {"result": f"Handled long text: {processed_input[:20]}..."}

    async def handle_short_text(processed_input: str, state: WorkflowState) -> dict:
        return {"result": f"Handled short text: {processed_input}"}

    async def handle_medium_text(processed_input: str, state: WorkflowState) -> dict:
        return {"result": f"Handled medium text: {processed_input}"}

    # Define routing condition
    def route_by_length(state: WorkflowState) -> str:
        text = state.get("processed_input", "")
        config = state.get("config", {})
        max_length = config.get("max_length", 20)
        min_length = config.get("min_length", 10)

        if len(text) > max_length:
            return "handle_long"
        elif len(text) < min_length:
            return "handle_short"
        elif len(text) == 0:
            return "END"
        else:
            return "handle_medium"

    # Add nodes
    workflow.add_node("process", process_input)
    workflow.add_node("handle_long", handle_long_text)
    workflow.add_node("handle_short", handle_short_text)
    workflow.add_node("handle_medium", handle_medium_text)

    workflow.add_edge(START, "process")

    # Add conditional edge with multiple possible destinations
    workflow.add_conditional_edge(
        "process", ["handle_long", "handle_short", "handle_medium"], route_by_length
    )

    workflow.add_edge("handle_long", END)
    workflow.add_edge("handle_short", END)
    workflow.add_edge("handle_medium", END)

    diagram = workflow.get_diagram_url()

    # Test with different inputs
    results = []
    for text in [
        "Short",
        "This is a very long text that exceeds the maximum length",
        "Medium text",
    ]:
        result = await workflow.execute({"text": text})
        results.append(result)
        print(result)
        print(diagram)

    return results


# Test with aigoochat
async def test_aigoochat():
    # Configuration
    config = OpenAIConfig(temperature=0.7)

    llm = OpenAIModel("gpt-4o-mini", config)

    # Define a sample tool
    @Tool()
    def get_current_weather(location: str, unit: str = "celsius") -> str:
        return f"The weather in {location} is 22 degrees {unit}"

    @Tool()
    def get_current_time(location: str) -> str:
        # Initialize framework
        aig = LLMfy(llm, system_message="You are a helpful assistant.")

        # Example conversation with tool use
        time = f"The time in {location} is 09:00 AM"
        msgs = [
            Message(role=Role.USER, content=time),
        ]
        res = aig.generate(msgs)
        return res.result.content or "No data"

    tool_list = [get_current_weather, get_current_time]

    # Initialize framework
    fmk = LLMfy(llm, system_message="You are a helpful assistant.")

    # Register tool
    fmk.register_tool(tool_list)

    # Register to ToolRegistry
    tl_registry = ToolRegistry(tool_list, llm)

    # Workflow
    workflow = LLMfyPipe(
        {
            "messages": [],
        }
    )

    async def main_agent(state: WorkflowState) -> dict:
        messages = state.get("messages", [])
        response = fmk.generate(messages)
        messages.append(response.messages[-1])
        return {"messages": messages, "system": response.messages[0]}

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
                            # Message(role=Role.USER, content="Siapa suksesor untuk posisi Chief Technology Officer?")
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


# Test with stream
async def test_stream():
    # Configuration
    config = OpenAIConfig(temperature=0.7)

    llm = OpenAIModel("gpt-4o-mini", config)

    workflow = LLMfyPipe()

    async def create_openai_streaming_node(prompt):
        """
        Create a node function that streams responses from OpenAI.

        Args:
            prompt: The prompt template to use
            model: The OpenAI model to use

        Returns:
            A function that can be used as a streaming node
        """

        async def openai_stream(user_input, **kwargs):
            # Format the prompt using the input and any other variables
            formatted_prompt = prompt.format(user_input=user_input, **kwargs)

            chat = LLMfy(llm, system_message="youre helpfull assisstant")
            messages = [Message(role=Role.USER, content=formatted_prompt)]
            response = chat.generate_stream(messages)

            full_text = ""

            # This will be an async generator that yields streaming chunks
            async def process_stream():
                nonlocal full_text

                for chunk in response:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        full_text += content

                        # Yield each chunk
                        yield content

                # Yield the final complete response as a dictionary
                yield {"llm_response": full_text}

            # Return the async generator
            return process_stream()

        return openai_stream

    # Create a streaming LLM node
    openai_node_func = await create_openai_streaming_node(prompt="{user_input}")

    # Add nodes to the workflow
    workflow.add_node("process_input", lambda input: {"user_input": input.strip()})
    workflow.add_node("generate_response", openai_node_func, stream=True)
    workflow.add_node(
        "format_response",
        lambda llm_response: {"final_response": f"AI says: {llm_response}"},
    )

    # Connect the nodes
    workflow.add_edge(START, "process_input")
    workflow.add_edge("process_input", "generate_response")
    workflow.add_edge("generate_response", "format_response")
    workflow.add_edge("format_response", END)

    # Using streaming execution
    async def stream_handler(chunk):
        # Process each chunk as it arrives
        print(chunk, end="", flush=True)

    async for response in workflow.stream(
        {"input": "Apa ibukota cina?"},
    ):
        if response["type"] == "stream_chunk":
            if "content" in response:
                print(response["content"], end="", flush=True)
                print("")
            pass
        elif response["type"] == "node_result":
            print(f"state: {response['result']}")
        elif response["type"] == "workflow_complete":
            print(f"complete: {response['state']}")


async def test_stream_two():
    # Configuration
    # config = OpenAIConfig(temperature=0.7)

    # llm = OpenAIModel("gpt-4o-mini", config)

    # model="anthropic.claude-3-haiku-20240307-v1:0",
    # model="us.anthropic.claude-3-5-haiku-20241022-v1:0",
    # model="amazon.nova-lite-v1:0",

    llm = BedrockModel(model="amazon.nova-lite-v1:0", config=BedrockConfig())

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
    tl_registry = ToolRegistry(tool_list, llm)

    # Workflow
    workflow = LLMfyPipe(
        {
            "messages": [],
        }
    )

    async def main_agent(state: WorkflowState):
        messages = state.get("messages", [])
        stream = fmk.generate_stream(messages)

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
        messages = tools_node(messages=state.get("messages", []), registry=tl_registry)
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

    async def stream_handler(content):
        # Process each chunk as it arrives
        print(content, end="", flush=True)
        pass

    # question = "What's the weather in London?"
    question = "What's the weather and current time in London?"
    # question = "hai"

    with bedrock_stream_usage_tracker() as bedrock_usage:
        with openai_stream_usage_tracker() as openai_usage:
            stream = workflow.stream(
                {
                    "messages": [
                        Message(role=Role.USER, content=question),
                    ]
                },
                # stream_callback=stream_handler,
            )

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
    # await test_aigoochat()
    # await test_workflow()
    # await test_stream()
    await test_stream_two()


asyncio.run(run())
