import os

from dotenv import load_dotenv

from llmfy import (
    BedrockConfig,
    BedrockModel,
    LLMfy,
    LLMfyException,
    Message,
    # OpenAIConfig,
    # OpenAIModel,
    Role,
)
from llmfy.llmfy_core.models import OpenAIModel
from llmfy.llmfy_core.models.openai.openai_config import OpenAIConfig
from llmfy.llmfy_core.usage.usage_tracker import llmfy_usage_tracker

env_file = os.getenv("ENV_FILE", ".env")  # Default to .env if ENV_FILE is not set
load_dotenv(env_file)


def retrieval_example():
    info = """
	Irufano adalah seorang sofware engineer.
	Dia berasal dari Indonesia.
	"""

    # Configuration
    # config = BedrockConfig(temperature=0.7)
    # llm = BedrockModel(
    #     model="amazon.nova-lite-v1:0",
    #     config=config,
    # )

    config = OpenAIConfig(temperature=0.7)
    llm = OpenAIModel(
        model="gpt-4o-mini",
        config=config,
    )

    SYSTEM_PROMPT = """Answer any user questions based solely on the data below:
    <data>
    {{info}}
    </data>
    
    Answer only relevant questions, otherwise say I don't know."""

    # Initialize framework
    framework = LLMfy(llm, system_message=SYSTEM_PROMPT, input_variables=["info"])

    try:
        messages = [Message(role=Role.USER, content="Apa ibukota china?")]

        response = framework.chat(messages, info=info)

        print(f"\n>> {response.result.content}\n")
        # print(f"\nUsage:\n{usage}\n")

    except LLMfyException as e:
        print(f"{e}")


def retrieval_invoke_example():
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
    {{info}}
    </data>

    Answer only relevant questions, otherwise say I don't know."""

    # Initialize framework
    framework = LLMfy(llm, system_message=SYSTEM_PROMPT, input_variables=["info"])

    try:
        content = "Apa ibukota china?"
        
        with llmfy_usage_tracker() as usage:
            response = framework.invoke(content, info=info)

        print(f"\n>> {response.result.content}\n")
        print(f"\nUsage:\n{usage}\n")

    except LLMfyException as e:
        print(f"{e}")


retrieval_example()
# retrieval_invoke_example()
