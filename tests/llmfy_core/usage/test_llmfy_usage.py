"""Unit tests for llmfy/llmfy_core/usage/llmfy_usage.py."""

import pytest

from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.llmfy_core.model_backend import ModelBackend
from llmfy.llmfy_core.service_provider import ServiceProvider
from llmfy.llmfy_core.service_type import ServiceType
from llmfy.llmfy_core.usage.llmfy_usage import LLMfyUsage

# ---------------------------------------------------------------------------
# Pricing structure validation
# ---------------------------------------------------------------------------


class TestPricingValidation:
    def test_valid_openai_pricing_accepted(self):
        usage = LLMfyUsage(openai_pricing={"m": {"input": 1.0, "output": 2.0}})
        assert "m" in usage.openai_pricing

    def test_invalid_openai_pricing_non_numeric_leaf_raises(self):
        with pytest.raises(LLMfyException):
            LLMfyUsage(openai_pricing={"m": {"input": "not-a-number", "output": 2.0}})

    def test_invalid_openai_pricing_not_a_dict_of_dicts_raises(self):
        with pytest.raises(LLMfyException):
            LLMfyUsage(openai_pricing={"m": "not-a-dict"})

    def test_valid_anthropic_pricing_accepted(self):
        usage = LLMfyUsage(anthropic_pricing={"m": {"input": 1.0, "output": 2.0}})
        assert "m" in usage.anthropic_pricing

    def test_invalid_anthropic_pricing_raises(self):
        with pytest.raises(LLMfyException):
            LLMfyUsage(anthropic_pricing={"m": {"input": "bad"}})

    def test_bedrock_pricing_structure_check_ignores_leaf_values(self):
        # Unlike openai/anthropic, bedrock's structure validator only checks
        # two levels of dict nesting — it never inspects the innermost leaf
        # values, so a region dict missing "input"/"output" passes
        # __is_valid_bedrock_pricing_structure... and only fails downstream
        # in _load_bedrock_pricing's raw `pricing["input"]` lookup, as a
        # plain KeyError (not the LLMfyException a caller might expect).
        with pytest.raises(KeyError):
            LLMfyUsage(bedrock_pricing={"m": {"us-east-1": {"not_input": 1}}})

    def test_bedrock_pricing_not_nested_two_levels_raises(self):
        with pytest.raises(LLMfyException):
            LLMfyUsage(bedrock_pricing={"m": "not-a-dict"})

    def test_googleai_flat_pricing_accepted(self):
        usage = LLMfyUsage(googleai_pricing={"m": {"input": 0.1, "output": 0.4}})
        assert "m" in usage.googleai_pricing

    def test_googleai_missing_input_or_output_key_raises(self):
        with pytest.raises(LLMfyException):
            LLMfyUsage(googleai_pricing={"m": {"input": 0.1}})

    def test_googleai_per_type_pricing_requires_default_key(self):
        with pytest.raises(LLMfyException):
            LLMfyUsage(googleai_pricing={"m": {"input": {"text": 0.5}, "output": 0.4}})

    def test_googleai_per_type_pricing_with_default_key_accepted(self):
        usage = LLMfyUsage(
            googleai_pricing={
                "m": {"input": {"default": 0.5, "text": 0.5}, "output": 0.4}
            }
        )
        assert "m" in usage.googleai_pricing

    def test_googleai_partial_tier_config_raises(self):
        # threshold/input_high/output_high must all be present together.
        with pytest.raises(LLMfyException):
            LLMfyUsage(
                googleai_pricing={"m": {"input": 1.0, "output": 2.0, "threshold": 1000}}
            )

    def test_googleai_full_tier_config_accepted(self):
        usage = LLMfyUsage(
            googleai_pricing={
                "m": {
                    "input": 1.0,
                    "output": 2.0,
                    "input_high": 2.0,
                    "output_high": 4.0,
                    "threshold": 1000,
                }
            }
        )
        assert "m" in usage.googleai_pricing

    def test_empty_dict_bypasses_validation_and_falls_back_to_default_pricing(self):
        # `{}` is falsy, so `if openai_pricing:` skips validation entirely,
        # AND `openai_pricing or OPENAI_PRICING` then substitutes the bundled
        # default table instead of using the (empty) dict as-is.
        usage = LLMfyUsage(openai_pricing={})
        assert len(usage.openai_pricing) > 0  # populated from bundled defaults

    def test_none_uses_bundled_defaults(self):
        usage = LLMfyUsage()
        assert len(usage.openai_pricing) > 0
        assert len(usage.anthropic_pricing) > 0
        assert len(usage.bedrock_pricing) > 0
        assert len(usage.googleai_pricing) > 0


