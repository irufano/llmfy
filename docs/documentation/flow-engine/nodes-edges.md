---
title: Nodes & Edges
description: Define nodes and edges including direct, conditional, and loop patterns in FlowEngine.
---

# Nodes & Edges

## START and END

`START` and `END` are special constants that mark the entry and exit points of every workflow.

```python
from llmfy import START, END
```

Every workflow must have exactly one edge from `START` and at least one edge to `END`.

## Nodes

A node is any Python function (sync or async) that takes the current state and returns a dict of updates.

```python linenums="1"
from llmfy import FlowEngine, START, END

flow = FlowEngine(AppState)

async def my_node(state: AppState) -> dict:
    return {"status": "done"}

flow.add_node("my_node", my_node)
```

### Async vs Sync

Both async and sync node functions are supported:

```python linenums="1"
# Async node
async def async_node(state: AppState) -> dict:
    return {"status": "async"}

# Sync node
def sync_node(state: AppState) -> dict:
    return {"status": "sync"}
```

## Direct Edges

A direct edge routes unconditionally from one node to another:

```python linenums="1"
flow.add_edge(START, "node_a")
flow.add_edge("node_a", "node_b")
flow.add_edge("node_b", END)
```

This creates a simple linear workflow: `START → node_a → node_b → END`.

## Conditional Edges

A conditional edge routes to one of several nodes based on the current state. The condition function receives the state and returns the name of the next node (or `END`).

```python linenums="1"
def route(state: AppState) -> str:
    if state.get("counter", 0) < 5:
        return "low_path"
    return "high_path"

flow.add_conditional_edge(
    "check",            # source node
    ["low_path", "high_path"],  # all possible targets
    route,              # condition function
)
```

## Example: Linear Workflow

```python linenums="1"
import asyncio
from typing_extensions import TypedDict
from llmfy import FlowEngine, START, END


class AppState(TypedDict):
    result: str
    status: str


async def process(state: AppState) -> dict:
    return {"result": "processed", "status": "done"}


async def main():
    flow = FlowEngine(AppState)

    flow.add_node("process", process)
    flow.add_edge(START, "process")
    flow.add_edge("process", END)
    flow.build()

    result = await flow.invoke({"result": "", "status": "start"})
    print(result)


asyncio.run(main())
```

## Example: Conditional Workflow

```python linenums="1"
import asyncio
from typing import Annotated
from typing_extensions import TypedDict
from llmfy import FlowEngine, START, END


def add_messages(old, new):
    return (old or []) + new


class AppState(TypedDict):
    messages: Annotated[list, add_messages]
    counter: int
    status: str


async def check(state: AppState) -> dict:
    return {"status": "checked"}


async def low_path(state: AppState) -> dict:
    return {"messages": ["low"], "counter": state["counter"] + 1, "status": "low"}


async def high_path(state: AppState) -> dict:
    return {"messages": ["high"], "counter": state["counter"] + 10, "status": "high"}


def route(state: AppState) -> str:
    if state.get("counter", 0) < 5:
        return "low_path"
    return "high_path"


async def main():
    flow = FlowEngine(AppState)

    flow.add_node("check", check)
    flow.add_node("low_path", low_path)
    flow.add_node("high_path", high_path)

    flow.add_edge(START, "check")
    flow.add_conditional_edge("check", ["low_path", "high_path"], route)
    flow.add_edge("low_path", END)
    flow.add_edge("high_path", END)

    flow.build()

    result = await flow.invoke({"messages": [], "counter": 2, "status": "start"})
    print(result)  # takes low_path (counter=2 < 5)


asyncio.run(main())
```

## Loop Pattern

Route back to a previous node to create a loop, and use `END` in the condition to break out:

```python linenums="1"
def should_loop(state: AppState) -> str:
    if state.get("counter", 0) < 3:
        return "main_node"   # loop back
    return END               # exit

flow.add_node("main_node", main_node)
flow.add_edge(START, "main_node")
flow.add_conditional_edge("main_node", ["main_node", END], should_loop)
flow.build()
```
