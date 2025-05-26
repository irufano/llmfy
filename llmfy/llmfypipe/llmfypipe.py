import base64
import inspect
from typing import Any, Callable, Dict, List, Optional, Union, AsyncGenerator

from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.llmfypipe.edge.edge import Edge
from llmfy.llmfypipe.node.node import END, START, Node, NodeType
from llmfy.llmfypipe.state.memory_manager import MemoryManager
from llmfy.llmfypipe.state.workflow_state import WorkflowState
from llmfy.llmfypipe.visualizer.visualizer import WorkflowVisualizer


class LLMfyPipe:
    def __init__(
        self,
        initial_state: Optional[Dict[str, Any]] = None,
        memory: Optional[MemoryManager] = None,
    ):
        self.nodes: Dict[str, Node] = {
            START: Node(name=START, node_type=NodeType.START),
            END: Node(name=END, node_type=NodeType.END),
        }
        self.edges: List[Edge] = []
        self.state = WorkflowState(initial_state or {})
        self.visualizer = WorkflowVisualizer()
        self.memory = memory

    def validate_workflow(self) -> bool:
        """
        Validate the workflow structure.
        Ensures START has outgoing edges and END has incoming edges.
        """
        start_has_edge = False
        end_has_edge = False

        for edge in self.edges:
            if edge.source == START:
                start_has_edge = True
            if END in edge.targets:
                end_has_edge = True

        if not start_has_edge:
            raise ValueError("Workflow must have at least one edge from START")
        if not end_has_edge:
            raise ValueError("Workflow must have at least one edge to END")

        return True

    def add_node(
        self,
        name: str,
        func: Callable,
        node_type: NodeType = NodeType.FUNCTION,
        stream: bool = False,
    ) -> None:
        """
        Add a node to the workflow.
        Set is_streaming=True for nodes that return streaming content.

        Args:
            name (str): Node name
            func (Callable): Node description
            node_type (NodeType, optional): Node type. Defaults to NodeType.FUNCTION.
            stream (bool, optional): Node is use stream or not, if node use streaming set to True. Defaults to False.

        Raises:
            ValueError: _description_

        Returns:
            _type_: _description_
        """
        if name in (START, END):
            raise ValueError(f"Cannot add node with reserved name {name}")

        # Modify the function to include state access
        original_func = func

        async def wrapped_func(*args, **kwargs):
            sig = inspect.signature(original_func)
            if "state" in sig.parameters:
                kwargs["state"] = self.state

            if inspect.iscoroutinefunction(original_func):
                return await original_func(*args, **kwargs)
            return original_func(*args, **kwargs)

        wrapped_func.__signature__ = inspect.signature(original_func)  # type: ignore
        wrapped_func.__annotations__ = original_func.__annotations__

        sig = inspect.signature(original_func)
        inputs = list(sig.parameters.keys())

        outputs = []
        if sig.return_annotation != inspect.Signature.empty:
            if hasattr(sig.return_annotation, "__annotations__"):
                outputs = list(sig.return_annotation.__annotations__.keys())

        node = Node(
            name=name,
            node_type=node_type,
            func=wrapped_func,
            inputs=inputs,
            outputs=outputs,
            stream=stream,
        )
        self.nodes[name] = node

    def add_edge(self, source: str, target: str) -> None:
        """Add a direct edge between nodes."""
        if source not in self.nodes:
            raise ValueError(f"Source node '{source}' not found")
        if target not in self.nodes:
            raise ValueError(f"Target node '{target}' not found")

        edge = Edge(source=source, targets=[target])
        self.edges.append(edge)

    def add_conditional_edge(
        self, source: str, targets: Union[str, List[str]], condition: Callable
    ) -> None:
        """Add a conditional edge with multiple possible targets."""
        if source not in self.nodes:
            raise ValueError(f"Source node '{source}' not found")

        target_list = [targets] if isinstance(targets, str) else targets

        for target in target_list:
            if target not in self.nodes:
                raise ValueError(f"Target node '{target}' not found")

        original_condition = condition

        def wrapped_condition(*args, **kwargs):
            result = original_condition(self.state)
            if result not in target_list and result != END:
                raise ValueError(
                    f"Condition returned '{result}' which is not in targets: {target_list}"
                )
            return result

        edge = Edge(source=source, targets=target_list, condition=wrapped_condition)
        self.edges.append(edge)

    def _handle_state_update(self, additional_state, thread_id=None):
        updated_state = (
            self.memory.update_memory(thread_id, additional_state)
            if self.memory and thread_id
            else additional_state
        )
        self.state._update(updated_state)

    async def execute(
        self,
        additional_state: Dict[str, Any],
        thread_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute the workflow in standard (non-streaming) mode.

        Args:
            additional_state: Initial state to add to the workflow
            thread_id: Optional thread ID for memory management

        Returns:
            The final workflow state
        """
        try:
            # validate thread_id
            if self.memory and not thread_id:
                raise LLMfyException(
                    "`thread_id` required because workflow has memory."
                )

            if additional_state:
                self._handle_state_update(additional_state, thread_id)
                # if self.memory and thread_id:
                #     # using memory
                #     self.state._update(
                #         self.memory.update_memory(thread_id, additional_state)
                #     )
                # else:
                #     self.state._update(additional_state)

            # Validate workflow before execution
            self.validate_workflow()

            nodes_to_process = [START]
            # processed_nodes = set()

            while nodes_to_process:
                current_node = nodes_to_process.pop(0)
                if current_node == END:
                    continue

                if current_node != START:
                    node = self.nodes[current_node]

                    try:
                        func_inputs = {
                            input_name: self.state.get(input_name)
                            for input_name in node.inputs
                            if input_name != "state"
                            and input_name in self.state.get_current()
                        }

                        if node.func:
                            result = await node.func(**func_inputs)
                            # print(f"execute@LLMfyPipe result: {result}")
                            if isinstance(result, dict):
                                self._handle_state_update(result, thread_id)
                                # self.state._update(result)
                            elif len(node.outputs) == 1:
                                self._handle_state_update(
                                    {node.outputs[0]: result}, thread_id
                                )
                                # self.state._update({node.outputs[0]: result})

                    except Exception as e:
                        raise LLMfyException(
                            f"Error executing node {current_node}: {str(e)}"
                        )

                # Get next nodes
                next_nodes = []
                for edge in self.edges:
                    if edge.source == current_node:
                        if edge.condition is None:
                            next_nodes.extend(edge.targets)
                        else:
                            target = edge.condition()
                            if target and target != END:
                                next_nodes.append(target)

                nodes_to_process.extend(next_nodes)

            return self.state.get_current()
        except Exception as e:
            raise LLMfyException(e)

    async def stream(
        self,
        additional_state: Dict[str, Any],
        thread_id: Optional[str] = None,
        stream_callback: Optional[Callable] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute the workflow in streaming mode, yielding results as they become available.

        Args:
            additional_state: Initial state to add to the workflow
            thread_id: Optional thread ID for memory management
            stream_callback: Optional callback function for handling streaming chunks (content only)

        Returns:
            An async generator yielding state and event updates
        """
        try:
            # validate thread_id
            if self.memory and not thread_id:
                raise LLMfyException(
                    "`thread_id` required because workflow has memory."
                )

            if additional_state:
                updated_state = self._handle_state_update(additional_state, thread_id)
                yield {"type": "state_update", "state": updated_state}

            # Validate workflow before execution
            self.validate_workflow()
            yield {"type": "workflow_start"}

            nodes_to_process = [START]

            while nodes_to_process:
                current_node = nodes_to_process.pop(0)

                if current_node == END:
                    yield {"type": "node_complete", "node": END}
                    continue

                yield {"type": "node_start", "node": current_node}

                if current_node != START:
                    node = self.nodes[current_node]

                    try:
                        func_inputs = {
                            input_name: self.state.get(input_name)
                            for input_name in node.inputs
                            if input_name != "state"
                            and input_name in self.state.get_current()
                        }

                        if node.func:
                            if node.stream:
                                # Handle streaming node
                                async for chunk in await node.func(**func_inputs):
                                    if isinstance(chunk, dict):
                                        # Update state
                                        updated_state = self._handle_state_update(
                                            chunk, thread_id
                                        )
                                        yield {
                                            "type": "node_result",
                                            "node": current_node,
                                            "result": chunk,
                                            "state": updated_state,
                                        }

                                    else:
                                        # For raw non-dict chunks (like string tokens)
                                        yield {
                                            "type": "stream_chunk",
                                            "node": current_node,
                                            "content": chunk,
                                        }

                                        if stream_callback:
                                            await stream_callback(chunk)
                            else:
                                # Handle non-streaming node
                                result = await node.func(**func_inputs)
                                if isinstance(result, dict):
                                    updated_state = self._handle_state_update(
                                        result, thread_id
                                    )
                                    yield {
                                        "type": "node_result",
                                        "node": current_node,
                                        "result": result,
                                        "state": updated_state,
                                    }
                                elif len(node.outputs) == 1:
                                    result_dict = {node.outputs[0]: result}
                                    updated_state = self._handle_state_update(
                                        result_dict, thread_id
                                    )
                                    yield {
                                        "type": "node_result",
                                        "node": current_node,
                                        "result": result_dict,
                                        "state": updated_state,
                                    }

                    except Exception as e:
                        error_msg = f"Error executing node {current_node}: {str(e)}"
                        yield {
                            "type": "error",
                            "node": current_node,
                            "error": error_msg,
                        }
                        raise LLMfyException(error_msg)

                yield {"type": "node_complete", "node": current_node}

                # Get next nodes
                next_nodes = []
                for edge in self.edges:
                    if edge.source == current_node:
                        if edge.condition is None:
                            next_nodes.extend(edge.targets)
                        else:
                            target = edge.condition()
                            if target and target != END:
                                next_nodes.append(target)

                nodes_to_process.extend(next_nodes)
                yield {"type": "next_nodes", "nodes": next_nodes}

            yield {"type": "workflow_complete", "state": self.state.get_current()}
        except Exception as e:
            yield {"type": "workflow_error", "error": str(e)}
            raise LLMfyException(e)

    def get_diagram_code(self) -> str:
        """Get code for the workflow diagram."""
        return self.visualizer.create_mermaid_diagram(self)

    def get_diagram_base64(self):
        """Generate Mermaid diagram base64 for the workflow.

        Display with:
        ```py
        display(Image(url=your_diagram_url))
        ```
        """

        def get_base64(graph):
            graphbytes = graph.encode("utf8")
            base64_bytes = base64.urlsafe_b64encode(graphbytes)
            base64_string = base64_bytes.decode("ascii")
            return base64_string

        mermaid_code = self.get_diagram_code()
        return get_base64(
            f"""
			 {mermaid_code}
			 """
        )

    def get_diagram_url(self):
        """Generate Mermaid diagram url for the workflow.

        Display with:
        ```py
        display(Image(url=your_diagram_url))
        ```
        """

        def get_url(graph):
            graphbytes = graph.encode("utf8")
            base64_bytes = base64.urlsafe_b64encode(graphbytes)
            base64_string = base64_bytes.decode("ascii")
            return "https://mermaid.ink/img/" + base64_string

        mermaid_code = self.get_diagram_code()
        return get_url(
            f"""
			 {mermaid_code}
			 """
        )
