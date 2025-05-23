from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, List, Optional


class NodeType(Enum):
    START = "start"
    END = "end"
    FUNCTION = "function"
    CONDITIONAL = "conditional"


# Special node identifiers
START = "START"
END = "END"


@dataclass
class Node:
    name: str
    node_type: NodeType
    func: Optional[Callable] = None
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    stream: bool = field(default=False)
