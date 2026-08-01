from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum


class NodeType(Enum):
    """Types of nodes in the workflow"""
    START = "start"
    END = "end"
    FUNCTION = "function"
    CONDITIONAL = "conditional"



# Special node identifiers
START = "__start__"
END = "__end__"


@dataclass
class Node:
    """Represents a node in the workflow graph"""
    name: str
    node_type: NodeType
    func: Callable | None = None
    sources: list[str] = field(default_factory=list)
    targets: list[str] = field(default_factory=list)
    stream: bool = field(default=False)
