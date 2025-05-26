import inspect
import re
from typing import Callable, Dict, get_type_hints


class FunctionParser:
    """Extracts metadata from a function."""

    @staticmethod
    def get_function_metadata(func: Callable) -> Dict:
        """Extracts metadata from the given function."""
        docstring = inspect.getdoc(func) or ""
        signature = inspect.signature(func)
        parameters = signature.parameters
        type_hints = get_type_hints(func)

        # Extract short description
        desc_match = re.search(
            r"^(.*?)(?:\n\s*(Args|Parameters):)", docstring, re.DOTALL
        )
        description = desc_match.group(1).strip() if desc_match else docstring

        return {
            "name": func.__name__,
            "description": description,
            "parameters": parameters,
            "type_hints": type_hints,
            "docstring": docstring,
        }
