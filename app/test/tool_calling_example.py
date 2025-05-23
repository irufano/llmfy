from dotenv import load_dotenv
from app.llmfy.llmfy import LLMfy
from app.llmfy.messages.message import Message
from app.llmfy.messages.role import Role
from app.llmfy.models.bedrock import bedrock_usage_tracker
from app.llmfy.models.bedrock.bedrock_config import BedrockConfig
from app.llmfy.models.bedrock.bedrock_model import BedrockModel
from app.llmfy.tools.tool import Tool

load_dotenv()


def tool_calling_example():
    # llm
    # model="anthropic.claude-3-haiku-20240307-v1:0",
    # model="us.anthropic.claude-3-5-haiku-20241022-v1:0",
    # model="anthropic.claude-3-5-sonnet-20240620-v1:0",
    # model="amazon.nova-lite-v1:0",

    llm = BedrockModel(
        model="amazon.nova-lite-v1:0",
        config=BedrockConfig(temperature=0.7),
    )

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

        # sample custom price
        prices = {
            "amazon.nova-lite-v1:0": {
                "us-east-1": {
                    "region": "US East (N. Virginia)",
                    "input": 0.00006,
                    "output": 0.00024,
                },
                "us-west-2": {
                    "region": "US West (Oregon)",
                    "input": 0.00006,
                    "output": 0.00024,
                },
            },
        }
        with bedrock_usage_tracker(pricing=prices) as usage:
            response = ai.generate_with_tools(messages)
            print(f"\n>> {response.result.content}\n")
            print(usage)
            print("\n")

    except Exception as e:
        print(e)


if __name__ == "__main__":
    tool_calling_example()
