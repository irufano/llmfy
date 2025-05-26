import warnings
import functools
from typing import Union, Callable, Optional


def deprecated(
    reason: Optional[str] = None,
    version: Optional[str] = None,
    alternative: Optional[str] = None,
    category: type = DeprecationWarning,
) -> Callable:
    """
    Decorator to mark functions, classes, or context managers as deprecated.

    Args:
        reason: Optional reason for deprecation
        version: Version when the item was deprecated
        alternative: Suggested alternative to use instead
        category: Warning category (default: DeprecationWarning)

    Returns:
        Decorated function, class, or context manager
    """

    def decorator(obj: Union[Callable, type]) -> Union[Callable, type]:
        # Build warning message
        obj_type = "class" if isinstance(obj, type) else "function"
        obj_name = getattr(obj, "__name__", str(obj))

        msg_parts = [f"{obj_type.capitalize()} '{obj_name}' is deprecated"]

        if version:
            msg_parts.append(f"since version {version}")
        if reason:
            msg_parts.append(f"({reason})")
        if alternative:
            msg_parts.append(f"Use '{alternative}' instead")

        warning_msg = ". ".join(msg_parts) + "."

        if isinstance(obj, type):
            # Handle classes
            original_init = obj.__init__

            @functools.wraps(original_init)
            def new_init(self, *args, **kwargs):
                warnings.warn(warning_msg, category=category, stacklevel=2)
                return original_init(self, *args, **kwargs)

            obj.__init__ = new_init
            return obj

        else:
            # Handle functions and context managers
            @functools.wraps(obj)
            def wrapper(*args, **kwargs):
                warnings.warn(warning_msg, category=category, stacklevel=2)
                return obj(*args, **kwargs)

            return wrapper

    return decorator
