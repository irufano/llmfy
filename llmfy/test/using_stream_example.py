from dotenv import load_dotenv

from llmfy import (
    # BedrockConfig,
    # BedrockModel,
    GenerationResponse,
    LLMfy,
    Message,
    Role,
    llmfy_usage_tracker,
)
from llmfy.llmfy_core.models.openai.openai_config import OpenAIConfig
from llmfy.llmfy_core.models.openai.openai_model import OpenAIModel

load_dotenv()


def stream_example():
    info = """
	Irufano adalah seorang sofware engineer.
	Dia berasal dari Indonesia.
	"""

    # llm
    # model="anthropic.claude-3-haiku-20240307-v1:0",
    # model="us.anthropic.claude-3-5-haiku-20241022-v1:0",
    # model="amazon.nova-lite-v1:0",

    # llm = BedrockModel(
    #     model="amazon.nova-lite-v1:0",
    #     config=BedrockConfig(temperature=0.7),
    # )

    llm = OpenAIModel(
        model="gpt-4o-mini",
        config=OpenAIConfig(temperature=0.7),
    )

    SYSTEM_PROMPT = """Answer any user questions based solely on the data below:
    <data>
    {{info}}
    </data>
    
    DO NOT response outside context."""

    # Initialize framework
    chat = LLMfy(llm, system_message=SYSTEM_PROMPT, input_variables=["info"])

    try:
        # Example conversation with tool use
        messages = [Message(role=Role.USER, content="apa ibukota jakarta?")]
        # with openai_usage_tracker() as usage:
        with llmfy_usage_tracker() as usage:
            stream = chat.chat_stream(messages, info=info)
            full_content = ""
            num = 0
            for chunk in stream:
                if isinstance(chunk, GenerationResponse):
                    if chunk.result.content:
                        content = chunk.result.content
                        full_content += content
                        num += 1
                        print(f"chunk: {num}")
                        print(content, flush=True)
                        print("\n")
                        # print(content, end="", flush=True)

            print("--- full ---")
            print(full_content)
            print("------")

            print(usage)

    except Exception as e:
        raise e


def stream_invoke_example():
    info = """
	Irufano adalah seorang sofware engineer.
	Dia berasal dari Indonesia.
	"""

    # llm
    # model="anthropic.claude-3-haiku-20240307-v1:0",
    # model="us.anthropic.claude-3-5-haiku-20241022-v1:0",
    # model="amazon.nova-lite-v1:0",

    # llm = BedrockModel(
    #     model="amazon.nova-lite-v1:0",
    #     config=BedrockConfig(temperature=0.7),
    # )

    llm = OpenAIModel(
        model="gpt-4o-mini",
        config=OpenAIConfig(temperature=0.7),
    )

    SYSTEM_PROMPT = """Answer any user questions based solely on the data below:
    <data>
    {{info}}
    </data>
    
    DO NOT response outside context."""

    # Initialize framework
    chat = LLMfy(llm, system_message=SYSTEM_PROMPT, input_variables=["info"])

    try:
        # with openai_usage_tracker() as usage:
        with llmfy_usage_tracker() as usage:
            stream = chat.invoke_stream(contents="apa ibukota jakarta?", info=info)
            full_content = ""
            num = 0
            for chunk in stream:
                if isinstance(chunk, GenerationResponse):
                    if chunk.result.content:
                        content = chunk.result.content
                        full_content += content
                        num += 1
                        print(f"chunk: {num}")
                        print(content, flush=True)
                        print("\n")
                        # print(content, end="", flush=True)

            print("--- full ---")
            print(full_content)
            print("------")

            print(usage)

    except Exception as e:
        raise e


if __name__ == "__main__":
    stream_example()