# ---------------------------------------------------------------------------
# update() dispatch
# ---------------------------------------------------------------------------


class TestUpdateDispatch:
    def test_llm_with_no_backend_is_a_silent_no_op(self):
        usage = LLMfyUsage()
        usage.update(type=ServiceType.LLM, model="gpt-4o", usage={"prompt_tokens": 10})
        assert usage.total_request == 0
        assert usage.total_tokens == 0

    def test_embedding_with_no_provider_is_a_silent_no_op(self):
        usage = LLMfyUsage()
        usage.update(type=ServiceType.EMBEDDING, model="m", usage={"prompt_tokens": 10})
        assert usage.total_request == 0

    def test_embedding_with_anthropic_provider_is_a_silent_no_op(self):
        # There is deliberately no ANTHROPIC case in the EMBEDDING match arm.
        usage = LLMfyUsage()
        usage.update(
            type=ServiceType.EMBEDDING,
            model="m",
            usage={"prompt_tokens": 10},
            provider=ServiceProvider.ANTHROPIC,
        )
        assert usage.total_request == 0

    def test_unrecognized_type_is_a_silent_no_op(self):
        usage = LLMfyUsage()
        usage.update(type="not-a-real-type", model="m", usage={})  # type: ignore[arg-type]
        assert usage.total_request == 0


# ---------------------------------------------------------------------------
# OpenAI Chat
# ---------------------------------------------------------------------------


class TestOpenAIChatUpdate:
    def test_basic_cost_and_token_accounting(self):
        usage = LLMfyUsage(openai_pricing={"gpt-test": {"input": 2.0, "output": 4.0}})
        usage.update(
            type=ServiceType.LLM,
            backend=ModelBackend.OPENAI_CHAT,
            model="gpt-test",
            usage={"prompt_tokens": 1_000_000, "completion_tokens": 500_000},
        )
        assert usage.total_request == 1
        assert usage.input_tokens == 1_000_000
        assert usage.output_tokens == 500_000
        assert usage.total_tokens == 1_500_000
        assert usage.total_cost == pytest.approx(2.0 + 2.0)  # 1*2.0 + 0.5*4.0

    def test_cache_read_and_write_pricing(self):
        usage = LLMfyUsage(
            openai_pricing={
                "gpt-test": {
                    "input": 2.0,
                    "output": 4.0,
                    "cache_read": 1.0,
                    "cache_write": 0.5,
                }
            }
        )
        usage.update(
            type=ServiceType.LLM,
            backend=ModelBackend.OPENAI_CHAT,
            model="gpt-test",
            usage={
                "prompt_tokens": 1_000_000,
                "completion_tokens": 500_000,
                "prompt_tokens_details": {
                    "cached_tokens": 200_000,
                    "cache_write_tokens": 100_000,
                },
            },  # type: ignore
        )
        # non_cached_input = 1,000,000 - 200,000 - 100,000 = 700,000
        # i_price = 0.7 * 2.0 = 1.4 ; cache_r = 0.2 * 1.0 = 0.2
        # cache_w = 0.1 * 0.5 = 0.05 ; o_price = 0.5 * 4.0 = 2.0
        assert usage.total_cost == pytest.approx(1.4 + 0.2 + 0.05 + 2.0)
        assert usage.cache_read_tokens == 200_000
        assert usage.cache_write_tokens == 100_000

    def test_unknown_model_warns_and_records_zero_cost_detail(self):
        usage = LLMfyUsage(
            openai_pricing={"known-model": {"input": 1.0, "output": 1.0}}
        )
        with pytest.warns(UserWarning, match="not found"):
            usage.update(
                type=ServiceType.LLM,
                backend=ModelBackend.OPENAI_CHAT,
                model="unknown-model",
                usage={"prompt_tokens": 100, "completion_tokens": 50},
            )
        assert usage.total_cost == 0
        assert usage.input_tokens == 100  # usage still recorded despite unknown pricing
        detail = usage.details[-1]
        assert detail["input_price"] is None
        assert detail["output_price"] is None

    def test_usage_object_with_attributes_instead_of_dict_is_supported(self):
        class FakeUsage:
            def __init__(self):
                self.prompt_tokens = 100
                self.completion_tokens = 50
                self.prompt_tokens_details = None

        usage = LLMfyUsage(openai_pricing={"m": {"input": 1.0, "output": 1.0}})
        usage.update(
            type=ServiceType.LLM,
            backend=ModelBackend.OPENAI_CHAT,
            model="m",
            usage=FakeUsage(),  # type: ignore
        )
        assert usage.total_request == 1
        assert usage.input_tokens == 100

    def test_detail_records_backend_and_provider(self):
        usage = LLMfyUsage(openai_pricing={"m": {"input": 1.0, "output": 1.0}})
        usage.update(
            type=ServiceType.LLM,
            backend=ModelBackend.OPENAI_CHAT,
            model="m",
            usage={"prompt_tokens": 1, "completion_tokens": 1},
        )
        detail = usage.details[-1]
        assert detail["backend"] == ModelBackend.OPENAI_CHAT
        assert detail["provider"] == ServiceProvider.OPENAI
        assert detail["type"] == ServiceType.LLM


