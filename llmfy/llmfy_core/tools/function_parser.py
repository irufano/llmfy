import inspect
import re
from collections.abc import Callable
from typing import get_type_hints


class FunctionParser:
    """Extracts metadata from a function."""

    @staticmethod
    def get_function_metadata(func: Callable) -> dict:
        """Extracts metadata from the given function."""
        docstring = inspect.getdoc(func) or ""
        signature = inspect.signature(func)
        parameters = signature.parameters
        type_hints = get_type_hints(func)

        # Extract short description (accept Google, reST and Sphinx style)
        desc_match = re.search(
            r"^(.*?)(?:\n\s*(?:Args|Arguments|Parameters|Returns?|Raises?|Yields?|Examples?|Attributes?|Notes?|Warnings?):|\n\s*:(?:param|returns?|rtype|raises?|type|var|ivar|cvar)\s)",
            docstring,
            re.DOTALL,
        )
        description = desc_match.group(1).strip() if desc_match else docstring

        return {
            "name": func.__name__,
            "description": description,
            "parameters": parameters,
            "type_hints": type_hints,
            "docstring": docstring,
        }
