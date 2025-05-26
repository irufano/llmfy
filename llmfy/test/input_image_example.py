import base64
from dotenv import load_dotenv

from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.llmfy.llmfy import LLMfy
from llmfy.llmfy.messages.content import Content
from llmfy.llmfy.messages.content_type import ContentType
from llmfy.llmfy.messages.message import Message
from llmfy.llmfy.messages.role import Role
from llmfy.llmfy.models.bedrock import bedrock_usage_tracker
from llmfy.llmfy.models.bedrock.bedrock_config import BedrockConfig
from llmfy.llmfy.models.bedrock.bedrock_model import BedrockModel
from llmfy.llmfy.models.openai.openai_config import OpenAIConfig
from llmfy.llmfy.models.openai.openai_model import OpenAIModel
from llmfy.llmfy.usage.usage_tracker import llmfy_usage_tracker


load_dotenv()


def image_bedrock_example():
    # Configuration
    config = BedrockConfig(temperature=0.7)
    llm = BedrockModel(
        model="amazon.nova-pro-v1:0",
        config=config,
    )

    SYSTEM_PROMPT = """You are helpfull assistant."""

    # Initialize framework
    framework = LLMfy(llm, system_message=SYSTEM_PROMPT)

    input_image = "app/test/simple_flowchart.jpg"
    with open(input_image, "rb") as f:
        image_bytes = f.read()

    try:
        # Example conversation with tool use
        messages = [
            Message(
                role=Role.USER,
                content=[
                    Content(
                        type=ContentType.TEXT,
                        value="Jelaskan flowchart berikut.",
                    ),
                    Content(
                        type=ContentType.IMAGE,
                        format="jpeg",
                        value=image_bytes,
                    ),
                ],
            )
        ]

        with bedrock_usage_tracker() as usage:
            response = framework.generate(messages)

        print(f"\n>> {response.result.content}\n")
        print(f"\nUsage:\n{usage}\n")

    except LLMfyException as e:
        print(f"{e}")


def image_openai_example():
    # Configuration
    config = OpenAIConfig(temperature=0.7)
    llm = OpenAIModel(
        model="gpt-4o-mini",
        config=config,
    )

    SYSTEM_PROMPT = """You are helpfull assistant."""

    # Initialize framework
    framework = LLMfy(llm, system_message=SYSTEM_PROMPT)

    input_image = "app/test/simple_flowchart.jpg"
    with open(input_image, "rb") as f:
        image = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode("utf-8")}"

    # image = "https://marketplace.canva.com/EAE6AFZ1JEQ/1/0/1600w/canva-simple-flowchart-infographic-graph-5JjJMyCnd5Y.jpg"

    try:
        # Example conversation with tool use
        messages = [
            Message(
                role=Role.USER,
                content=[
                    Content(
                        value="Jelaskan flowchart berikut.",
                    ),
                    Content(
                        type=ContentType.IMAGE,
                        value=image,
                    ),
                ],
            )
        ]

        with llmfy_usage_tracker() as usage:
            response = framework.generate(messages)

        print(f"\n>> {response.result.content}\n")
        print(f"\nUsage:\n{usage}\n")

    except LLMfyException as e:
        print(f"{e}")


# image_bedrock_example()
image_openai_example()
