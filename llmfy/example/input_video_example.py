from dotenv import load_dotenv

from llmfy import (
    BedrockConfig,
    BedrockModel,
    Content,
    ContentType,
    GoogleAIConfig,
    GoogleAIModel,
    LLMfy,
    LLMfyException,
    Message,
    Role,
    llmfy_usage_tracker,
)

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


def video_googleai_example():
    # Configuration
    config = GoogleAIConfig(temperature=0.7)
    llm = GoogleAIModel(
        model="gemini-2.5-flash-lite",
        config=config,
    )

    SYSTEM_PROMPT = """You are helpfull assistant."""

    # Initialize framework
    framework = LLMfy(llm, system_message=SYSTEM_PROMPT)

    # Google supports http URL or YouTube URL
    input_video = "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/Big_Buck_Bunny_360_10s_1MB.mp4"

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
                        value=input_video,
                        format="mp4"
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
                value=input_video,
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


def video_googleai_bytes_example():
    # Configuration
    config = GoogleAIConfig(temperature=0.7)
    llm = GoogleAIModel(
        model="gemini-2.5-flash-lite",
        config=config,
    )

    SYSTEM_PROMPT = """You are helpfull assistant."""

    # Initialize framework
    framework = LLMfy(llm, system_message=SYSTEM_PROMPT)

    # Inline bytes — recommended for files < 20 MB.
    # `format` is optional; defaults to "mp4" if omitted.
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
                        value=video_bytes,
                        format="mp4",  # optional, defaults to mp4
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
                value=video_bytes,
                # format="mp4",  # optional, defaults to mp4
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


# video_bedrock_example()
# video_googleai_example()
video_googleai_bytes_example()
