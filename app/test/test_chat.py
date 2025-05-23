import os
from dotenv import load_dotenv

from app import (
    OpenAIModel,
    OpenAIConfig,
    LLMfy,
    Tool,
    Message,
    Role,
    LLMfyException,
    openai_usage_tracker,
    ChatResponse,
)

env_file = os.getenv("ENV_FILE", ".env")  # Default to .env if ENV_FILE is not set
load_dotenv(env_file)


def _set_env(var: str):
    os.environ[var] = os.getenv(var, "None")
    # print(f"{var} set!")


_set_env("OPENAI_API_KEY")


# Test tools
def test_tools():
    # llm
    llm = OpenAIModel("gpt-4o-mini", config=OpenAIConfig(temperature=0.7))

    # Initialize framework
    framework = LLMfy(llm, system_message="You are a helpful assistant.")

    # Define a sample tool
    @Tool()
    def get_current_weather(location: str, unit: str = "celsius") -> str:
        return f"The weather in {location} is 22 degrees {unit}"

    @Tool()
    def get_time(location: str) -> str:
        return f"The time in {location} is 09:00 AM"

    tools = [get_current_weather, get_time]

    # Register tool
    framework.register_tool(tools)

    try:
        # Example conversation with tool use
        messages = [
            Message(
                role=Role.USER,
                content="What's the weather like in London and what time?",
            )
        ]

        response = framework.generate_with_tools(messages)
        print(f"\n>> {response.result.content}\n")

    except LLMfyException as e:
        print(f"Error: {e}")


# Test prompt
def test_prompt():
    info = """
	Irufano adalah seorang sofware engineer.
	Dia berasal dari Indonesia.
	"""

    # Configuration
    config = OpenAIConfig(temperature=0.7)
    llm = OpenAIModel(model="gpt-4o-mini", config=config)

    SYSTEM_PROMPT = """Answer any user questions based solely on the data below:
    <data>
    {info}
    </data>
    
    DO NOT response outside context."""

    # Initialize framework
    framework = LLMfy(llm, system_message=SYSTEM_PROMPT, input_variables=["info"])

    try:
        # Example conversation with tool use
        messages = [Message(role=Role.USER, content="apa ibukota china")]

        # sample custom price
        prices = {
            "gpt-4o": {"input": 2.50, "output": 10.00},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gpt-3.5-turbo": {"input": 0.05, "output": 1.50},
        }

        with openai_usage_tracker(pricing=prices) as usage:
            response = framework.generate(messages, info=info)
            print(f"\n>> {response.result.content}\n")
            print(f"\nUsage:\n{usage}\n")

    except LLMfyException as e:
        print(f"{e}")


def test_stream():
    info = """
	Irufano adalah seorang sofware engineer.
	Dia berasal dari Indonesia.
	"""

    # Configuration
    config = OpenAIConfig(temperature=0.7)
    llm = OpenAIModel(model="gpt-4o-mini", config=config)

    SYSTEM_PROMPT = """Answer any user questions based solely on the data below:
    <data>
    {info}
    </data>
    
    DO NOT response outside context."""

    # Initialize framework
    framework = LLMfy(llm, system_message=SYSTEM_PROMPT, input_variables=["info"])

    try:
        # Example conversation with tool use
        messages = [Message(role=Role.USER, content="apa ibukota china")]
        # with openai_usage_tracker() as usage:
        stream = framework.generate_stream(messages, info=info)
        print("RESPONSE:")
        for chunk in stream:
            if isinstance(chunk, ChatResponse):
                if chunk.result.content is not None:
                    print(f"{chunk.result.content}", end="")

    except LLMfyException as e:
        print(f"{e}")


if __name__ == "__main__":
    # test_tools()
    # test_prompt()
    test_stream()
