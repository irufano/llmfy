"""
Examples demonstrating how to use FlowEngine with different checkpointers.
"""

import asyncio
import os
from typing import TypedDict

from dotenv import load_dotenv
from sqlalchemy.engine import URL
from typing_extensions import Annotated

from llmfy import Message
from llmfy.flow_engine.checkpointer.sql_checkpointer import SQLCheckpointer
from llmfy.flow_engine.flow_engine import FlowEngine
from llmfy.flow_engine.node.node import END, START
from llmfy.llmfy_core.messages.role import Role

load_dotenv()

# ============================================================================
# Define helper functions for state management
# ============================================================================


def add_message(old_messages, new_message):
    """Reducer function to append messages."""
    if old_messages is None:
        return new_message
    return old_messages + new_message


# ============================================================================
# Define State Schema
# ============================================================================


class AppState(TypedDict):
    """Application state with message history."""

    messages: Annotated[list[str], add_message]
    status: str
    counter: int


db_url = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv('MYSQL_USER', 'root'),
    password=os.getenv('MYSQL_PASSWORD', ''),
    host=os.getenv('MYSQL_HOST', 'localhost'),
    port=int(os.getenv('MYSQL_PORT', 3306)),
    database=os.getenv('MYSQL_DATABASE', ''),
    query={"charset": "utf8mb4"},
)

# ============================================================================
# Example 1: Automatic Continuation with Same Thread ID
# ============================================================================

async def example_automatic_continuation():
    """Example showing automatic continuation when using same session_id."""
    print("\n" + "=" * 60)
    print("Example 1: Automatic Continuation with Same Thread ID")
    print("=" * 60 + "\n")

    # Create checkpointer
    checkpointer = SQLCheckpointer(
        connection_string=db_url.render_as_string(hide_password=False),
        echo=False,  # Set to True to see SQL queries
    )

    # Create flow engine with checkpointer
    flow = FlowEngine(state_schema=AppState, checkpointer=checkpointer)

    # Define nodes
    def step1(state):
        print(
            f"  Step 1: counter={state.get('counter', 0)}, status={state.get('status', 'N/A')}"
        )
        return {
            "messages": ["Completed step 1"],
            "counter": state.get("counter", 0) + 1,
            "status": "step1_done",
        }

    def step2(state):
        print(f"  Step 2: counter={state['counter']}, status={state['status']}")
        return {
            "messages": ["Completed step 2"],
            "counter": state["counter"] + 1,
            "status": "step2_done",
        }

    def step3(state):
        print(f"  Step 3: counter={state['counter']}, status={state['status']}")
        return {
            "messages": ["Completed step 3"],
            "counter": state["counter"] + 1,
            "status": "completed",
        }

    # Build workflow
    flow.add_node("step1", step1)
    flow.add_node("step2", step2)
    flow.add_node("step3", step3)
    flow.add_edge(START, "step1")
    flow.add_edge("step1", "step2")
    flow.add_edge("step2", "step3")
    flow.add_edge("step3", END)
    flow.build()

    # First invocation - starts fresh
    print("🚀 First invocation (fresh start):")
    session_id = "user-123"
    initial_state = {"messages": [], "status": "started", "counter": 0}

    final_state = await flow.invoke(initial_state, session_id=session_id)
    print("\n✅ First run completed:")
    print(f"   Messages: {final_state['messages']}")
    print(f"   Counter: {final_state['counter']}")
    print(f"   Status: {final_state['status']}")

    # Second invocation - continues from checkpoint with same session_id
    print("\n\n🔄 Second invocation (same session_id - continues from checkpoint):")
    initial_state = {
        "messages": ["Starting continuation"],
        "status": "continuing",
        "counter": 100,  # This will be added/updated based on reducer
    }

    final_state = await flow.invoke(initial_state, session_id=session_id)
    print("\n✅ Second run completed:")
    print(f"   Messages: {final_state['messages']}")
    print(f"   Counter: {final_state['counter']}")
    print(f"   Status: {final_state['status']}")

    # Third invocation - different session_id (fresh start)
    print("\n\n🆕 Third invocation (different session_id - fresh start):")
    new_thread_id = "user-456"
    initial_state = {"messages": [], "status": "fresh_start", "counter": 0}

    final_state = await flow.invoke(initial_state, session_id=new_thread_id)
    print("\n✅ Third run completed:")
    print(f"   Messages: {final_state['messages']}")
    print(f"   Counter: {final_state['counter']}")
    print(f"   Status: {final_state['status']}")


