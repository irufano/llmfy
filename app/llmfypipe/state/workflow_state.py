from copy import deepcopy
from typing import Any, Dict, List


class WorkflowState:
    def __init__(
        self,
        initial_state: Dict[str, Any],
    ):
        self._state = initial_state or {}
        self._history: List[Dict[str, Any]] = []

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the state."""
        # Return a deep copy to prevent direct modifications
        value = self._state.get(key, default)
        return deepcopy(value)

    def get_current(self) -> Dict[str, Any]:
        """Get the current state."""
        return deepcopy(self._state)

    def _update(self, values: Dict[str, Any]) -> None:
        """Internal method to update state. Only used by Workflow class."""
        self._state.update(deepcopy(values))
        self._history.append(deepcopy(self._state))
