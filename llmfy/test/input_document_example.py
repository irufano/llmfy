import base64
from dotenv import load_dotenv

from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.llmfy_core.llmfy import LLMfy
from llmfy.llmfy_core.messages.content import Content
from llmfy.llmfy_core.messages.content_type import ContentType
from llmfy.llmfy_core.messages.message import Message
from llmfy.llmfy_core.messages.role import Role
from llmfy.llmfy_core.models.bedrock import bedrock_usage_tracker
from llmfy.llmfy_core.models.bedrock.bedrock_config import BedrockConfig
from llmfy.llmfy_core.models.bedrock.bedrock_model import BedrockModel
from llmfy.llmfy_core.models.openai import openai_usage_tracker
from llmfy.llmfy_core.models.openai.openai_config import OpenAIConfig
from llmfy.llmfy_core.models.openai.openai_model import OpenAIModel


load_dotenv()


def doc_bedrock_example():
    # Configuration
    config = BedrockConfig(temperature=0.7)
    llm = BedrockModel(
        model="amazon.nova-pro-v1:0",
        config=config,
    )

    SYSTEM_PROMPT = """You are helpfull assistant."""

    # Initialize framework
    framework = LLMfy(llm, system_message=SYSTEM_PROMPT)

    input_doc = "app/test/short_stories.pdf"
    with open(input_doc, "rb") as f:
        doc = f.read()

    try:
        # Example conversation with tool use
        messages = [
            Message(
                role=Role.USER,
                content=[
                    Content(
                        type=ContentType.DOCUMENT,
                        filename="short_stories",
                        value=doc,
                    ),
                    Content(
                        type=ContentType.TEXT,
                        value="Siapa pemeran dalam cerita di dokumen?",
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


def doc_openai_example():
    # Configuration
    config = OpenAIConfig(temperature=0.7)
    llm = OpenAIModel(
        model="gpt-4o",
        config=config,
    )

    SYSTEM_PROMPT = """You are helpfull assistant."""

    # Initialize framework
    framework = LLMfy(llm, system_message=SYSTEM_PROMPT)

    input_doc = "app/test/short_stories.pdf"
    with open(input_doc, "rb") as f:
        doc = (
            f"data:application/pdf;base64,{base64.b64encode(f.read()).decode("utf-8")}"
        )

    try:
        # Example conversation with tool use
        messages = [
            Message(
                role=Role.USER,
                content=[
                    Content(
                        type=ContentType.DOCUMENT,
                        filename="short_stories.pdf",
                        value=doc,
                    ),
                    Content(
                        value="Siapa pemeran dalam cerita di dokumen?",
                    ),
                ],
            )
        ]

        with openai_usage_tracker() as usage:
            response = framework.generate(messages)

        print(f"\n>> {response.result.content}\n")
        print(f"\nUsage:\n{usage}\n")

    except LLMfyException as e:
        print(f"{e}")


doc_bedrock_example()
# file_openai_example()
