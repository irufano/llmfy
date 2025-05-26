from dotenv import load_dotenv

from llmfy.llmfy.llmfy import LLMfy
from llmfy.llmfy.messages.message import Message
from llmfy.llmfy.messages.role import Role
from llmfy.llmfy.models.bedrock import bedrock_stream_usage_tracker
from llmfy.llmfy.models.bedrock.bedrock_config import BedrockConfig
from llmfy.llmfy.models.bedrock.bedrock_model import BedrockModel
from llmfy.llmfy.responses.chat_response import ChatResponse


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

    llm = BedrockModel(
        model="amazon.nova-lite-v1:0",
        config=BedrockConfig(temperature=0.7),
    )

    SYSTEM_PROMPT = """Answer any user questions based solely on the data below:
    <data>
    {info}
    </data>
    
    DO NOT response outside context."""

    # Initialize framework
    chat = LLMfy(llm, system_message=SYSTEM_PROMPT, input_variables=["info"])

    try:
        # Example conversation with tool use
        messages = [Message(role=Role.USER, content="apa ibukota jakarta?")]
        # with openai_usage_tracker() as usage:
        with bedrock_stream_usage_tracker() as usage:
            stream = chat.generate_stream(messages, info=info)
            full_content = ""
            for chunk in stream:
                if isinstance(chunk, ChatResponse):
                    if chunk.result.content:
                        content = chunk.result.content
                        full_content += content
                        print(content, end="", flush=True)

            print(usage)

    except Exception as e:
        raise e


if __name__ == "__main__":
    stream_example()
