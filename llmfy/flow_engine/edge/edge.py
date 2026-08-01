from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class Edge:
    """Represents an edge in the workflow graph"""
    source: str
    targets: str | list[str]
    condition: Callable | None = None
    
    def __post_init__(self):
        """Normalize targets to always be a list"""
        if isinstance(self.targets, str):
            self.targets = [self.targets]
