# Retrieval Example

```python linenums="1"
import os

from dotenv import load_dotenv

from llmfy import (
    LLMfyException,
    LLMfy,
    Message,
    Role,
    BedrockConfig,
    BedrockModel,
    # OpenAIConfig,
    # OpenAIModel,
)

env_file = os.getenv("ENV_FILE", ".env")  # Default to .env if ENV_FILE is not set
load_dotenv(env_file)


def retrieval_chat_example():
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
        messages = [Message(role=Role.USER, content="Apa ibukota china?")]

        response = framework.chat(messages, info=info)

        print(f"\n>> {response.result.content}\n")

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
    {info}
    </data>
    
    Answer only relevant questions, otherwise, say I don't know."""

    # Initialize framework
    framework = LLMfy(llm, system_message=SYSTEM_PROMPT, input_variables=["info"])

    try:
        content = "Apa ibukota china?"

        response = framework.invoke(content, info=info)

        print(f"\n>> {response.result.content}\n")

    except LLMfyException as e:
        print(f"{e}")


retrieval_chat_example()
retrieval_invoke_example()
```