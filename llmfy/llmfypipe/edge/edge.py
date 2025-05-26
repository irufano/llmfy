from dataclasses import dataclass
from typing import Callable, List, Optional, Union


@dataclass
class Edge:
    source: str
    targets: Union[str, List[str]]
    condition: Optional[Callable] = None
    
    def __post_init__(self):
        if isinstance(self.targets, str):
            self.targets = [self.targets]