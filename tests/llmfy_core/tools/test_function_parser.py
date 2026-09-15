"""Unit tests for llmfy/llmfy_core/tools/function_parser.py."""

from llmfy.llmfy_core.tools.function_parser import FunctionParser


def with_google_docstring(location: str, unit: str = "celsius") -> str:
    """Get the current weather for a location.

    Args:
        location (str): The city and state.
        unit (str): Temperature unit.

    Returns:
        str: The weather.
    """
    return "sunny"


def with_rest_docstring(city: str) -> str:
    """Get the current weather.

    :param city: The city name.
    :returns: The weather.
    """
    return "sunny"


def with_no_docstring(x: int) -> int:
    return x


def with_one_line_docstring(x: int) -> int:
    """Just doubles a number."""
    return x * 2


class TestGetFunctionMetadata:
    def test_name(self):
        metadata = FunctionParser.get_function_metadata(with_google_docstring)
        assert metadata["name"] == "with_google_docstring"

    def test_description_stops_before_args_section_google_style(self):
        metadata = FunctionParser.get_function_metadata(with_google_docstring)
        assert metadata["description"] == "Get the current weather for a location."

    def test_description_stops_before_param_marker_rest_style(self):
        metadata = FunctionParser.get_function_metadata(with_rest_docstring)
        assert metadata["description"] == "Get the current weather."

    def test_no_docstring_gives_empty_description_and_docstring(self):
        metadata = FunctionParser.get_function_metadata(with_no_docstring)
        assert metadata["description"] == ""
        assert metadata["docstring"] == ""

    def test_one_line_docstring_with_no_sections_is_used_verbatim(self):
        metadata = FunctionParser.get_function_metadata(with_one_line_docstring)
        assert metadata["description"] == "Just doubles a number."

    def test_parameters_contains_expected_names(self):
        metadata = FunctionParser.get_function_metadata(with_google_docstring)
        assert list(metadata["parameters"].keys()) == ["location", "unit"]

    def test_type_hints_resolved(self):
        metadata = FunctionParser.get_function_metadata(with_google_docstring)
        assert metadata["type_hints"]["location"] is str
        assert metadata["type_hints"]["return"] is str

    def test_docstring_field_is_the_raw_getdoc_output(self):
        metadata = FunctionParser.get_function_metadata(with_rest_docstring)
        assert ":param city:" in metadata["docstring"]

    def test_default_value_reflected_in_signature_parameter(self):
        metadata = FunctionParser.get_function_metadata(with_google_docstring)
        assert metadata["parameters"]["unit"].default == "celsius"
        import inspect

        assert metadata["parameters"]["location"].default is inspect.Parameter.empty

    def test_bound_method_includes_self_in_parameters(self):
        class Foo:
            def bar(self, x: int) -> int:
                """Do a thing.

                Args:
                    x (int): a number.
                """
                return x

        metadata = FunctionParser.get_function_metadata(Foo.bar)
        assert "self" in metadata["parameters"]
