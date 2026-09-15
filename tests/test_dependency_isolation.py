"""Supply-chain / optional-dependency isolation tests.

Architectural invariant: provider SDKs (openai,
boto3, anthropic, google-genai) are imported lazily behind
`try: import X except ImportError: X = None`, specifically so the core
`llmfy` package has NO hard dependency on any of them. These are the
project's most realistic "security" surface (this is a client library, not a
server — there's no auth/session/DB boundary to test) in two ways:

1. A future refactor could accidentally harden a lazy guarded import into an
   eager one, silently making an optional extra a hard dependency for every
   user (dependency-confusion-adjacent risk: users who installed only
   `llmfy[anthropic]` would suddenly need `openai` too, or the package would
   fail to import at all).
2. A missing optional SDK must fail with a clean, actionable `LLMfyException`
   ("install `llmfy[openai]`") — never a raw unhandled `ModuleNotFoundError`
   leaking an internal import-path stack trace to the caller.

Both are tested here by running a real subprocess with the target SDK's
import path blocked via a `sys.meta_path` finder — this is the only reliable
way to test "package X is not installed" without actually uninstalling
anything from the shared dev/test environment.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CORE_USAGE_SCRIPT = """
import sys


class BlockingFinder:
    def __init__(self, blocked):
        self.blocked = blocked

    def find_spec(self, name, path, target=None):
        if name in self.blocked or any(name.startswith(b + ".") for b in self.blocked):
            raise ModuleNotFoundError(f"blocked for isolation test: {name}")
        return None


sys.meta_path.insert(0, BlockingFinder({"openai", "boto3", "aioboto3", "anthropic", "google.genai"}))

import llmfy
from llmfy import Content, ContentType, LLMfyException, Message, Role, Tool, chunk_text

msg = Message(role=Role.USER, content="hi")
assert msg.content == "hi"

chunks = chunk_text("word " * 30, chunk_size=100, chunk_overlap=20)
assert len(chunks) >= 1

@Tool()
def noop() -> None:
    \"\"\"Do nothing.\"\"\"
    return None

assert noop._is_tool is True

content = Content(type=ContentType.TEXT, value="x")
assert content.value == "x"

exc = LLMfyException("ok")
assert exc.message == "ok"

print("CORE_USAGE_OK")
"""


def _run_isolated_script(script: str) -> subprocess.CompletedProcess:
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(script)
        script_path = f.name
    try:
        return subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=60,
        )
    finally:
        Path(script_path).unlink(missing_ok=True)


def test_core_package_usable_with_zero_optional_sdks_installed():
    result = _run_isolated_script(CORE_USAGE_SCRIPT)
    assert result.returncode == 0, f"stdout={result.stdout}\nstderr={result.stderr}"
    assert "CORE_USAGE_OK" in result.stdout


PROVIDER_MODEL_CASES = [
    pytest.param(
        "openai",
        "from llmfy import OpenAIChatModel as M\nM(model='m', api_key='k')",
        "openai package is not installed",
        id="openai-chat",
    ),
    pytest.param(
        "anthropic",
        "from llmfy import AnthropicMessagesModel as M\nM(model='m', api_key='k')",
        "anthropic package is not installed",
        id="anthropic-messages",
    ),
    pytest.param(
        "boto3",
        (
            "from llmfy import BedrockConverseModel as M\n"
            "M(model='m', aws_access_key_id='a', aws_secret_access_key='b', "
            "aws_bedrock_region='us-east-1')"
        ),
        "boto3 package is not installed",
        id="bedrock-converse",
    ),
    pytest.param(
        "google.genai",
        "from llmfy import GoogleAIGenerateModel as M\nM(model='m', api_key='k')",
        "google-genai package is not installed",
        id="google-generate",
    ),
]


@pytest.mark.parametrize("blocked_module, construct_call, expected_message", PROVIDER_MODEL_CASES)
def test_missing_provider_sdk_raises_clean_llmfy_exception(
    blocked_module: str, construct_call: str, expected_message: str
):
    indented_call = "\n".join("    " + line for line in construct_call.splitlines())
    script = f"""
import sys


class BlockingFinder:
    def __init__(self, blocked):
        self.blocked = blocked

    def find_spec(self, name, path, target=None):
        if name == self.blocked or name.startswith(self.blocked + "."):
            raise ModuleNotFoundError(f"blocked for isolation test: {{name}}")
        return None


sys.meta_path.insert(0, BlockingFinder({blocked_module!r}))

from llmfy import LLMfyException

try:
{indented_call}
    print("NO_EXCEPTION_RAISED")
except LLMfyException as e:
    print("LLMFY_EXCEPTION:" + str(e))
except Exception as e:
    print("WRONG_EXCEPTION_TYPE:" + type(e).__name__ + ":" + str(e))
"""
    result = _run_isolated_script(script)
    assert result.returncode == 0, f"stdout={result.stdout}\nstderr={result.stderr}"
    assert "LLMFY_EXCEPTION:" in result.stdout, (
        f"expected a clean LLMfyException, got: {result.stdout!r} / {result.stderr!r}"
    )
    assert expected_message in result.stdout
    assert "WRONG_EXCEPTION_TYPE" not in result.stdout
    assert "NO_EXCEPTION_RAISED" not in result.stdout
