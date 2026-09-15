"""Unit tests for llmfy/llmfy_utils/deprecated/deprecated.py."""

import warnings

import pytest

from llmfy.llmfy_utils.deprecated.deprecated import deprecated


class TestFunctionDecoration:
    def test_calling_decorated_function_emits_warning(self):
        @deprecated(reason="use new_func instead")
        def old_func(x):
            return x * 2

        with pytest.warns(DeprecationWarning, match="old_func"):
            result = old_func(5)
        assert result == 10

    def test_decoration_itself_does_not_warn_only_calling_does(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error")

            @deprecated()
            def old_func():
                return "ok"

        with pytest.warns(DeprecationWarning):
            old_func()

    def test_message_includes_version_and_alternative(self):
        @deprecated(version="1.2", alternative="new_func")
        def old_func():
            return None

        with pytest.warns(DeprecationWarning) as record:
            old_func()
        message = str(record[0].message)
        assert "since version 1.2" in message
        assert "Use 'new_func' instead" in message

    def test_message_includes_reason_in_parentheses(self):
        @deprecated(reason="slow and buggy")
        def old_func():
            return None

        with pytest.warns(DeprecationWarning, match=r"\(slow and buggy\)"):
            old_func()

    def test_custom_warning_category(self):
        @deprecated(category=FutureWarning)
        def old_func():
            return None

        with pytest.warns(FutureWarning):
            old_func()

    def test_wraps_preserves_function_metadata(self):
        @deprecated()
        def old_func():
            """Original docstring."""
            return None

        assert old_func.__name__ == "old_func"
        assert old_func.__doc__ == "Original docstring."


class TestClassDecoration:
    def test_instantiation_emits_warning(self):
        @deprecated(alternative="NewClass")
        class OldClass:
            def __init__(self, value):
                self.value = value

        with pytest.warns(DeprecationWarning, match="Class 'OldClass'"):
            instance = OldClass(42)
        assert instance.value == 42

    def test_decorator_returns_same_class_object(self):
        class Original:
            pass

        Decorated = deprecated()(Original)
        assert Decorated is Original

    def test_class_with_no_explicit_init_still_works(self):
        @deprecated()
        class NoInit:
            pass

        with pytest.warns(DeprecationWarning):
            NoInit()
