"""Unit tests for llmfy/llmfy_core/tools/function_param_desc_extractor.py.

Fixture docstrings mirror the 3 styles demonstrated in
llmfy/example/tool_calling_example.py (Google, reST, Sphinx-with-type).
"""

from llmfy.llmfy_core.tools.function_param_desc_extractor import extract_param_desc

GOOGLE_STYLE_DOC = """Get the current weather for a location.

Args:
    location (str): The city and state, e.g. San Francisco, CA.
    unit (str): Temperature unit, either 'celsius' or
        'fahrenheit', spanning two lines.

Returns:
    dict: The weather info.
"""

REST_STYLE_DOC = """Get the current weather for a location.

:param location: The city and state, e.g. San Francisco, CA.
:param unit: Temperature unit, either celsius or fahrenheit.
:returns: The weather info.
"""

SPHINX_STYLE_DOC = """Get the current weather for a location.

:param str location: The city and state, e.g. San Francisco, CA.
:param str unit: Temperature unit, either celsius or fahrenheit.
:returns: The weather info.
"""


class TestGoogleStyle:
    def test_extracts_single_line_description(self):
        result = extract_param_desc("location", GOOGLE_STYLE_DOC)
        assert result == "The city and state, e.g. San Francisco, CA."

    def test_extracts_and_collapses_multiline_description(self):
        result = extract_param_desc("unit", GOOGLE_STYLE_DOC)
        assert result == "Temperature unit, either 'celsius' or 'fahrenheit', spanning two lines."

    def test_stops_before_returns_section(self):
        result = extract_param_desc("unit", GOOGLE_STYLE_DOC)
        assert "weather info" not in result


class TestRestStyle:
    def test_extracts_description(self):
        result = extract_param_desc("location", REST_STYLE_DOC)
        assert result == "The city and state, e.g. San Francisco, CA."

    def test_only_used_when_google_style_does_not_match(self):
        result = extract_param_desc("unit", REST_STYLE_DOC)
        assert result == "Temperature unit, either celsius or fahrenheit."


class TestSphinxStyleWithType:
    def test_extracts_description_ignoring_type_token(self):
        result = extract_param_desc("location", SPHINX_STYLE_DOC)
        assert result == "The city and state, e.g. San Francisco, CA."


class TestNoMatch:
    def test_empty_docstring_returns_empty_string(self):
        assert extract_param_desc("location", "") == ""

    def test_param_not_present_returns_empty_string(self):
        assert extract_param_desc("nonexistent_param", GOOGLE_STYLE_DOC) == ""

    def test_never_raises_on_garbage_docstring(self):
        assert extract_param_desc("location", "not a docstring at all") == ""


class TestNoFalseSubstringMatch:
    def test_substring_param_name_does_not_match_longer_name_google_style(self):
        # "loc" must not match against "location (str): ..." — the Google
        # regex requires a literal "(" immediately after the param name.
        assert extract_param_desc("loc", GOOGLE_STYLE_DOC) == ""

    def test_substring_param_name_does_not_match_rest_style(self):
        assert extract_param_desc("loc", REST_STYLE_DOC) == ""


class TestRegexSpecialCharactersAreEscaped:
    """Security-relevant: param_name is interpolated into a regex pattern.
    The source uses re.escape, so metacharacters must be treated literally
    rather than as regex syntax — this is what stops a param name containing
    regex metacharacters from corrupting the match or raising re.error."""

    def test_param_name_with_dot_is_treated_literally(self):
        doc = "a.b (str): dotted name description.\n"
        assert extract_param_desc("a.b", doc) == "dotted name description."
        # A literal dot should not match an unrelated single character here.
        assert extract_param_desc("axb", doc) == ""

    def test_param_name_with_parentheses_does_not_raise(self):
        doc = "weird(name) (str): odd but must not crash the regex engine.\n"
        # Must not raise re.error, regardless of match outcome.
        result = extract_param_desc("weird(name)", doc)
        assert isinstance(result, str)

    def test_param_name_with_asterisk_does_not_raise_or_wildcard_match(self):
        doc = "safe_param (str): unrelated description.\n"
        # "*" is a regex quantifier if unescaped; must not crash and must not
        # spuriously match unrelated docstring content.
        assert extract_param_desc("a*b", doc) == ""
