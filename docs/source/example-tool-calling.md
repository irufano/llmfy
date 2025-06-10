# Tool Calling Example

```python
from dotenv import load_dotenv

from llmfy import (
    BedrockConfig,
    BedrockModel,
    LLMfy,
    Message,
    Role,
    Tool,
    # OpenAIConfig,
    # OpenAIModel,
)

load_dotenv()


def tool_calling_example():
    llm = BedrockModel(
        model="amazon.nova-lite-v1:0",
        config=BedrockConfig(temperature=0.7),
    )

    # llm = OpenAIModel(
    #     model="gpt-4o-mini",
    #     config=OpenAIConfig(temperature=0.7),
    # )

    # Initialize framework
    ai = LLMfy(llm, system_message="You are a helpful assistant.")

    # Define a sample tool
    @Tool()
    def get_current_weather(location: str, unit: str = "celsius") -> str:
        return f"The weather in {location} is 22 degrees {unit}"

    @Tool()
    def get_current_time(location: str) -> str:
        return f"The time in {location} is 09:00 AM"

    tools = [get_current_weather, get_current_time]

    # Register tool
    ai.register_tool(tools)

    try:
        # Example conversation with tool use
        messages = [
            Message(
                role=Role.USER,
                content="what time and weather in London?",
            )
        ]

        response = ai.chat_with_tools(messages)

        print(f"\n>> {response.result.content}\n")

    except Exception as e:
        print(e)


def tool_calling_with_invoke_example():
    llm = BedrockModel(
        model="amazon.nova-lite-v1:0",
        config=BedrockConfig(temperature=0.7),
    )

    # config = OpenAIConfig(temperature=0.7)
    # llm = OpenAIModel(
    #     model="gpt-4o-mini",
    #     config=config,
    # )

    # Initialize framework
    ai = LLMfy(llm, system_message="You are a helpful assistant.")

    # Define a sample tool
    @Tool()
    def get_current_weather(location: str, unit: str = "celsius") -> str:
        return f"The weather in {location} is 22 degrees {unit}"

    @Tool()
    def get_current_time(location: str) -> str:
        return f"The time in {location} is 09:00 AM"

    tools = [get_current_weather, get_current_time]

    # Register tool
    ai.register_tool(tools)

    try:
        # Example conversation with tool use
        content = "what time and weather in London?"

        response = ai.invoke_with_tools(content)

        print(f"\n>> {response.result.content}\n")

    except Exception as e:
        print(e)


if __name__ == "__main__":
    tool_calling_example()
    tool_calling_with_invoke_example()
```