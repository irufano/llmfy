
<div align="center">

  <a href="https://pypi.org/project/aigoofusion/">![llmfy](https://img.shields.io/badge/llmfy-0.2.6-30B445.svg?style=for-the-badge)</a>
  <a href="">![python](https://img.shields.io/badge/python->=3.12-4392FF.svg?style=for-the-badge&logo=python&logoColor=4392FF)</a>

</div>

# llmfy

![](llmfy-banner.png)

`LLMfy` is a framework for developing applications with large language models (LLMs). 
- `LLMfy` is llm abstraction to use various llm on one module. 
- `LLMfyPipe` is llm apps workflow.

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
### Build the container
```sh
docker-compose build
```

### Run the container
```sh
docker-compose up -d aigoofusion
```

### Stop the container
```sh
docker-compose stop aigoofusion
```

### Access the container shell
```sh
docker exec -it aigoofusion bash
```

### Build package
```sh
python setup.py sdist bdist_wheel
```

### Upload package
```sh
twine upload dist/*
```
