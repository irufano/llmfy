import base64
from dotenv import load_dotenv

from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.llmfy_core.llmfy import LLMfy
from llmfy.llmfy_core.messages.content import Content
from llmfy.llmfy_core.messages.content_type import ContentType
from llmfy.llmfy_core.messages.message import Message
from llmfy.llmfy_core.messages.role import Role
from llmfy.llmfy_core.models.bedrock.bedrock_config import BedrockConfig
from llmfy.llmfy_core.models.bedrock.bedrock_model import BedrockModel
from llmfy.llmfy_core.models.openai.openai_config import OpenAIConfig
from llmfy.llmfy_core.models.openai.openai_model import OpenAIModel
from llmfy.llmfy_core.usage.usage_tracker import llmfy_usage_tracker


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

    input_image = "llmfy/test/simple_flowchart.jpg"
    with open(input_image, "rb") as f:
        image_bytes = f.read()

    try:
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

        content = [
            Content(
                type=ContentType.TEXT,
                value="Jelaskan flowchart berikut.",
            ),
            Content(
                type=ContentType.IMAGE,
                format="jpeg",
                value=image_bytes,
            ),
        ]

        with llmfy_usage_tracker() as usage:
            # Use chat or invoke
            # (chat with messages)
            response = framework.chat(messages)
            # (invoke with content)
            response = framework.invoke(content)

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

    input_image = "llmfy/test/simple_flowchart.jpg"
    with open(input_image, "rb") as f:
        image = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode("utf-8")}"

    # image = "https://marketplace.canva.com/EAE6AFZ1JEQ/1/0/1600w/canva-simple-flowchart-infographic-graph-5JjJMyCnd5Y.jpg"

    try:
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

        content = [
            Content(
                value="Jelaskan flowchart berikut.",
            ),
            Content(
                type=ContentType.IMAGE,
                value=image,
            ),
        ]

        with llmfy_usage_tracker() as usage:
            # Use chat or invoke
            # (chat with messages)
            response = framework.chat(messages)
            # (invoke with content)
            response = framework.invoke(content)

        print(f"\n>> {response.result.content}\n")
        print(f"\nUsage:\n{usage}\n")

    except LLMfyException as e:
        print(f"{e}")


# image_bedrock_example()
image_openai_example()