class TestOpenAIResponsesUpdate:
    def test_uses_input_output_tokens_field_names(self):
        usage = LLMfyUsage(openai_pricing={"m": {"input": 1.0, "output": 2.0}})
        usage.update(
            type=ServiceType.LLM,
            backend=ModelBackend.OPENAI_RESPONSES,
            model="m",
            usage={"input_tokens": 1_000_000, "output_tokens": 500_000},
        )
        assert usage.total_cost == pytest.approx(1.0 + 1.0)
        assert usage.details[-1]["backend"] == ModelBackend.OPENAI_RESPONSES

    def test_shares_pricing_table_with_chat_completions(self):
        # Same self.openai_pricing lookup as OPENAI_CHAT — pricing is
        # per-model, not per-endpoint.
        usage = LLMfyUsage(
            openai_pricing={"shared-model": {"input": 1.0, "output": 1.0}}
        )
        usage.update(
            type=ServiceType.LLM,
            backend=ModelBackend.OPENAI_RESPONSES,
            model="shared-model",
            usage={"input_tokens": 1_000_000, "output_tokens": 0},
        )
        assert usage.total_cost == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Bedrock
# ---------------------------------------------------------------------------


class TestBedrockConverseUpdate:
    def test_basic_cost_uses_env_region(self, monkeypatch):
        monkeypatch.setenv("AWS_BEDROCK_REGION", "us-east-1")
        usage = LLMfyUsage(
            bedrock_pricing={"claude-x": {"us-east-1": {"input": 3.0, "output": 15.0}}}
        )
        usage.update(
            type=ServiceType.LLM,
            backend=ModelBackend.BEDROCK_CONVERSE,
            model="claude-x",
            usage={"inputTokens": 1000, "outputTokens": 500},
        )
        assert usage.total_cost == pytest.approx(
            (1000 / 1_000 * 3.0) + (500 / 1_000 * 15.0)
        )

    def test_missing_region_for_known_model_raises_key_error(self, monkeypatch):
        # Unlike "model not found" (warned, not raised), a present model with
        # a region that isn't priced propagates a raw KeyError.
        monkeypatch.setenv("AWS_BEDROCK_REGION", "eu-west-1")
        usage = LLMfyUsage(
            bedrock_pricing={"claude-x": {"us-east-1": {"input": 3.0, "output": 15.0}}}
        )
        with pytest.raises(KeyError):
            usage.update(
                type=ServiceType.LLM,
                backend=ModelBackend.BEDROCK_CONVERSE,
                model="claude-x",
                usage={"inputTokens": 1000, "outputTokens": 500},
            )

    def test_unknown_model_warns(self, monkeypatch):
        monkeypatch.setenv("AWS_BEDROCK_REGION", "us-east-1")
        usage = LLMfyUsage(
            bedrock_pricing={"known": {"us-east-1": {"input": 1.0, "output": 1.0}}}
        )
        with pytest.warns(UserWarning):
            usage.update(
                type=ServiceType.LLM,
                backend=ModelBackend.BEDROCK_CONVERSE,
                model="unknown",
                usage={"inputTokens": 10, "outputTokens": 5},
            )

    def test_cache_default_rates_are_10_percent_read_125_percent_write(
        self, monkeypatch
    ):
        monkeypatch.setenv("AWS_BEDROCK_REGION", "us-east-1")
        usage = LLMfyUsage(
            bedrock_pricing={"claude-x": {"us-east-1": {"input": 10.0, "output": 20.0}}}
        )
        usage.update(
            type=ServiceType.LLM,
            backend=ModelBackend.BEDROCK_CONVERSE,
            model="claude-x",
            usage={
                "inputTokens": 1000,
                "outputTokens": 0,
                "cacheReadInputTokens": 1000,
                "cacheWriteInputTokens": 1000,
            },
        )
        # i_price = 1*10 = 10 ; cache_r = 1*10*0.10 = 1 ; cache_w = 1*10*1.25 = 12.5
        assert usage.total_cost == pytest.approx(10 + 1 + 12.5)


