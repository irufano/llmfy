import os

from dotenv import load_dotenv

from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.llmfy.llmfy import LLMfy
from llmfy.llmfy.messages.message import Message
from llmfy.llmfy.messages.role import Role
from llmfy.llmfy.models.bedrock.bedrock_config import BedrockConfig
from llmfy.llmfy.models.bedrock.bedrock_model import BedrockModel

# from app.llmfy.models.openai.openai_config import OpenAIConfig
# from app.llmfy.models.openai.openai_model import OpenAIModel


env_file = os.getenv("ENV_FILE", ".env")  # Default to .env if ENV_FILE is not set
load_dotenv(env_file)


def retrieval_example():
    info = """
	Irufano adalah seorang sofware engineer.
	Dia berasal dari Indonesia.
	"""

    # Configuration
    config = BedrockConfig(temperature=0.7)
    llm = BedrockModel(
        model="amazon.nova-lite-v1:0",
        config=config,
    )

    # config = OpenAIConfig(temperature=0.7)
    # llm = OpenAIModel(
    #     model="gpt-4o-mini",
    #     config=config,
    # )

    SYSTEM_PROMPT = """Answer any user questions based solely on the data below:
    <data>
    {info}
    </data>
    
    Answer only relevant questions, otherwise, say I don't know."""

    # Initialize framework
    framework = LLMfy(llm, system_message=SYSTEM_PROMPT, input_variables=["info"])

    try:
        # Example conversation with tool use
        messages = [Message(role=Role.USER, content="Apa ibukota china?")]

        response = framework.generate(messages, info=info)

        print(f"\n>> {response.result.content}\n")
        # print(f"\nUsage:\n{usage}\n")

    except LLMfyException as e:
        print(f"{e}")


retrieval_example()
