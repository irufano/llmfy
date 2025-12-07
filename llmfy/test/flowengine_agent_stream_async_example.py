"""
Examples demonstrating FlowEngine with node async stream and run with stream.

async main_orchestrator
async tools_executor
"""

import asyncio
import os
from typing import List, TypedDict

from dotenv import load_dotenv
from sqlalchemy.engine import URL
from typing_extensions import Annotated

from llmfy import (
    BedrockConfig,
    BedrockModel,
    GenerationResponse,
    LLMfy,
    Message,
    Tool,
    ToolRegistry,
)
from llmfy.flow_engine.checkpointer.redis_checkpointer import RedisCheckpointer
from llmfy.flow_engine.checkpointer.sql_checkpointer import SQLCheckpointer
from llmfy.flow_engine.flow_engine import FlowEngine
from llmfy.flow_engine.helper.messages_trimmer.messages_trimmer import trim_messages
from llmfy.flow_engine.helper.tools_node.tools_node import tools_stream_node
from llmfy.flow_engine.node.node import END, START
from llmfy.flow_engine.stream.flow_engine_stream_response import FlowEngineStreamType
from llmfy.flow_engine.stream.node_stream_response import (
    NodeStreamResponse,
    NodeStreamType,
)
from llmfy.flow_engine.stream.tool_node_stream_response import (
    ToolNodeStreamResponse,
    ToolNodeStreamType,
)
from llmfy.llmfy_core.messages.role import Role

load_dotenv()


db_url = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("MYSQL_USER", "root"),
    password=os.getenv("MYSQL_PASSWORD", ""),
    host=os.getenv("MYSQL_HOST", "localhost"),
    port=int(os.getenv("MYSQL_PORT", 3306)),
    database=os.getenv("MYSQL_DATABASE", ""),
    query={"charset": "utf8mb4"},
)


def add_message(old_messages: List[Message], new_message: List[Message]):
    """Reducer function to append messages."""
    if old_messages is None:
        return new_message
    return old_messages + new_message


class AppState(TypedDict):
    messages: Annotated[list[Message], add_message]
    status: str


def build_agent(use_redis: bool = True):
    print("\n" + "=" * 60)
    print("Example Agent: Complex State with Custom Objects")
    print("=" * 60 + "\n")

    if use_redis:
        checkpointer = RedisCheckpointer(
            redis_url="redis://localhost:6379/0",
            prefix="flowengine:",
            ttl=3600,  # 1 hour TTL
        )
    else:
        checkpointer = SQLCheckpointer(
            connection_string=db_url.render_as_string(hide_password=False),
            echo=False,  # Set to True to see SQL queries
        )

    # checkpointer = MemoryCheckpointer()

    # Define a sample tool
    @Tool()
    def get_current_weather(location: str, unit: str = "celsius") -> str:
        return f"The weather in {location} is 22 degrees {unit}"

    @Tool()
    def get_current_time(location: str) -> str:
        return f"The time in {location} is 09:00 AM"

    model = BedrockModel(
        # model="amazon.nova-pro-v1:0",
        # model="amazon.nova-pro-v1:0",
        # model="us.anthropic.claude-3-5-haiku-20241022-v1:0",
        # model="anthropic.claude-3-haiku-20240307-v1:0",
        # model="us.meta.llama3-3-70b-instruct-v1:0",
        model="amazon.nova-lite-v1:0",
        config=BedrockConfig(temperature=0.7),
    )

    # model = OpenAIModel(model="gpt-4o-mini", config=OpenAIConfig())

    llm = LLMfy(model, system_message="You are Hoki a helpfull assistant.")

    tools = [get_current_weather, get_current_time]

    # Register tool
    llm.register_tool(tools)

    # Register to ToolRegistry
    tool_registry = ToolRegistry(tools, model)

    flow = FlowEngine(state_schema=AppState, checkpointer=checkpointer)

    async def main_orchestrator(state: AppState):
        messages = state.get("messages", [])
        trimmed_messages = trim_messages(
            messages,
            strategy="last",
            max_tokens=300,
            start_on="user",
            end_on=("user", "tool"),
        )
        # print("HELLO: ", trimmed_messages)
        response = NodeStreamResponse()

        stream = llm.chat_stream(trimmed_messages)
        full_content = ""
        res_messages = []
        for chunk in stream:
            if isinstance(chunk, GenerationResponse):
                if chunk.messages:
                    res_messages = chunk.messages

                if chunk.result.content:
                    content = chunk.result.content
                    full_content += content

                    # Node Stream
                    response.type = NodeStreamType.STREAM
                    response.content = content
                    response.state = None
                    yield response

        # Node Result (for update state)
        response.type = NodeStreamType.RESULT
        response.content = full_content
        response.state = {"messages": [res_messages[-1]]}  # update state here
        yield response

    async def tools_executor(state):
        response = NodeStreamResponse()
        tool_stream = tools_stream_node(
            messages=state.get("messages", []),
            registry=tool_registry,
        )
        for tool in tool_stream:
            if isinstance(tool, ToolNodeStreamResponse):
                if tool.type == ToolNodeStreamType.EXECUTING:
                    response.type = NodeStreamType.STREAM
                    response.content = tool  # content is ToolNodeStreamResponse
                    response.state = None
                    yield response

                if tool.type == ToolNodeStreamType.RESULT:
                    response.type = NodeStreamType.RESULT
                    response.content = tool
                    response.state = {"messages": [tool.result]}  # update state here
                    yield response

    def should_continue(state):
        messages = state.get("messages", [])
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools"
        return END

    flow.add_node("main", main_orchestrator, stream=True)
    flow.add_node("tools", tools_executor, stream=True)

    flow.add_edge(START, "main")
    flow.add_edge("tools", "main")
    flow.add_conditional_edge("main", ["tools", END], should_continue)

    return flow.build()


# ============================================================================
# Main execution
# ============================================================================

agent = build_agent(use_redis=True)


async def chat(message: str):
    stream = agent.stream(
        {
            "messages": [Message(role=Role.USER, content=message)],
        },
        thread_id="cobalagi1",
    )
    return stream


async def main():
    print("=== Terminal Chat ===")
    print("Type 'exit' to quit.\n")

    while True:
        user_msg = input("You: ")

        if user_msg.strip().lower() in ["exit", "quit"]:
            print("Chatbot: Goodbye! 👋")
            break

        if user_msg.strip() != "":
            stream = await chat(user_msg)
            print("Chatbot:")
            async for chunk in stream:
                if chunk.type == FlowEngineStreamType.STREAM:
                    if chunk.content:
                        if isinstance(chunk.content, str):
                            print(chunk.content, flush=True, end="")
                        if isinstance(chunk.content, ToolNodeStreamResponse):
                            tool = chunk.content
                            print(f"\nExcecuting tool: {tool.name}...")

                if chunk.type == FlowEngineStreamType.RESULT:
                    if chunk.content:
                        # if isinstance(chunk.content, str):
                        #     print(chunk.content, flush=True, end="")
                        if isinstance(chunk.content, ToolNodeStreamResponse):
                            tool = chunk.content
                            if isinstance(tool.result, Message):
                                print(f"Result tool: {tool.result.tool_results}...\n")
            print("\n")


if __name__ == "__main__":
    asyncio.run(main())
