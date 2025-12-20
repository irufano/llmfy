# Usage Tracker Example

```python linenums="1"
from dotenv import load_dotenv

from llmfy import (
    LLMfyException,
    LLMfy,
    Message,
    Role,
    BedrockConfig,
    BedrockModel,
    OpenAIConfig,
    OpenAIModel,
    llmfy_usage_tracker,
)

load_dotenv()


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
    {{info}}
    </data>
    
    Answer only relevant questions, otherwise, say sorry."""

    # Initialize framework
    bedrock = LLMfy(llm, system_message=SYSTEM_PROMPT, input_variables=["info"])
    openai = LLMfy(llm2, system_message=SYSTEM_PROMPT, input_variables=["info"])

    try:
        # Example conversation with tool use
        messages = [Message(role=Role.USER, content="Apa ibukota china?")]
        contents = "Apa ibukota china?"

        with llmfy_usage_tracker() as usage:
            # Use chat or invoke
            # (chat use messages)
            response_b = bedrock.chat(messages, info=info)
            # response_o = openai.chat(messages, info=info)
            # (invoke use contents)
            # response_b = bedrock.invoke(contents, info=info)
            response_o = openai.invoke(contents, info=info)

        print(f"\n>> {response_b.result.content}\n")
        print(f"\n>> {response_o.result.content}\n")
        print(f"Usage:\n{usage}\n")

    except LLMfyException as e:
        print(f"{e}")


usage_example()

```