# ============================================================================
# Example 2: Reducer Behavior with Continuation
# ============================================================================


async def example_reducer_behavior():
    """Example showing how reducers work during continuation."""
    print("\n" + "=" * 60)
    print("Example 2: Reducer Behavior with Continuation")
    print("=" * 60 + "\n")

    checkpointer = SQLCheckpointer(
        connection_string=db_url.__to_string__(hide_password=False),
        echo=False,  # Set to True to see SQL queries
    )
    flow = FlowEngine(state_schema=AppState, checkpointer=checkpointer)

    def process(state):
        return {
            "messages": [f"Processed at counter={state.get('counter', 0)}"],
            "counter": state.get("counter", 0) + 1,
            "status": "processed",
        }

    flow.add_node("process", process)
    flow.add_edge(START, "process")
    flow.add_edge("process", END)
    flow.build()

    session_id = "demo-reducers"

    # First run
    print("Run 1: Initial state")
    state1 = await flow.invoke(
        {"messages": [], "status": "start", "counter": 0}, session_id=session_id
    )
    print(f"  Messages (with reducer): {state1['messages']}")
    print(f"  Status (no reducer): {state1['status']}")
    print(f"  Counter (no reducer): {state1['counter']}")

    # Second run - messages append, others replace
    print("\nRun 2: Continue with updates")
    state2 = await flow.invoke(
        {"messages": ["New message"], "status": "updated", "counter": 50},
        session_id=session_id,
    )
    print(f"  Messages (APPENDED with reducer): {state2['messages']}")
    print(f"  Status (REPLACED, no reducer): {state2['status']}")
    print(f"  Counter (REPLACED, no reducer): {state2['counter']}")

    # Third run - with empty updates
    print("\nRun 3: Continue without updates")
    state3 = await flow.invoke(None, session_id=session_id)
    print(f"  Messages: {state3['messages']}")
    print(f"  Status: {state3['status']}")
    print(f"  Counter: {state3['counter']}")


# ============================================================================
# Example 3: Reset Thread to Start Fresh
# ============================================================================


async def example_reset_thread():
    """Example showing how to reset a thread."""
    print("\n" + "=" * 60)
    print("Example 3: Reset Thread to Start Fresh")
    print("=" * 60 + "\n")

    checkpointer = SQLCheckpointer(
        connection_string=db_url.__to_string__(hide_password=False),
        echo=False,  # Set to True to see SQL queries
    )
    flow = FlowEngine(state_schema=AppState, checkpointer=checkpointer)

    def process(state):
        return {
            "messages": ["Processed"],
            "counter": state.get("counter", 0) + 1,
            "status": "done",
        }

    flow.add_node("process", process)
    flow.add_edge(START, "process")
    flow.add_edge("process", END)
    flow.build()

    session_id = "user-reset-demo"

    # First run
    print("Run 1: First execution")
    state1 = await flow.invoke(
        {"messages": [], "status": "start", "counter": 0}, session_id=session_id
    )
    print(f"  Counter: {state1['counter']}, Status: {state1['status']}")

    # Continue (would add to checkpoint)
    print("\nRun 2: Continue from checkpoint")
    state2 = await flow.invoke(None, session_id=session_id)
    print(f"  Counter: {state2['counter']}, Status: {state2['status']}")

    # Reset the thread
    print("\n🔄 Resetting thread...")
    await flow.reset_session(session_id)

    # After reset, starts fresh
    print("\nRun 3: After reset (fresh start)")
    state3 = await flow.invoke(
        {"messages": [], "status": "fresh", "counter": 0}, session_id=session_id
    )
    print(f"  Counter: {state3['counter']}, Status: {state3['status']}")


# ============================================================================
# Example 4: Checking State Before Invocation
# ============================================================================


