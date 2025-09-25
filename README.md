
<div align="center">

  <a href="https://img.shields.io/github/actions/workflow/status/irufano/llmfy/publish.yml">![llmfy](https://img.shields.io/github/actions/workflow/status/irufano/llmfy/publish.yml?style=for-the-badge&logo=pypi&logoColor=blue&label=publish
  )</a>
  <a href="https://pypi.org/project/llmfy/0.3.1">![llmfy](https://img.shields.io/badge/llmfy-V0.4.1-31CA9C.svg?style=for-the-badge&logo=pypi&logoColor=yellow)</a>
  <a href="https://pypi.org/project/llmfy/">![llmfy](https://img.shields.io/pypi/v/llmfy?style=for-the-badge&label=llmfy%20latest%20version&labelColor=691DC6&color=B77309)</a>
  <a href="">![python](https://img.shields.io/badge/python->=3.12-4392FF.svg?style=for-the-badge&logo=python&logoColor=4392FF)</a>

</div>

# llmfy

![](llmfy-banner.png)

`LLMfy` is a flexible and developer-friendly framework designed to streamline the creation of applications powered by large language models (LLMs). It provides essential tools and abstractions that simplify the integration, orchestration, and management of LLMs across various use cases, enabling developers to focus on building intelligent, context-aware solutions without getting bogged down in low-level model handling. With support for modular components, prompt engineering, and extensibility, LLMfy accelerates the development of AI-driven applications from prototyping to production.

See complete documentation at [https://llmfy.readthedocs.io/](https://llmfy.readthedocs.io/)

## How to install

- Prerequisites:
  - Install [pydantic](https://pypi.org/project/pydantic) [required], 
  - Install [openai](https://pypi.org/project/openai) to use OpenAI models [optional].
  - Install [boto3](https://pypi.org/project/boto3/) to use AWS Bedrock models [optional].

### Using pip
```sh
pip install llmfy
```
### using requirements.txt
- Add into requirements.txt
```txt
llmfy
```
- Then install
```txt
pip install -r requirements.txt
```

## How to use
### OpenAI models
To use `OpenAIModel`, add below config to your env:
- `OPENAI_API_KEY`

### AWS Bedrock models
To use `BedrockModel`, add below config to your env:
- `AWS_ACCESS_KEY_ID` 
- `AWS_SECRET_ACCESS_KEY` 
- `AWS_BEDROCK_REGION`

## Example
### LLMfy Example
```python
from llmfy import (
    OpenAIModel,
    OpenAIConfig,
    LLMfy,
    Message,
    Role,
    LLMfyException,
)

def sample_prompt():
    info = """Irufano adalah seorang software engineer.
    Dia berasal dari Indonesia.
    Kamu bisa mengunjungi websitenya di https:://irufano.github.io"""

    # Configuration
    config = OpenAIConfig(temperature=0.7)
    llm = OpenAIModel(model="gpt-4o-mini", config=config)

    SYSTEM_PROMPT = """Answer any user questions based solely on the data below:
    <data>
    {info}
    </data>
    
    DO NOT response outside context."""

    # Initialize framework
    framework = LLMfy(llm, system_message=SYSTEM_PROMPT, input_variables=["info"])

    try:
        messages = [Message(role=Role.USER, content="apa ibukota china")]
       
        response = framework.generate(messages, info=info)
        print(f"\n>> {response.result.content}\n")

    except LLMfyException as e:
        print(f"{e}")


if __name__ == "__main__":
    sample_prompt()
```

## Develop as Contributor

### Build package
```sh
python setup.py sdist bdist_wheel
```

### Upload package
```sh
twine upload dist/*
```

### Trigger buld and deploy to pypi
```sh
# TAGE_NAME must starting with "v" (e.g., v1.0.0)
git tag -a [TAGE_NAME] -m "[TAGE_MESSAGE]"
 
# push tag to remote
git push origin [TAGE_NAME]
```
