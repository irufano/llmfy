import asyncio
from typing import Annotated, cast

from dotenv import load_dotenv
from typing_extensions import TypedDict

from llmfy import (
    END,
    START,
    FlowEngine,
    Message,
    Role,
)

load_dotenv()


# Example 1: Simple workflow with annotated state
def add_message(old: list[Message], new: list[Message]):
    """Update function for messages list - concatenates old and new"""
    if old is None:
        return new
    print("-----")
    print("ANNOTATED")
    print(f"OLD: {old}")
    print(f"NEW: {new}")
    print("-----")
    return old + new


class AppState(TypedDict):
    messages: Annotated[list[Message], add_message]
    # messages:list[str]
    status: str
    counter: int


async def main_node(state: AppState) -> dict:
    """Main processing node"""
    print(f"\n✅ Main node executing with state: {state}")
    counter = state.get("counter", 0)
    counter += 1
    response = f"Hey ini output ke {counter}"
    responses = [Message(role=Role.ASSISTANT, content=response)]
    return {
        "messages": responses,
        "status": "processing",
        "counter": counter,
    }


async def loop_node(state: AppState) -> dict:
    """Loop node"""
    print(f"✅ Loop node executing with state: {state}")
    return {"status": "completed"}


async def condition(state: AppState) -> str:
    counter = state.get("counter", 0)

    if counter == 3:
        return END
    return "loop_node"


async def example_simple_workflow():
    """Example of a simple linear workflow"""
    print("\n" + "=" * 60)
    print("Example 1: Simple Linear Workflow")
    print("=" * 60)

    flow = FlowEngine(AppState)

    # Add nodes
    flow.add_node("main_node", main_node)
    flow.add_node("loop_node", loop_node)

    # Add edges
    flow.add_edge(START, "main_node")
    flow.add_conditional_edge("main_node", ["loop_node", END], condition)
    flow.add_edge("loop_node", "main_node")

    # Build
    flow.build()

    # Visualize
    print(flow.visualize())

    # Execute
    print("\nExecuting workflow...\n")
    messages = [Message(role=Role.USER, content="Hallo")]
    result = await flow.invoke({"messages": messages, "status": "started"})

    print("\nFinal state: ")
    for msg in result['messages']:
        message = cast(Message, msg)
        print(f"\t- {message.role}: '{message.content}'")


async def run():
    await example_simple_workflow()


asyncio.run(run())