async def example_check_state():
    """Example showing how to check state before invocation."""
    print("\n" + "=" * 60)
    print("Example 4: Checking State Before Invocation")
    print("=" * 60 + "\n")

    checkpointer = SQLCheckpointer(
        connection_string=db_url.__to_string__(hide_password=False),
        echo=False,  # Set to True to see SQL queries
    )
    flow = FlowEngine(state_schema=AppState, checkpointer=checkpointer)

    def process(state):
        return {
            "messages": ["Processed"],
            "counter": state.get("counter", 0) + 1,
            "status": "done",
        }

    flow.add_node("process", process)
    flow.add_edge(START, "process")
    flow.add_edge("process", END)
    flow.build()

    session_id = "check-state-demo"

    # Check state before any execution
    print("Checking state before execution...")
    state = await flow.get_state(session_id)
    print(f"  State: {state}")

    # First run
    print("\nRun 1: First execution")
    await flow.invoke(
        {"messages": [], "status": "start", "counter": 0}, session_id=session_id
    )

    # Check state after execution
    print("\nChecking state after execution...")
    state = await flow.get_state(session_id)
    print(f"  State: {state}")

    # Check if we should continue or start fresh
    if state and state.get("status") == "done":
        print("\n✅ Workflow already completed. Starting fresh with reset...")
        await flow.reset_session(session_id)
        await flow.invoke(
            {"messages": [], "status": "restart", "counter": 0}, session_id=session_id
        )
    else:
        print("\n🔄 Continuing from checkpoint...")
        await flow.invoke(None, session_id=session_id)


# ============================================================================
# Example 5: Multi-Step Workflow with Updates
# ============================================================================


async def example_multistep_updates():
    """Example showing multi-step workflow with updates at each continuation."""
    print("\n" + "=" * 60)
    print("Example 5: Multi-Step Workflow with Updates")
    print("=" * 60 + "\n")

    checkpointer = SQLCheckpointer(
        connection_string=db_url.__to_string__(hide_password=False),
        echo=False,  # Set to True to see SQL queries
    )
    flow = FlowEngine(state_schema=AppState, checkpointer=checkpointer)

    def step1(state):
        print(f"  Step 1: {state.get('status', 'N/A')}")
        return {"messages": ["Step 1"], "counter": 1, "status": "step1"}

    def step2(state):
        print(f"  Step 2: {state.get('status', 'N/A')}")
        return {"messages": ["Step 2"], "counter": 2, "status": "step2"}

    def step3(state):
        print(f"  Step 3: {state.get('status', 'N/A')}")
        return {"messages": ["Step 3"], "counter": 3, "status": "step3"}

    flow.add_node("step1", step1)
    flow.add_node("step2", step2)
    flow.add_node("step3", step3)
    flow.add_edge(START, "step1")
    flow.add_edge("step1", "step2")
    flow.add_edge("step2", "step3")
    flow.add_edge("step3", END)
    flow.build()

    session_id = "multistep-demo"

    # Execute in parts with different status updates
    print("Execution 1: Starting workflow")
    state = await flow.invoke(
        {"messages": [], "status": "initializing", "counter": 0}, session_id=session_id
    )
    print(f"  Final: {state}")

    print("\nExecution 2: Continue with status update")
    state = await flow.invoke({"status": "continuing phase 2"}, session_id=session_id)
    print(f"  Final: {state}")

    print("\nExecution 3: Continue with message addition")
    state = await flow.invoke({"messages": ["Additional info"]}, session_id=session_id)
    print(f"  Final: {state}")
    print(f"  All messages: {state['messages']}")


# ============================================================================
# Example 6: Conditional Workflow with Continuation
# ============================================================================


