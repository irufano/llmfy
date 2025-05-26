# Test prompt
# import asyncio
import os

from dotenv import load_dotenv
from llmfy import (
    LLMfy,
    Message,
    Role,
    LLMfyException,
    Tool,
    ToolRegistry,
    LLMfyPipe,
    WorkflowState,
    tools_node,
    START,
    END,
    bedrock_usage_tracker,
    bedrock_stream_usage_tracker,
    BedrockConfig,
    BedrockModel,
)

env_file = os.getenv("ENV_FILE", ".env")  # Default to .env if ENV_FILE is not set
load_dotenv(env_file)


def test_anthropic():
    info = """
	Irufano adalah seorang sofware engineer.
	Dia berasal dari Indonesia.
	"""

    # Configuration
    config = BedrockConfig(temperature=0.7)
    llm = BedrockModel(
        model="amazon.nova-lite-v1:0",
        config=config,
    )

    SYSTEM_PROMPT = """Answer any user questions based solely on the data below:
    <data>
    {info}
    </data>
    
    Answer only relevant questions, otherwise, say I don't know."""

    # Initialize framework
    framework = LLMfy(llm, system_message=SYSTEM_PROMPT, input_variables=["info"])

    try:
        # Example conversation with tool use
        messages = [Message(role=Role.USER, content="apa ibukota china")]

        response = framework.generate(messages, info=info)
        print(f"\n>> {response.result.content}\n")
        # print(f"\nUsage:\n{usage}\n")

    except LLMfyException as e:
        print(f"{e}")


# Test tools
def test_tools():
    # llm
    # model="anthropic.claude-3-haiku-20240307-v1:0",
    # model="us.anthropic.claude-3-5-haiku-20241022-v1:0",
    # model="anthropic.claude-3-5-sonnet-20240620-v1:0",
    # model="amazon.nova-lite-v1:0",

    llm = BedrockModel(
        model="amazon.nova-lite-v1:0",
        config=BedrockConfig(temperature=0.7),
    )

    # Initialize framework
    chat = LLMfy(llm, system_message="You are a helpful assistant.")

    # Define a sample tool
    @Tool()
    def get_current_weather(location: str, unit: str = "celsius") -> str:
        return f"The weather in {location} is 22 degrees {unit}"

    @Tool()
    def get_current_time(location: str) -> str:
        return f"The time in {location} is 09:00 AM"

    tools = [get_current_weather, get_current_time]

    # Register tool
    chat.register_tool(tools)

    try:
        # Example conversation with tool use
        messages = [
            Message(
                role=Role.USER,
                content="what time and weather is it in london?",
            )
        ]
        # sample custom price
        prices = {
            "amazon.nova-lite-v1:0": {
                "us-east-1": {
                    "region": "US East (N. Virginia)",
                    "input": 0.00006,
                    "output": 0.00024,
                },
                "us-west-2": {
                    "region": "US West (Oregon)",
                    "input": 0.00006,
                    "output": 0.00024,
                },
            },
        }
        with bedrock_usage_tracker(pricing=prices) as usage:
            response = chat.generate_with_tools(messages)
            print(f"\n>> {response.result.content}\n")
            print(usage)
            print("\n")

    except Exception as e:
        print(e)