# ---------------------------------------------------------------------------
# Anthropic
# ---------------------------------------------------------------------------


class TestAnthropicMessagesUpdate:
    def test_flat_pricing_no_region_dimension(self):
        usage = LLMfyUsage(
            anthropic_pricing={"claude-sonnet-5": {"input": 3.3, "output": 16.5}}
        )
        usage.update(
            type=ServiceType.LLM,
            backend=ModelBackend.ANTHROPIC_MESSAGES,
            model="claude-sonnet-5",
            usage={"input_tokens": 1_000_000, "output_tokens": 500_000},
        )
        assert usage.total_cost == pytest.approx(3.3 + 8.25)

    def test_cache_fields_use_anthropic_native_key_names(self):
        usage = LLMfyUsage(anthropic_pricing={"m": {"input": 10.0, "output": 20.0}})
        usage.update(
            type=ServiceType.LLM,
            backend=ModelBackend.ANTHROPIC_MESSAGES,
            model="m",
            usage={
                "input_tokens": 1000,
                "output_tokens": 0,
                "cache_creation_input_tokens": 1000,
                "cache_read_input_tokens": 1000,
            },
        )
        assert usage.cache_write_tokens == 1000
        assert usage.cache_read_tokens == 1000
        # Anthropic pricing defaults to token_unit=1_000_000 (per-million),
        # unlike Bedrock's 1_000 (per-thousand) default.
        # i_price = 1000/1e6*10.0 = 0.01
        # cache_r = 1000/1e6*(10.0*0.10) = 0.001 ; cache_w = 1000/1e6*(10.0*1.25) = 0.0125
        assert usage.total_cost == pytest.approx(0.01 + 0.001 + 0.0125)


# ---------------------------------------------------------------------------
# Google AI
# ---------------------------------------------------------------------------


