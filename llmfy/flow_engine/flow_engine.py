import inspect
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

# Import checkpointer
from typing_extensions import Annotated

from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.flow_engine.checkpointer.base_checkpointer import (
    BaseCheckpointer,
    Checkpoint,
    CheckpointMetadata,
)
from llmfy.flow_engine.edge.edge import Edge
from llmfy.flow_engine.node.node import END, START, Node, NodeType
from llmfy.flow_engine.stream.flow_engine_stream_response import (
    FlowEngineStreamResponse,
    FlowEngineStreamType,
)
from llmfy.flow_engine.stream.node_stream_response import (
    NodeStreamResponse,
    NodeStreamType,
)
from llmfy.flow_engine.visualizer.visualizer import WorkflowVisualizer


class FlowEngine:
    """
    A workflow engine that manages state transitions through nodes and edges.

    Attributes:
        state_schema: TypedDict class defining the state structure
        nodes: Dictionary of node name to node function
        edges: Dictionary of node name to list of target nodes
        conditional_edges: Dictionary of node name to conditional routing info
        state: Current state of the workflow
        checkpointer: Optional checkpointer for state persistence
    """

    def __init__(
        self,
        state_schema: type,
        checkpointer: Optional[BaseCheckpointer] = None,
    ):
        """
        Initialize the FlowEngine with a state schema.

        Args:
            state_schema: A TypedDict class defining the state structure
            checkpointer: Optional checkpointer for state persistence
        """
        self.is_built = False
        self.state_schema = state_schema
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self.state: Dict[str, Any] = {}
        self._reducers = {}
        self._type_hints = {}  # Store type hints for deserialization

        # Checkpointer configuration
        self.checkpointer = checkpointer
        self._thread_id: Optional[str] = None
        self._step_counter: int = 0
        self._checkpoint_enabled: bool = checkpointer is not None

        # Add special START and END nodes
        self.nodes[START] = Node(name=START, node_type=NodeType.START)
        self.nodes[END] = Node(name=END, node_type=NodeType.END)

        # Extract annotations from the state schema and validate reducers
        self._extract_state_annotations()

        # Visualizer
        self.visualizer = WorkflowVisualizer()

    def _extract_state_annotations(self):
        """Extract and validate reducer functions from the state schema."""
        hints = get_type_hints(self.state_schema, include_extras=True)

        for f, hint in hints.items():
            origin = get_origin(hint)

            # Check if it's an Annotated type
            if origin is Annotated:
                args = get_args(hint)
                if len(args) >= 2:
                    # Store the actual type (first arg)
                    self._type_hints[f] = args[0]
                    # Store the reducer (second arg)
                    reducer = args[1]
                    # Validate the reducer function
                    self._validate_reducer(f, reducer)
                    self._reducers[f] = reducer
                else:
                    self._type_hints[f] = args[0] if args else hint
                    self._reducers[f] = None
            else:
                # Store the type hint directly
                self._type_hints[f] = hint
                self._reducers[f] = None

    def _validate_reducer(self, field_name: str, reducer: Callable):
        """
        Validate that a reducer function has the correct signature.

        Args:
            field_name: Name of the field this reducer is for
            reducer: The reducer function to validate

        Raises:
            LLMfyException: If the reducer doesn't have exactly 2 parameters
        """
        if not callable(reducer):
            raise LLMfyException(
                f"Reducer for field '{field_name}' must be callable, got {type(reducer)}"
            )

        sig = inspect.signature(reducer)
        params = list(sig.parameters.values())

        if len(params) != 2:
            raise LLMfyException(
                f"Reducer for field '{field_name}' must have exactly 2 parameters "
                f"(old_value, new_value), but has {len(params)} parameters"
            )

    def _deserialize_state(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deserialize state dictionary and reconstruct objects based on TypedDict schema.

        Args:
            state_dict: Dictionary with potentially serialized objects

        Returns:
            Dictionary with objects reconstructed to their proper types
        """
        deserialized = {}

        for field_name, value in state_dict.items():
            # Get the expected type for this field
            expected_type = self._type_hints.get(field_name)

            if expected_type is None:
                # No type hint available, keep as is
                deserialized[field_name] = value
                continue

            # Reconstruct the value based on expected type
            deserialized[field_name] = self._reconstruct_value(value, expected_type)

        return deserialized

    def _reconstruct_value(self, value: Any, expected_type: Any) -> Any:
        """
        Reconstruct a value to match the expected type.

        Args:
            value: The value to reconstruct (may be dict, list, or primitive)
            expected_type: The expected type from TypedDict

        Returns:
            Reconstructed value
        """
        if value is None:
            return None

        # Handle Annotated types - extract the actual type
        origin = get_origin(expected_type)
        if origin is Annotated:
            args = get_args(expected_type)
            if args:
                # First arg is the actual type
                expected_type = args[0]
                origin = get_origin(expected_type)

        # Handle List types
        if origin in (list, List):
            if not isinstance(value, list):
                return value

            # Get the element type
            args = get_args(expected_type)
            if args:
                element_type = args[0]
                # Reconstruct each element
                return [self._reconstruct_value(item, element_type) for item in value]
            return value

        # Handle Dict types
        if origin in (dict, Dict):
            if not isinstance(value, dict):
                return value

            args = get_args(expected_type)
            if len(args) >= 2:
                key_type, value_type = args[0], args[1]
                return {
                    self._reconstruct_value(k, key_type): self._reconstruct_value(
                        v, value_type
                    )
                    for k, v in value.items()
                }
            return value

        # Handle custom class objects
        if isinstance(value, dict) and hasattr(expected_type, "__mro__"):
            # Check if this looks like a serialized object
            if "__dict__" in value or self._is_serialized_object(value):
                return self._reconstruct_object(value, expected_type)

        # Handle primitive types and already correct types
        if isinstance(value, expected_type):
            return value

        # Try to cast to expected type if it's a simple type
        try:
            if expected_type in (int, float, str, bool):
                return expected_type(value)  # type: ignore
        except (LLMfyException, TypeError):
            pass

        return value

    def _is_serialized_object(self, value: dict) -> bool:
        """Check if a dict looks like a serialized object."""
        # Common patterns for serialized objects
        return (
            "__type__" in value
            or "__class__" in value
            or "__module__" in value
            or (
                isinstance(value, dict)
                and not any(k.startswith("_") for k in value.keys())
                and len(value) > 0
            )
        )

    def _reconstruct_object(self, data: dict, cls: type) -> Any:
        """
        Reconstruct an object from a dictionary.

        Args:
            data: Dictionary containing object data
            cls: The class to instantiate

        Returns:
            Reconstructed object instance
        """
        try:
            # Handle checkpointer serialization format with __type__, __module__, data
            if "__type__" in data and "__module__" in data and "data" in data:
                obj_data = data["data"]
            # Handle format with __dict__
            elif "__dict__" in data:
                obj_data = data["__dict__"]
            else:
                obj_data = data

            # Try to instantiate the class
            if hasattr(cls, "__init__"):
                # Get __init__ signature
                sig = inspect.signature(cls.__init__)
                params = list(sig.parameters.keys())[1:]  # Skip 'self'

                if len(params) == 0:
                    # No-arg constructor, set attributes after
                    obj = cls()
                    for key, value in obj_data.items():
                        if not key.startswith("_"):
                            setattr(obj, key, value)
                    return obj
                else:
                    # Try to match constructor parameters
                    init_args = {}
                    for param in params:
                        if param in obj_data:
                            init_args[param] = obj_data[param]

                    obj = cls(**init_args)

                    # Set remaining attributes
                    for key, value in obj_data.items():
                        if key not in init_args and not key.startswith("_"):
                            setattr(obj, key, value)

                    return obj
            else:
                # Fallback: create instance and set attributes
                obj = cls()
                for key, value in obj_data.items():
                    if not key.startswith("_"):
                        setattr(obj, key, value)
                return obj

        except Exception as _:
            # If reconstruction fails, return the dict
            # This allows the workflow to continue even if object reconstruction fails
            return data

    def add_node(
        self,
        name: str,
        func: Callable,
        stream: bool = False,
    ):
        """
        Add a node to the workflow.

        Args:
            name (str): Name of the node
            func (Callable): Function to execute (can be sync or async)
            stream (bool): Node is use stream or not, if node use streaming set to True. Defaults to False.
        """
        if name in [START, END]:
            raise LLMfyException(f"Cannot add node with reserved name: {name}")

        # Determine if this is a conditional node (will be set when conditional edge is added)
        node = Node(name=name, node_type=NodeType.FUNCTION, func=func, stream=stream)
        self.nodes[name] = node

    def add_edge(self, source: str, target: str):
        """
        Add an edge connecting two nodes.

        Args:
            source: Source node name (can be START)
            target: Target node name (can be END)
        """
        # Validation: START cannot be a target
        if target == START:
            raise LLMfyException("START cannot be a target node")

        # Validation: END cannot be a source
        if source == END:
            raise LLMfyException("END cannot be a source node")

        # Validation: edge cannot target itself
        if source == target:
            raise LLMfyException("Source same as target, edge cannot target itself")

        # Create edge
        edge = Edge(source=source, targets=target)
        self.edges.append(edge)

        # Update node connections
        if source in self.nodes:
            self.nodes[source].targets.append(target)
        if target in self.nodes:
            self.nodes[target].sources.append(source)

    def add_conditional_edge(
        self,
        source: str,
        targets: List[str],
        condition_func: Callable,
    ):
        """
        Add a conditional edge that routes to different nodes based on a condition.

        Args:
            source: Source node name
            targets: List of possible target nodes (can include END)
            condition_func: Function that takes state and returns target node name
        """
        # Validation: START cannot be in targets
        if START in targets:
            raise LLMfyException("START cannot be a target in conditional edges")

        # Validation: END cannot be source
        if source == END:
            raise LLMfyException("END cannot be a source node")

        # Create conditional edge
        edge = Edge(source=source, targets=targets, condition=condition_func)
        self.edges.append(edge)

        # Mark source node as conditional
        if source in self.nodes and source not in [START, END]:
            self.nodes[source].node_type = NodeType.CONDITIONAL

        # Update node connections
        if source in self.nodes:
            self.nodes[source].targets.extend(targets)
        for to_node in targets:
            if to_node in self.nodes:
                self.nodes[to_node].sources.append(source)

    def _update_state(self, updates: Dict[str, Any]):
        """
        Update the workflow state with new values.

        Uses reducer functions if available, otherwise replaces values.

        Args:
            updates: Dictionary of state updates
        """
        for key, new_value in updates.items():
            if key in self._reducers and self._reducers[key] is not None:
                # Use the reducer function
                reducer = self._reducers[key]
                old_value = self.state.get(key)
                self.state[key] = reducer(old_value, new_value)
            else:
                # Replace the value
                self.state[key] = new_value

    def _validate_workflow(self):
        """
        Validate the workflow structure before execution.

        Raises:
            LLMfyException: If the workflow has structural issues
        """
        # Validation 1: START must have at least one outgoing edge
        start_edges = [e for e in self.edges if e.source == START]
        if not start_edges:
            raise LLMfyException(
                "No edge from START node. Use flow.add_edge(START, 'node_name')"
            )

        # Validation 2: At least one path must lead to END
        end_edges = [e for e in self.edges if END in e.targets]
        if not end_edges:
            raise LLMfyException(
                "No edge to END node. At least one execution path must reach END. "
                "Use flow.add_edge('node_name', END) or include END in conditional targets."
            )

        # Collect all referenced nodes
        all_referenced_nodes = set()

        for edge in self.edges:
            # Add source (except special nodes)
            if edge.source not in [START, END]:
                all_referenced_nodes.add(edge.source)

            # Add targets (except special nodes)
            for target in edge.targets:
                if target not in [START, END]:
                    all_referenced_nodes.add(target)

        # Validation 3: All referenced nodes must be defined
        defined_nodes = set(self.nodes.keys()) - {START, END}
        undefined_nodes = all_referenced_nodes - defined_nodes
        if undefined_nodes:
            raise LLMfyException(
                f"Referenced nodes are not defined: {', '.join(sorted(undefined_nodes))}. "
                f"Use flow.add_node() to define them."
            )

        # Validation 4: Conditional edges - validate that condition function returns valid targets
        for edge in self.edges:
            if edge.condition is not None:
                # This is a conditional edge
                source_node_name = edge.source
                # valid_targets = set(edge.targets)

                # Check that all targets exist (except END)
                for target in edge.targets:
                    if target != END and target not in self.nodes:
                        raise LLMfyException(
                            f"Conditional edge from '{source_node_name}' references "
                            f"undefined target '{target}'"
                        )

                # Can't validate the return value until runtime, but we document it
                # The runtime validation happens in _get_next_node

        # Validation 5: Detect nodes with multiple non-conditional edges
        edge_counts = {}
        for edge in self.edges:
            if edge.condition is None:  # Only check non-conditional edges
                if edge.source not in edge_counts:
                    edge_counts[edge.source] = []
                edge_counts[edge.source].extend(edge.targets)

        for source, targets in edge_counts.items():
            if len(targets) > 1:
                raise LLMfyException(
                    f"Node '{source}' has multiple outgoing edges ({len(targets)}) but no conditional logic. "
                    f"Use add_conditional_edge() instead of multiple add_edge() calls."
                )

        # Warning: Detect unreachable nodes
        unreachable_nodes = defined_nodes - all_referenced_nodes
        if unreachable_nodes:
            import warnings

            warnings.warn(
                f"Some nodes are defined but not reachable: {', '.join(sorted(unreachable_nodes))}",
                UserWarning,
            )

    async def _save_checkpoint(self, node_name: str):
        """
        Save current state as a checkpoint.

        Args:
            node_name: Name of the node that just executed
        """
        if not self._checkpoint_enabled or self.checkpointer is None:
            return

        checkpoint_id = str(uuid.uuid4())
        metadata = CheckpointMetadata(
            checkpoint_id=checkpoint_id,
            thread_id=self._thread_id,  # type: ignore
            timestamp=datetime.now(timezone.utc),
            node_name=node_name,
            step=self._step_counter,
        )

        checkpoint = Checkpoint(metadata=metadata, state=deepcopy(self.state))

        await self.checkpointer.save(checkpoint)

    async def _execute_node(self, node_name: str) -> Dict[str, Any]:
        """
        Execute a node function with the current state.

        Args:
            node_name: Name of the node to execute

        Returns:
            Dictionary of state updates from the node
        """
        if node_name not in self.nodes:
            raise LLMfyException(f"Node '{node_name}' not found")

        node = self.nodes[node_name]
        func = node.func

        if func is None:
            raise LLMfyException(f"Node '{node_name}' has no function defined")

        # Check if the function is async or sync
        if inspect.iscoroutinefunction(func):
            result = await func(self.state)
        else:
            result = func(self.state)

        # Return empty dict if node doesn't return anything
        if result is None:
            return {}

        return result

    async def _execute_stream_node(self, node_name: str, func: Optional[Callable]):
        """
        Execute a stream node function with the current state.

        Args:
            node_name: Name of the node to execute
        """
        if func is None:
            raise LLMfyException(f"Node '{node_name}' has no function defined")

        # Check if the function is async generator or generator
        if inspect.isasyncgenfunction(func):
            async for chunk in func(self.state):
                if isinstance(chunk, NodeStreamResponse):
                    yield chunk
                else:
                    raise LLMfyException(
                        f"Stream response in node: '{node_name}' must use `NodeStreamResponse`"
                    )

        elif inspect.isgeneratorfunction(func):
            for chunk in func(self.state):
                if isinstance(chunk, NodeStreamResponse):
                    yield chunk
                else:
                    raise LLMfyException(
                        f"Stream response in node: '{node_name}' must use `NodeStreamResponse`"
                    )

        else:
            raise LLMfyException(
                f"Function in node: '{node_name}' is not stream. Please yield `NodeStreamResponse`."
            )

    async def _get_next_node(self, current_node: str) -> Union[str, None]:
        """
        Determine the next node to execute.

        Args:
            current_node: Current node name

        Returns:
            Next node name or None if END
        """
        # Find edges from current node
        outgoing_edges = [e for e in self.edges if e.source == current_node]

        if not outgoing_edges:
            return None

        # Should only be one edge per node (validated in _validate_workflow)
        edge = outgoing_edges[0]

        # Check if this is a conditional edge
        if edge.condition is not None:
            condition_func = edge.condition

            # Execute condition function (can be sync or async)
            if inspect.iscoroutinefunction(condition_func):
                next_node = await condition_func(self.state)
            else:
                next_node = condition_func(self.state)

            # Validate that the returned node is in the targets
            if next_node not in edge.targets:
                raise LLMfyException(
                    f"Condition function returned '{next_node}' which is not in targets: {edge.targets}"
                )

            return next_node if next_node != END else None

        # Regular edge - single target
        next_node = edge.targets[0]
        return next_node if next_node != END else None

    def build(self):
        """
        Build FlowEngine workflow.

        Returns:
            FlowEngine: Workflow built.
        """
        # Validate workflow structure before execution
        self._validate_workflow()

        # Set is built true
        self.is_built = True

        return self

    async def invoke(
        self,
        apply_state: Optional[Dict[str, Any]] = None,
        thread_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute the workflow starting from START node or continue from last checkpoint.

        Args:
            apply_state: Optional state updates to apply. If continuing from checkpoint,
                these are merged with the checkpoint state using reducers.
            thread_id: Thread ID for checkpoint management. If provided and a checkpoint
                exists, continues from last checkpoint. If None, always starts fresh.

        Returns:
            Final state after workflow execution
        """
        # Check build
        if not self.is_built:
            raise LLMfyException("Build first. Use `your_flow.build()`")

        # Set thread ID
        self._thread_id = thread_id or str(uuid.uuid4())
        self._step_counter = 0

        # Initialize state
        if apply_state is None:
            apply_state = {}

        # Try to load from last checkpoint if thread_id is provided
        loaded_checkpoint = None
        if thread_id and self.checkpointer:
            loaded_checkpoint = await self.checkpointer.load(thread_id)

        if loaded_checkpoint:
            # Continue from checkpoint - deserialize objects
            raw_state = loaded_checkpoint.state
            self.state = self._deserialize_state(raw_state)
            self._step_counter = loaded_checkpoint.metadata.step

            # Apply initial_state as updates to checkpoint state
            if apply_state:
                self._update_state(apply_state)

            # Find where to resume (next node after last completed node)
            current_node = await self._get_next_node(
                loaded_checkpoint.metadata.node_name
            )

            # If no next node (workflow was completed), start from beginning
            if current_node is None:
                start_edges = [e for e in self.edges if e.source == START]
                current_node = start_edges[0].targets[0]
        else:
            # Start fresh - no checkpoint found or no thread_id provided
            self.state = deepcopy(apply_state)

            # Find the starting node from START edges
            start_edges = [e for e in self.edges if e.source == START]
            current_node = start_edges[0].targets[0]

        # Save initial checkpoint
        if self._checkpoint_enabled:
            await self._save_checkpoint(START)

        # Execute workflow
        while current_node is not None:
            # Increment step counter
            self._step_counter += 1

            if current_node not in self.nodes:
                raise LLMfyException(f"Node '{current_node}' not found")

            node = self.nodes[current_node]

            if node.stream:
                # Handle stream node
                async for chunk in self._execute_stream_node(
                    current_node,
                    func=node.func,
                ):
                    # NodeStreamType.RESULT is always send at last stream
                    if chunk.type == NodeStreamType.RESULT:
                        # In invoke update state is in last stream result.
                        # Update state with results
                        if chunk.state:
                            self._update_state(chunk.state)

                        # Save checkpoint
                        if self._checkpoint_enabled:
                            await self._save_checkpoint(current_node)

                # Determine next node (now async)
                current_node = await self._get_next_node(current_node)

            else:
                # Handle non-streaming node
                # Execute current node
                updates = await self._execute_node(current_node)

                # Update state with results
                if updates:
                    self._update_state(updates)

                # Save checkpoint after node execution
                if self._checkpoint_enabled:
                    await self._save_checkpoint(current_node)

                # Determine next node (now async)
                current_node = await self._get_next_node(current_node)

        return self.state

    async def stream(
        self,
        apply_state: Optional[Dict[str, Any]] = None,
        thread_id: Optional[str] = None,
        stream_callback: Optional[Callable] = None,
    ):
        """
        Execute the workflow in streaming mode, starting from START node or continue from last checkpoint.

        Args:
            apply_state: Optional state updates to apply. If continuing from checkpoint,
                these are merged with the checkpoint state using reducers.
            thread_id: Thread ID for checkpoint management. If provided and a checkpoint
                exists, continues from last checkpoint. If None, always starts fresh.
            stream_callback: Optional callback function for handling streaming chunks (content only)

        Returns:
            Final state after workflow execution
        """
        # Check build
        if not self.is_built:
            raise LLMfyException("Build first. Use `your_flow.build()`")

        # Set thread ID
        self._thread_id = thread_id or str(uuid.uuid4())
        self._step_counter = 0

        # Initialize state
        if apply_state is None:
            apply_state = {}

        # Try to load from last checkpoint if thread_id is provided
        loaded_checkpoint = None
        if thread_id and self.checkpointer:
            loaded_checkpoint = await self.checkpointer.load(thread_id)

        if loaded_checkpoint:
            # Continue from checkpoint - deserialize objects
            raw_state = loaded_checkpoint.state
            self.state = self._deserialize_state(raw_state)
            self._step_counter = loaded_checkpoint.metadata.step

            # Apply apply_state as updates to checkpoint state
            if apply_state:
                self._update_state(apply_state)

            # Find where to resume (next node after last completed node)
            current_node = await self._get_next_node(
                loaded_checkpoint.metadata.node_name
            )

            # If no next node (workflow was completed), start from beginning
            if current_node is None:
                start_edges = [e for e in self.edges if e.source == START]
                current_node = start_edges[0].targets[0]
        else:
            # Start fresh - no checkpoint found or no thread_id provided
            self.state = deepcopy(apply_state)

            # Find the starting node from START edges
            start_edges = [e for e in self.edges if e.source == START]
            current_node = start_edges[0].targets[0]

        # Save initial checkpoint
        if self._checkpoint_enabled:
            await self._save_checkpoint(START)

        # START
        response = FlowEngineStreamResponse()
        response.type = FlowEngineStreamType.START
        response.node = START
        response.content = None
        response.state = self.state
        yield response

        # Execute workflow
        while current_node is not None:
            # Increment step counter
            self._step_counter += 1

            if current_node not in self.nodes:
                raise LLMfyException(f"Node '{current_node}' not found")

            node = self.nodes[current_node]

            if node.stream:
                # Handle stream node
                async for chunk in self._execute_stream_node(
                    current_node,
                    func=node.func,
                ):
                    # NodeStreamType.RESULT is always send at last stream
                    if chunk.type == NodeStreamType.RESULT:
                        # Update state with results
                        if chunk.state:
                            self._update_state(chunk.state)

                        # Save checkpoint
                        if self._checkpoint_enabled:
                            await self._save_checkpoint(current_node)

                        # NODE RESULT
                        response.type = FlowEngineStreamType.RESULT
                        response.node = current_node
                        response.content = chunk.content
                        response.state = self.state
                        yield response

                    else:
                        # Not NodeStreamType.RESULT
                        # NODE STREAM
                        response.type = FlowEngineStreamType.STREAM
                        response.node = current_node
                        response.content = chunk.content
                        response.state = self.state
                        yield response

                # Determine next node (now async)
                current_node = await self._get_next_node(current_node)

            else:
                # Handle non-streaming node
                updates = await self._execute_node(current_node)

                # Update state with results
                if updates:
                    self._update_state(updates)

                # Save checkpoint after node execution
                if self._checkpoint_enabled:
                    await self._save_checkpoint(current_node)

                # NODE RESULT
                response.type = FlowEngineStreamType.RESULT
                response.node = current_node
                response.content = updates
                response.state = self.state
                yield response

                # Determine next node (now async)
                current_node = await self._get_next_node(current_node)

    async def get_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current state for a thread from the last checkpoint.

        Args:
            thread_id: The thread ID

        Returns:
            The state if checkpoint exists, None otherwise
        """
        if not self.checkpointer:
            raise LLMfyException("No checkpointer configured")

        checkpoint = await self.checkpointer.load(thread_id)
        if checkpoint:
            # Deserialize the state to reconstruct objects
            return self._deserialize_state(checkpoint.state)
        return None

    async def list_checkpoints(
        self,
        thread_id: str,
        limit: int = 10,
    ) -> list[Checkpoint]:
        """
        List checkpoints for a specific thread.

        Args:
            thread_id: The thread ID
            limit: Maximum number of checkpoints to return

        Returns:
            List of checkpoints, newest first
        """
        if not self.checkpointer:
            raise LLMfyException("No checkpointer configured")

        return await self.checkpointer.list(thread_id, limit)

    async def get_checkpoint(
        self,
        thread_id: str,
        checkpoint_id: Optional[str] = None,
    ) -> Optional[Checkpoint]:
        """
        Get a specific checkpoint or the latest checkpoint for a thread.

        Args:
            thread_id: The thread ID
            checkpoint_id: Optional checkpoint ID, or None for latest

        Returns:
            The checkpoint if found, None otherwise
        """
        if not self.checkpointer:
            raise LLMfyException("No checkpointer configured")

        return await self.checkpointer.load(thread_id, checkpoint_id)

    async def delete_checkpoints(
        self,
        thread_id: str,
        checkpoint_id: Optional[str] = None,
    ):
        """
        Delete checkpoint(s) for a thread.

        Args:
            thread_id: The thread ID
            checkpoint_id: Optional checkpoint ID to delete, or None to delete all
        """
        if not self.checkpointer:
            raise LLMfyException("No checkpointer configured")

        await self.checkpointer.delete(thread_id, checkpoint_id)

    async def reset_thread(self, thread_id: str):
        """
        Reset a thread by deleting all its checkpoints.
        This allows starting fresh with the same thread_id.

        Args:
            thread_id: The thread ID to reset
        """
        if not self.checkpointer:
            raise LLMfyException("No checkpointer configured")

        await self.checkpointer.delete(thread_id)

    def details(self) -> str:
        """
        Generate a simple details text visualization of the workflow.

        Returns:
            String representation of the workflow graph
        """
        # Check build
        if not self.is_built:
            raise LLMfyException("Build first. Use `your_flow.build()`")

        lines = ["Workflow Graph:", "=" * 50]

        # Show START connections
        start_edges = [e for e in self.edges if e.source == START]
        for edge in start_edges:
            for target in edge.targets:
                lines.append(f"START -> {target}")

        # Show all function nodes
        function_nodes = [
            n for n in self.nodes.values() if n.node_type == NodeType.FUNCTION
        ]
        if function_nodes:
            lines.append("\nFunction Nodes:")
            for node in function_nodes:
                lines.append(f"  - {node.name}")

        # Show conditional nodes
        conditional_nodes = [
            n for n in self.nodes.values() if n.node_type == NodeType.CONDITIONAL
        ]
        if conditional_nodes:
            lines.append("\nConditional Nodes:")
            for node in conditional_nodes:
                lines.append(f"  - {node.name}")

        # Show regular edges
        regular_edges = [
            e for e in self.edges if e.condition is None and e.source != START
        ]
        if regular_edges:
            lines.append("\nRegular Edges:")
            for edge in regular_edges:
                for target in edge.targets:
                    lines.append(f"  {edge.source} -> {target}")

        # Show conditional edges
        conditional_edges = [e for e in self.edges if e.condition is not None]
        if conditional_edges:
            lines.append("\nConditional Edges:")
            for edge in conditional_edges:
                targets = ", ".join(edge.targets)
                lines.append(f"  {edge.source} ->? [{targets}]")

        return "\n".join(lines)

    def visualize(self) -> str:
        """
        Visualize workflow diagram.
        Generate Mermaid diagram url.

        Returns:
            str: Mermaid URL.
        """
        # Check build
        if not self.is_built:
            raise LLMfyException("Build first. Use `your_flow.build()`")

        mermaid_code = self.visualizer.create_mermaid_diagram(self)
        return self.visualizer.generate_diagram_url(mermaid_code)
