import os

from dotenv import load_dotenv

from app.exception.llmfy_exception import LLMfyException
from app.llmfy.llmfy import LLMfy
from app.llmfy.messages.message import Message
from app.llmfy.messages.role import Role
from app.llmfy.models.bedrock.bedrock_config import BedrockConfig
from app.llmfy.models.bedrock.bedrock_model import BedrockModel

from app.llmfy.models.openai.openai_config import OpenAIConfig
from app.llmfy.models.openai.openai_model import OpenAIModel
from app.llmfy.usage.usage_tracker import llmfy_usage_tracker


env_file = os.getenv("ENV_FILE", ".env")  # Default to .env if ENV_FILE is not set
load_dotenv(env_file)


def usage_example():
    info = """
	Irufano adalah seorang sofware engineer.
	"""

    # Configuration
    llm = BedrockModel(
        model="amazon.nova-lite-v1:0",
        config=BedrockConfig(temperature=0.7),
    )

    llm2 = OpenAIModel(
        model="gpt-4o-mini",
        config=OpenAIConfig(temperature=0.7),
    )

    SYSTEM_PROMPT = """Answer any user questions based solely on the data below:
    <data>
    {info}
    </data>
    
    Answer only relevant questions, otherwise, say sorry."""

    # Initialize framework
    bedrock = LLMfy(llm, system_message=SYSTEM_PROMPT, input_variables=["info"])
    openai = LLMfy(llm2, system_message=SYSTEM_PROMPT, input_variables=["info"])

    try:
        # Example conversation with tool use
        messages = [Message(role=Role.USER, content="Apa ibukota china?")]

        with llmfy_usage_tracker() as usage:
            response_b = bedrock.generate(messages, info=info)
            response_o = openai.generate(messages, info=info)

        print(f"\n>> {response_b.result.content}\n")
        print(f"\n>> {response_o.result.content}\n")
        print(f"Usage:\n{usage}\n")

    except LLMfyException as e:
        print(f"{e}")


usage_example()
