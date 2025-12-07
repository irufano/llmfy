from dataclasses import dataclass
from typing import Callable, List, Optional, Union


@dataclass
class Edge:
    """Represents an edge in the workflow graph"""
    source: str
    targets: Union[str, List[str]]
    condition: Optional[Callable] = None
    
    def __post_init__(self):
        """Normalize targets to always be a list"""
        if isinstance(self.targets, str):
            self.targets = [self.targets]
