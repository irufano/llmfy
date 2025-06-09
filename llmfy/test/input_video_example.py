from dotenv import load_dotenv

from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.llmfy_core.llmfy import LLMfy
from llmfy.llmfy_core.messages.content import Content
from llmfy.llmfy_core.messages.content_type import ContentType
from llmfy.llmfy_core.messages.message import Message
from llmfy.llmfy_core.messages.role import Role
from llmfy.llmfy_core.models.bedrock.bedrock_config import BedrockConfig
from llmfy.llmfy_core.models.bedrock.bedrock_model import BedrockModel
from llmfy.llmfy_core.usage.usage_tracker import llmfy_usage_tracker


load_dotenv()


def video_bedrock_example():
    # Configuration
    config = BedrockConfig(temperature=0.7)
    llm = BedrockModel(
        model="amazon.nova-pro-v1:0",
        config=config,
    )

    SYSTEM_PROMPT = """You are helpfull assistant."""

    # Initialize framework
    framework = LLMfy(llm, system_message=SYSTEM_PROMPT)

    input_video = "llmfy/test/sample_video.mp4"
    with open(input_video, "rb") as f:
        video_bytes = f.read()

    try:
        messages = [
            Message(
                role=Role.USER,
                content=[
                    Content(
                        type=ContentType.TEXT,
                        value="Apa yg terjadi di video berikut.",
                    ),
                    Content(
                        type=ContentType.VIDEO,
                        format="mp4",
                        value=video_bytes,
                    ),
                ],
            )
        ]

        content = [
            Content(
                type=ContentType.TEXT,
                value="Apa yg terjadi di video berikut.",
            ),
            Content(
                type=ContentType.VIDEO,
                format="mp4",
                value=video_bytes,
            ),
        ]

        with llmfy_usage_tracker() as usage:
            # Use chat or invoke
            # (chat with messages)
            response = framework.chat(messages)
            # (invoke with content)
            response = framework.invoke(content)

        print(f"\n>> {response.result.content}\n")
        print(f"\n{usage}\n")

    except LLMfyException as e:
        print(f"{e}")


video_bedrock_example()
