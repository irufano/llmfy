from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, List, Optional


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
    func: Optional[Callable] = None
    sources: List[str] = field(default_factory=list)
    targets: List[str] = field(default_factory=list)
    stream: bool = field(default=False)