async def example_conditional_continuation():
    """Example showing conditional workflow with continuation."""
    print("\n" + "=" * 60)
    print("Example 6: Conditional Workflow with Continuation")
    print("=" * 60 + "\n")

    checkpointer = SQLCheckpointer(
        connection_string=db_url.__to_string__(hide_password=False),
        echo=False,  # Set to True to see SQL queries
    )
    flow = FlowEngine(state_schema=AppState, checkpointer=checkpointer)

    def check(state):
        print(f"  Checking: counter={state.get('counter', 0)}")
        return {"messages": ["Checked"], "status": "checked"}

    def path_low(state):
        print("  Taking LOW path")
        return {
            "messages": ["Path: LOW"],
            "counter": state["counter"] + 1,
            "status": "path_low",
        }

    def path_high(state):
        print("  Taking HIGH path")
        return {
            "messages": ["Path: HIGH"],
            "counter": state["counter"] + 10,
            "status": "path_high",
        }

    def finalize(state):
        print("  Finalizing")
        return {"messages": ["Finalized"], "status": "done"}

    def route(state):
        if state.get("counter", 0) < 5:
            return "path_low"
        return "path_high"

    flow.add_node("check", check)
    flow.add_node("path_low", path_low)
    flow.add_node("path_high", path_high)
    flow.add_node("finalize", finalize)

    flow.add_edge(START, "check")
    flow.add_conditional_edge("check", ["path_low", "path_high"], route)
    flow.add_edge("path_low", "finalize")
    flow.add_edge("path_high", "finalize")
    flow.add_edge("finalize", END)
    flow.build()

    session_id = "conditional-demo"

    # First run with low counter
    print("Run 1: counter=2 (should take LOW path)")
    state = await flow.invoke(
        {"messages": [], "status": "start", "counter": 2}, session_id=session_id
    )
    print(f"  Result: {state}\n")

    # Continue - since workflow completed, restarts from beginning
    print("Run 2: Continue (workflow was complete, restarts)")
    state = await flow.invoke(
        {"counter": 7},  # High counter this time
        session_id=session_id,
    )
    print(f"  Result: {state}\n")


# ============================================================================
# Example 7: Complex state containing custom objects.
# ============================================================================


# class Message:
#     """Custom message class."""

#     def __init__(self, role: str, content: str):
#         self.role = role
#         self.content = content

#     def __repr__(self):
#         return f"Message(role='{self.role}', content='{self.content}')"


def add_message_objects(old_messages, new_message):
    """Reducer for Message objects."""
    if old_messages is None:
        return new_message
    return old_messages + new_message


class ComplexState(TypedDict):
    """State with custom objects."""

    messages: Annotated[list[Message], add_message_objects]
    metadata: dict


async def example_complex_state():
    """Example with complex state containing custom objects."""
    print("\n" + "=" * 60)
    print("Example 7: Complex State with Custom Objects")
    print("=" * 60 + "\n")

    checkpointer = SQLCheckpointer(
        connection_string=db_url.__to_string__(hide_password=False),
        echo=False,  # Set to True to see SQL queries
    )
    flow = FlowEngine(state_schema=ComplexState, checkpointer=checkpointer)

    def add_user_message(state):
        return {
            "messages": [Message(role=Role.USER, content="Hello, assistant!")],
            "metadata": {"timestamp": "2024-01-01"},
        }

    def add_assistant_message(state):
        return {
            "messages": [
                Message(role=Role.ASSISTANT, content="Hello! How can I help?")
            ],
        }

    flow.add_node("user_msg", add_user_message)
    flow.add_node("assistant_msg", add_assistant_message)

    flow.add_edge(START, "user_msg")
    flow.add_edge("user_msg", "assistant_msg")
    flow.add_edge("assistant_msg", END)

    flow.build()

    print("RUN 1:")
    initial_state = {"messages": [], "metadata": {}}
    final_state = await flow.invoke(initial_state, session_id="complex-001")

    print("Messages in final state:")
    for msg in final_state["messages"]:
        print(f"  {msg}")

    print(f"\nMetadata: {final_state['metadata']}")

    print("RUN 2:")
    final_state = await flow.invoke(
        {
            "messages": [Message(role=Role.USER, content="Apa kabar?")],
        },
        session_id="complex-001",
    )

    print("Messages in final state:")
    for msg in final_state["messages"]:
        print(f"  {msg}")

    print(f"\nMetadata: {final_state['metadata']}")

    print("\n✓ Complex state example completed!")


# ============================================================================
# Main execution
# ============================================================================


async def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("FlowEngine Automatic Continuation Examples")
    print("=" * 60)

    # Run examples
    # await example_automatic_continuation()
    # await example_reducer_behavior()
    # await example_reset_thread()
    # await example_check_state()
    # await example_multistep_updates()
    # await example_conditional_continuation()
    await example_complex_state()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
