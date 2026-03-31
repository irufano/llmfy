---
title: Overview
description: State-based workflow orchestrator for building LLM-powered pipelines.
---

# FlowEngine

FlowEngine is a state-based workflow orchestrator for building LLM-powered pipelines. It lets you define a graph of nodes (processing steps) connected by edges (transitions), manage shared state across nodes, and optionally persist state across sessions with checkpointers.

## Key Concepts

| Concept | Description |
|---------|-------------|
| **State** | A `TypedDict` shared across all nodes. Each node reads from state and returns updates. |
| **Node** | A Python function (sync or async) that processes state and returns a dict of updates. |
| **Edge** | A connection between two nodes. Can be direct or conditional. |
| **START / END** | Special constants marking the entry and exit of the workflow. |
| **Checkpointer** | Optional backend that saves state after each node so sessions can resume. |

## Installation

FlowEngine state requires the `typing_extensions` package:

=== "UV"
    
    ```shell
    uv add "llmfy[typing_extensions]"
    ```

=== "pip"
    
    ```shell
    pip install "llmfy[typing_extensions]"
    ```

## Quick Start

```python linenums="1"
import asyncio
from typing import Annotated
from typing_extensions import TypedDict
from llmfy import FlowEngine, START, END


def add_messages(old: list, new: list) -> list:
    if old is None:
        return new
    return old + new


class AppState(TypedDict):
    messages: Annotated[list[str], add_messages]
    status: str


async def step_one(state: AppState) -> dict:
    return {"messages": ["step one done"], "status": "step1"}


async def step_two(state: AppState) -> dict:
    return {"messages": ["step two done"], "status": "step2"}


async def main():
    flow = FlowEngine(AppState)

    flow.add_node("step_one", step_one)
    flow.add_node("step_two", step_two)

    flow.add_edge(START, "step_one")
    flow.add_edge("step_one", "step_two")
    flow.add_edge("step_two", END)

    flow.build()

    result = await flow.invoke({"messages": [], "status": "start"})
    print(result)


asyncio.run(main())
```

## FlowEngine API

```python
from llmfy import FlowEngine
```

| Method | Description |
|--------|-------------|
| `FlowEngine(state_schema, checkpointer=None)` | Create engine with a TypedDict state schema and optional checkpointer |
| `add_node(name, func, stream=False)` | Add a processing node. Set `stream=True` for generator nodes |
| `add_edge(source, target)` | Add a direct transition between nodes |
| `add_conditional_edge(source, targets, condition)` | Add conditional routing: `condition(state) -> str` returns the next node name |
| `build()` | Validate and compile the workflow. Returns the built `FlowEngine` |
| `invoke(apply_state, session_id=None)` | Run the workflow synchronously. Returns the final state dict |
| `stream(apply_state, session_id=None)` | Run the workflow with streaming. Returns an async generator of `FlowEngineStreamResponse` |
| `get_state(session_id)` | Retrieve the latest checkpointed state for a session |
| `reset_session(session_id)` | Clear all checkpoints for a session (start fresh) |
| `list_checkpoints(session_id, limit=10)` | List checkpoint metadata for a session |
| `details()` | Print a text representation of the workflow graph |
| `visualize()` | Return a Mermaid diagram URL for the workflow |

## Visualization

After calling `build()`, inspect or visualize the workflow:

```python linenums="1"
flow.build()

# Text representation
print(flow.details())

# Mermaid diagram URL
print(flow.visualize())
```
