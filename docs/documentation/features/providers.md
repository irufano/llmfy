# Providers

Available providers on this llmfy:

- bedrock 
- openai
- google (next feature)

## Bedrock

Use `BedrockModel`.

```python
llm = BedrockModel(model="amazon.nova-lite-v1:0", config=config)
```

## OpenAI

Use `OpenAIModel`.

```python
llm = OpenAIModel(model="gpt-4o-mini", config=config)
```