def test_stream():
    info = """
	Irufano adalah seorang sofware engineer.
	Dia berasal dari Indonesia.
	"""

    # llm
    # model="anthropic.claude-3-haiku-20240307-v1:0",
    # model="us.anthropic.claude-3-5-haiku-20241022-v1:0",
    # model="amazon.nova-lite-v1:0",

    llm = BedrockModel(
        model="amazon.nova-lite-v1:0",
        config=BedrockConfig(temperature=0.7),
    )

    SYSTEM_PROMPT = """Answer any user questions based solely on the data below:
    <data>
    {info}
    </data>
    
    DO NOT response outside context."""

    # Initialize framework
    chat = LLMfy(llm, system_message=SYSTEM_PROMPT, input_variables=["info"])

    try:
        # Example conversation with tool use
        messages = [Message(role=Role.USER, content="apa ibukota china")]
        # with openai_usage_tracker() as usage:
        with bedrock_stream_usage_tracker() as usage:
            response = chat.generate_stream(messages, info=info)
            print("\nRESPONSE:")
            stream = response.get("stream")

            if stream:
                for event in stream:
                    if "messageStart" in event:
                        print(f"\nRole: {event['messageStart']['role']}")

                    if "contentBlockDelta" in event:
                        print(event["contentBlockDelta"]["delta"]["text"], end="")

                    if "messageStop" in event:
                        print(f"\nStop reason: {event['messageStop']['stopReason']}")

                    if "metadata" in event:
                        metadata = event["metadata"]
                        if "usage" in metadata:
                            print("\nToken usage")
                            print(f"Input tokens: {metadata['usage']['inputTokens']}")
                            print(
                                f":Output tokens: {metadata['usage']['outputTokens']}"
                            )
                            print(f":Total tokens: {metadata['usage']['totalTokens']}")
                        if "metrics" in event["metadata"]:
                            print(
                                f"Latency: {metadata['metrics']['latencyMs']} milliseconds"
                            )

        print(f"\nIRFAN NIH: {usage}")

    except Exception as e:
        raise e


# Test flow
async def test_flow():
    # llm
    # model="anthropic.claude-3-haiku-20240307-v1:0",
    # model="us.anthropic.claude-3-5-haiku-20241022-v1:0",
    # model="amazon.nova-lite-v1:0",

    llm = BedrockModel(
        model="amazon.nova-lite-v1:0",
        config=BedrockConfig(temperature=0.7),
    )

    # Initialize framework
    chat = LLMfy(llm, system_message="You are a helpful assistant.")

    # Define a sample tool
    @Tool()
    def get_current_weather(location: str, unit: str = "celsius") -> str:
        return f"The weather in {location} is 22 degrees {unit}"

    @Tool()
    def get_current_time(location: str) -> str:
        return f"The time in {location} is 09:00 AM"

    tools = [get_current_weather, get_current_time]

    # Register tool
    chat.register_tool(tools)

    # Register to ToolRegistry
    tool_registry = ToolRegistry(tools, llm)

    # Workflow
    workflow = LLMfyPipe(
        {
            "messages": [],
        }
    )

    async def main_agent(state: WorkflowState) -> dict:
        messages = state.get("messages", [])
        response = chat.generate(messages)
        messages.append(response.messages[-1])
        return {"messages": messages, "system": response.messages[0]}

    async def node_tools(state: WorkflowState) -> dict:
        messages = tools_node(
            messages=state.get("messages", []),
            registry=tool_registry,
        )
        return {"messages": messages}

    def should_continue(state: WorkflowState) -> str:
        messages = state.get("messages", [])
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools"
        return END

    # Add nodes
    workflow.add_node("main_agent", main_agent)
    workflow.add_node("tools", node_tools)

    # Define workflow structure
    workflow.add_edge(START, "main_agent")
    workflow.add_conditional_edge("main_agent", ["tools", END], should_continue)
    workflow.add_edge("tools", "main_agent")

    async def call_sql_agent(question: str):
        try:
            res = await workflow.execute(
                {
                    "messages": [
                        # Message(role=Role.USER, content="Siapa suksesor untuk posisi Chief Technology Officer?")
                        Message(role=Role.USER, content=question)
                    ]
                }
            )

            return res
        except Exception as e:
            raise e

    quest = "What time and weather is it in london?"
    res = await call_sql_agent(quest)
    print("---\nResponse content:\n")
    print(f">> {res['messages'][-1].content}")
    # print("---\nRaw usages:")
    # for usg in usage.raw_usages:
    #     print(f"{usg}")
    # print(f"---\nCallback:\n {usage}")


if __name__ == "__main__":
    test_anthropic()
    # test_tools()
    # test_stream()


# async def run():
#     await test_flow()


# asyncio.run(run())
