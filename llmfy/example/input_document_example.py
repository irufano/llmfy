import base64

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
    OpenAIConfig,
    OpenAIModel,
    Role,
    llmfy_usage_tracker,
)

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

    input_doc = "llmfy/test/short_stories.pdf"
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

        content = [
            Content(
                type=ContentType.DOCUMENT,
                filename="short_stories",
                value=doc,
            ),
            Content(
                type=ContentType.TEXT,
                value="Siapa pemeran dalam cerita di dokumen?",
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


def doc_openai_example():
    # Configuration
    config = OpenAIConfig(temperature=0.7)
    llm = OpenAIModel(
        model="gpt-4o-mini",
        config=config,
    )

    SYSTEM_PROMPT = """You are helpfull assistant."""

    # Initialize framework
    framework = LLMfy(llm, system_message=SYSTEM_PROMPT)

    input_doc = "llmfy/test/short_stories.pdf"
    with open(input_doc, "rb") as f:
        doc = (
            f"data:application/pdf;base64,{base64.b64encode(f.read()).decode('utf-8')}"
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

        content = [
            Content(
                type=ContentType.DOCUMENT,
                filename="short_stories.pdf",
                value=doc,
            ),
            Content(
                value="Siapa pemeran dalam cerita di dokumen?",
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


def doc_googleai_example():
    # Configuration
    config = GoogleAIConfig(temperature=0.7)
    llm = GoogleAIModel(
        model="gemini-2.5-flash-lite",
        config=config,
    )

    SYSTEM_PROMPT = """You are helpfull assistant."""

    # Initialize framework
    framework = LLMfy(llm, system_message=SYSTEM_PROMPT)

    input_doc = "llmfy/test/short_stories.pdf"
    with open(input_doc, "rb") as f:
        doc = (
            f"data:application/pdf;base64,{base64.b64encode(f.read()).decode('utf-8')}"
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

        content = [
            Content(
                type=ContentType.DOCUMENT,
                filename="short_stories.pdf",
                value=doc,
            ),
            Content(
                value="Siapa pemeran dalam cerita di dokumen?",
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


# doc_bedrock_example()
# doc_openai_example()
doc_googleai_example()