class TestGoogleAIUpdate:
    def test_flat_pricing(self):
        usage = LLMfyUsage(googleai_pricing={"m": {"input": 0.10, "output": 0.40}})
        usage.update(
            type=ServiceType.LLM,
            backend=ModelBackend.GOOGLE_GENERATE,
            model="m",
            usage={"prompt_token_count": 1_000_000, "candidates_token_count": 500_000},
        )
        assert usage.total_cost == pytest.approx(0.10 + 0.20)

    def test_threshold_tier_selects_high_rate_when_exceeded(self):
        usage = LLMfyUsage(
            googleai_pricing={
                "m": {
                    "input": 1.0,
                    "output": 2.0,
                    "input_high": 2.0,
                    "output_high": 4.0,
                    "threshold": 1000,
                }
            }
        )
        usage.update(
            type=ServiceType.LLM,
            backend=ModelBackend.GOOGLE_GENERATE,
            model="m",
            usage={"prompt_token_count": 2000, "candidates_token_count": 1000},
        )
        assert usage.total_cost == pytest.approx(
            (2000 / 1_000_000 * 2.0) + (1000 / 1_000_000 * 4.0)
        )

    def test_threshold_tier_not_exceeded_uses_normal_rate(self):
        usage = LLMfyUsage(
            googleai_pricing={
                "m": {
                    "input": 1.0,
                    "output": 2.0,
                    "input_high": 2.0,
                    "output_high": 4.0,
                    "threshold": 1000,
                }
            }
        )
        usage.update(
            type=ServiceType.LLM,
            backend=ModelBackend.GOOGLE_GENERATE,
            model="m",
            usage={"prompt_token_count": 500, "candidates_token_count": 100},
        )
        assert usage.total_cost == pytest.approx(
            (500 / 1_000_000 * 1.0) + (100 / 1_000_000 * 2.0)
        )

    def test_per_type_pricing_weighted_by_content_type(self):
        usage = LLMfyUsage(
            googleai_pricing={
                "m": {
                    "input": {"default": 1.0, "text": 0.5, "image": 2.0},
                    "output": 3.0,
                }
            }
        )
        usage.update(
            type=ServiceType.LLM,
            backend=ModelBackend.GOOGLE_GENERATE,
            model="m",
            usage={
                "prompt_token_count": 1000,
                "candidates_token_count": 200,
                "text_token_count": 600,
                "image_token_count": 400,
            },
        )
        expected_input = (600 / 1_000_000 * 0.5) + (400 / 1_000_000 * 2.0)
        expected_output = 200 / 1_000_000 * 3.0
        assert usage.total_cost == pytest.approx(expected_input + expected_output)

    def test_per_type_pricing_without_breakdown_falls_back_to_default(self):
        usage = LLMfyUsage(
            googleai_pricing={
                "m": {"input": {"default": 1.0, "text": 0.5}, "output": 3.0}
            }
        )
        usage.update(
            type=ServiceType.LLM,
            backend=ModelBackend.GOOGLE_GENERATE,
            model="m",
            usage={"prompt_token_count": 1000, "candidates_token_count": 0},
            # no text/image/video/audio token counts given -> has_type_breakdown=False
        )
        assert usage.total_cost == pytest.approx(1000 / 1_000_000 * 1.0)

    def test_cache_read_discount_defaults_to_75_percent_off(self):
        usage = LLMfyUsage(googleai_pricing={"m": {"input": 0.10, "output": 0.40}})
        usage.update(
            type=ServiceType.LLM,
            backend=ModelBackend.GOOGLE_GENERATE,
            model="m",
            usage={
                "prompt_token_count": 1_000_000,
                "candidates_token_count": 0,
                "cached_content_token_count": 200_000,
            },
        )
        # i_price = 1.0*0.10 = 0.10 (full input priced, cache is a rebate)
        # cache_savings = 0.2*0.10 - 0.2*0.10*0.25 = 0.02 - 0.005 = 0.015
        # total = i_price - cache_savings + o_price = 0.10 - 0.015 + 0 = 0.085
        assert usage.total_cost == pytest.approx(0.085)
        assert usage.cache_read_tokens == 200_000

    def test_unknown_model_warns(self):
        usage = LLMfyUsage(googleai_pricing={"known": {"input": 1.0, "output": 1.0}})
        with pytest.warns(UserWarning):
            usage.update(
                type=ServiceType.LLM,
                backend=ModelBackend.GOOGLE_GENERATE,
                model="unknown",
                usage={"prompt_token_count": 10, "candidates_token_count": 5},
            )


# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------


