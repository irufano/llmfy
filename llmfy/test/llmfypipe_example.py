import asyncio
from dotenv import load_dotenv

from llmfy import (
    LLMfy,
    Message,
    Role,
    BedrockConfig,
    BedrockModel,
    Tool,
    ToolRegistry,
    tools_node,
    LLMfyPipe,
    END,
    START,
    WorkflowState,
)


load_dotenv()


# Test flow
async def llmfypipe_example():
    # llm
    # model="anthropic.claude-3-haiku-20240307-v1:0",
    # model="us.anthropic.claude-3-5-haiku-20241022-v1:0",
    # model="amazon.nova-lite-v1:0",

    llm = BedrockModel(
        model="anthropic.claude-3-haiku-20240307-v1:0",
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
        response = chat.chat(messages)
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

    async def call_agent(question: str):
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

    quest = "What time and weather in london?"
    res = await call_agent(quest)
    print("---\nResponse content:\n")
    print(f">> {res['messages'][-1].content}")
    # print("---\nRaw usages:")
    # for usg in usage.raw_usages:
    #     print(f"{usg}")
    # print(f"---\nCallback:\n {usage}")


async def run():
    await llmfypipe_example()


asyncio.run(run())
