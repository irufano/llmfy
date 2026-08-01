from copy import deepcopy
from typing import Any

from llmfy.llmfy_utils.deprecated.deprecated import deprecated


@deprecated(alternative='TypedDict')
class WorkflowState:
    def __init__(
        self,
        initial_state: dict[str, Any],
    ):
        self._state = initial_state or {}
        self._history: list[dict[str, Any]] = []

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the state."""
        # Return a deep copy to prevent direct modifications
        value = self._state.get(key, default)
        return deepcopy(value)

    def get_current(self) -> dict[str, Any]:
        """Get the current state."""
        return deepcopy(self._state)

    def _update(self, values: dict[str, Any]) -> None:
        """Internal method to update state. Only used by Workflow class."""
        self._state.update(deepcopy(values))
        self._history.append(deepcopy(self._state))