class TestEmbeddingUpdates:
    def test_openai_embedding_forces_zero_output_tokens(self):
        usage = LLMfyUsage(
            openai_pricing={"embed-model": {"input": 0.02, "output": 999}}
        )
        usage.update(
            type=ServiceType.EMBEDDING,
            provider=ServiceProvider.OPENAI,
            model="embed-model",
            usage={"prompt_tokens": 1_000_000},
        )
        assert usage.output_tokens == 0
        assert usage.total_cost == pytest.approx(0.02)
        assert usage.details[-1]["type"] == ServiceType.EMBEDDING
        assert "backend" not in usage.details[-1]

    def test_bedrock_embedding_uses_hyphenated_usage_key(self, monkeypatch):
        monkeypatch.setenv("AWS_BEDROCK_REGION", "us-east-1")
        usage = LLMfyUsage(
            bedrock_pricing={"titan-embed": {"us-east-1": {"input": 0.1, "output": 0}}}
        )
        usage.update(
            type=ServiceType.EMBEDDING,
            provider=ServiceProvider.BEDROCK,
            model="titan-embed",
            usage={"x-amzn-bedrock-input-token-count": 1_000},
        )
        assert usage.input_tokens == 1_000
        assert usage.output_tokens == 0

    def test_googleai_embedding_uses_default_key_for_dict_pricing(self):
        usage = LLMfyUsage(
            googleai_pricing={"embed": {"input": {"default": 0.05}, "output": 0}}
        )
        usage.update(
            type=ServiceType.EMBEDDING,
            provider=ServiceProvider.GOOGLE,
            model="embed",
            usage={"prompt_token_count": 1_000_000},
        )
        assert usage.total_cost == pytest.approx(0.05)


# ---------------------------------------------------------------------------
# to_dict / repr / reset
# ---------------------------------------------------------------------------


class TestToDictAndRepr:
    def test_to_dict_shape(self):
        usage = LLMfyUsage(openai_pricing={"m": {"input": 1.0, "output": 1.0}})
        usage.update(
            type=ServiceType.LLM,
            backend=ModelBackend.OPENAI_CHAT,
            model="m",
            usage={"prompt_tokens": 1, "completion_tokens": 1},
        )
        d = usage.to_dict()
        assert d["total_request"] == 1
        assert d["tokens"]["total_tokens"] == 2
        assert "total_cost_formatted" in d["costs"]

    def test_trimmed_float_formatting_strips_trailing_zeros(self):
        usage = LLMfyUsage()
        assert usage.to_dict()["costs"]["total_cost_formatted"] == "0"

    def test_repr_omits_cache_section_when_no_cache_activity(self):
        usage = LLMfyUsage(openai_pricing={"m": {"input": 1.0, "output": 1.0}})
        usage.update(
            type=ServiceType.LLM,
            backend=ModelBackend.OPENAI_CHAT,
            model="m",
            usage={"prompt_tokens": 1, "completion_tokens": 1},
        )
        assert "Cache:" not in repr(usage)

    def test_repr_includes_cache_section_when_cache_tokens_present(self):
        usage = LLMfyUsage(openai_pricing={"m": {"input": 1.0, "output": 1.0}})
        usage.update(
            type=ServiceType.LLM,
            backend=ModelBackend.OPENAI_CHAT,
            model="m",
            usage={
                "prompt_tokens": 100,
                "completion_tokens": 10,
                "prompt_tokens_details": {"cached_tokens": 50},
            },  # type: ignore
        )
        assert "Cache:" in repr(usage)

    def test_repr_omits_backend_line_for_embedding_details(self):
        usage = LLMfyUsage(openai_pricing={"m": {"input": 1.0, "output": 1.0}})
        usage.update(
            type=ServiceType.EMBEDDING,
            provider=ServiceProvider.OPENAI,
            model="m",
            usage={"prompt_tokens": 10},
        )
        assert "backend:" not in repr(usage)

    def test_repr_includes_backend_line_for_llm_details(self):
        usage = LLMfyUsage(openai_pricing={"m": {"input": 1.0, "output": 1.0}})
        usage.update(
            type=ServiceType.LLM,
            backend=ModelBackend.OPENAI_CHAT,
            model="m",
            usage={"prompt_tokens": 1, "completion_tokens": 1},
        )
        assert "backend:" in repr(usage)


class TestReset:
    def test_reset_zeroes_counters_but_keeps_pricing(self):
        usage = LLMfyUsage(openai_pricing={"m": {"input": 1.0, "output": 1.0}})
        usage.update(
            type=ServiceType.LLM,
            backend=ModelBackend.OPENAI_CHAT,
            model="m",
            usage={"prompt_tokens": 100, "completion_tokens": 100},
        )
        assert usage.total_request == 1
        usage.reset()
        assert usage.total_request == 0
        assert usage.total_tokens == 0
        assert usage.total_cost == 0.0
        assert usage.details == []
        assert usage.raw_usages == []
        assert "m" in usage.openai_pricing  # pricing persists across reset
