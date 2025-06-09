# Prerequisites
## Requirement packages
LLMfy depend on package below:
- Install [pydantic](https://pypi.org/project/pydantic) [required], 
- Install [openai](https://pypi.org/project/openai) to use OpenAI models [optional].
- Install [boto3](https://pypi.org/project/boto3/) to use AWS Bedrock models [optional].

## Configuration
### OpenAI models
To use `OpenAIModel`, add below config to your env:
- `OPENAI_API_KEY`

### AWS Bedrock models
To use `BedrockModel`, add below config to your env:
- `AWS_ACCESS_KEY_ID` 
- `AWS_SECRET_ACCESS_KEY` 
- `AWS_BEDROCK_REGION`