Create workflow class name FlowEngine like langgraph style using python,
The features:
1. Has dynamic state with TypedDict, State can be updated when workflow excecute. Can handle annotated type, if using annotated behaviour update use the annotated function, else do update/replace last state. 

  - Example initiate state:
    ```py
    def add_message(old, new):
        return old + new

    class AppState(TypedDict):
        messages: Annotated[list[str], add_message]
        status: str

    flow = FlowEngine(AppState)
    ```

3. Has special node START and END.
   
4. Add node, node is function. in node has args state that define at initiate. Can handle async or sync function.
   - Example add node:
    ```py
    async def main_node(state: AppState) -> dict:
        # some logic
        # if return property of state they will be updated else no update
        return {"messages": messages, "status": "success"}

    flow.add_node("main_node", main_node)
    ```
5. Add edge, edge is connection between node.
   - Example add edge:
    ```py
    flow.add_edge(START, "main_node")
    ```
6. Add conditional edge.
   - Example:
    ```py
    async def node_tools(state: AppState) -> dict:
        # some logic
        return {"messages": messages}

    def should_continue(state: AppState) -> str:
        # some logic
        if last_message.tool_calls:
            return "tools"
        return END

    flow.add_node("main_node", main_node)
    flow.add_node("tools", node_tools)

    flow.add_edge(START, "main_node")
    
    # arg 1: start name node 
    # arg 2: target name node
    # arg 3: conditional function
    flow.add_conditional_edge("main_node", ["tools", END], should_continue)
    
    flow.add_edge("tools", "main_node")
    
    ```
7. can execute flow:
   - Example:
    ```py
    res = await workflow.execute(
        {
            "messages": [
               "hello"
            ]
        }
    )
    ```


Make updates:
- add validation on _validate_workflow must have START and END edge.
- add validation on _validate_workflow for add_conditional_edge on to_nodes if condition_func has no return to_nodes, function must return in to_nodes.
- add validation on _validate_workflow node cannot add edges to node itself, e.g: flow.add_edge("node_a", "node_a")
- add validation on _validate_workflow START cannot add into end edges, and END cannor add into beginning edge
- Make Node and edge as class:
    ```py
    class NodeType(Enum):
        START = "start"
        END = "end"
        FUNCTION = "function"
        CONDITIONAL = "conditional"

    @dataclass
    class Node:
        name: str
        node_type: NodeType
        func: Optional[Callable] = None
        inputs: List[str] = field(default_factory=list)
        outputs: List[str] = field(default_factory=list)

    @dataclass
    class Edge:
        source: str
        targets: Union[str, List[str]]
        condition: Optional[Callable] = None
        
        def __post_init__(self):
            if isinstance(self.targets, str):
                self.targets = [self.targets]
    ```