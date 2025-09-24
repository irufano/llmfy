import os
import re
import warnings
from typing import Any, Dict, List, Optional

from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.llmfy_core.models.bedrock.bedrock_pricing_list import BEDROCK_PRICING
from llmfy.llmfy_core.models.model_pricing import ModelPricing
from llmfy.llmfy_core.models.openai.openai_pricing_list import OPENAI_PRICING
from llmfy.llmfy_core.service_provider import ServiceProvider
from llmfy.llmfy_core.service_type import ServiceType


class LLMfyUsage:
    """
    LLMfyUsage class.

    Count all provider token usage.

    Usage in `OpenAIModel`, `openai_usage_tracker` and `track_openai_usage`
    """

    def __init__(
        self,
        openai_pricing: Optional[Dict[str, Any]] = None,
        bedrock_pricing: Optional[Dict[str, Any]] = None,
    ):
        if openai_pricing:
            if not self.__is_valid_openai_pricing_structure(openai_pricing):
                error = """
				Please provide the right pricing structure for openai, example:
				```
				{
					"gpt-4o": {
						"input": 2.50,
						"output": 10.00
					},
					"gpt-4o-mini": {
						"input": 0.15,
						"output": 0.60
					},
					"gpt-3.5-turbo": {
						"input": 0.05,
						"output": 1.50
					}
				}
				```
				"""
                raise LLMfyException(error)

        if bedrock_pricing:
            if not self.__is_valid_bedrock_pricing_structure(bedrock_pricing):
                error = """
                Please provide the right pricing structure for bedrock, example:
                ```
                {
                    "anthropic.claude-3-5-sonnet-20240620-v1:0": {
                        "us-east-1": {
                            "region": "US East (N. Virginia)",
                            "input": 0.003,
                            "output": 0.015,
                        },
                        "us-west-2": {
                            "region": "US West (Oregon)",
                            "input": 0.003,
                            "output": 0.015,
                        },
                    },
                    "anthropic.claude-3-5-sonnet-20241022-v2:0": {
                        "us-east-1": {
                            "region": "US East (N. Virginia)",
                            "input": 0.003,
                            "output": 0.015,
                        },
                        "us-west-2": {
                            "region": "US West (Oregon)",
                            "input": 0.003,
                            "output": 0.015,
                        },
                    }
                }
                ```
                """
                raise LLMfyException(error)

        self.total_request: int = 0
        self.output_tokens: int = 0
        self.input_tokens: int = 0
        self.total_tokens: int = 0
        self.total_cost: float = 0.0
        self.raw_usages: List[Dict[str, int]] = []
        self.openai_pricing: Dict[str, ModelPricing] = (
            self._load_openai_pricing(pricing_source=openai_pricing or OPENAI_PRICING)
            or {}
        )
        self.bedrock_pricing: Dict[str, Dict[str, ModelPricing]] = (
            self._load_bedrock_pricing(
                pricing_source=bedrock_pricing or BEDROCK_PRICING
            )
            or {}
        )
        self.details: List[Dict[str, Any]] = []

    def to_dict(self):
        return {
            "total_request": self.total_request,
            "tokens": {
                "total_tokens": self.total_tokens,
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
            },
            "costs": {
                "total_cost": self.total_cost,
                "total_cost_formatted": self.__format_trimmed_float(self.total_cost),
            },
            "details": self.details,
        }

    def __repr__(self) -> str:
        # rounded_up = math.ceil(self.total_cost * 1000000) / 1000000
        return (
            f"\n------------------\n"
            f"USAGE: \n\n"
            f"Total Tokens: {self.total_tokens}\n"
            f"\tInput Tokens: {self.input_tokens}\n"
            f"\tOutput Tokens: {self.output_tokens}\n"
            f"Total Requests: {self.total_request}\n"
            # f"Total Cost (USD): ${rounded_up:.6f}"
            f"Total Cost (USD): ${self.total_cost}\n"
            f"Total Cost (USD formatted): ${self.__format_trimmed_float(self.total_cost)}\n\n"
            f"Request Details:\n"
            + "\n".join(
                f"{i + 1}. {detail['model']} "
                f"\n\tprovider: {detail['provider']} "
                f"\n\ttype: {detail['type']} "
                f"\n\tinput_tokens: {detail['input_tokens']} "
                f"\n\toutput_tokens: {detail['output_tokens']} "
                f"\n\ttotal_tokens: {detail['total_tokens']} "
                f"\n\tinput_price: {detail['input_price']} "
                f"\n\toutput_price: {detail['output_price']} "
                f"\n\tprice_per_tokens: {detail['price_per_tokens']} "
                f"\n\ttotal_cost (USD): {detail['total_cost']} "
                f"\n\ttotal_cost (USD formatted): {self.__format_trimmed_float(detail.get('total_cost', 0))}\n"
                for i, detail in enumerate(self.details)
            )
            + "\n------------------\n"
        )

    def __format_trimmed_float(self, value: float) -> str:
        """
        Format a float with up to 9 decimal places,
        trimming unnecessary trailing zeros.
        """
        formatted = f"{value:.9f}"
        if "." in formatted:
            formatted = formatted.rstrip("0").rstrip(".")
        return formatted

    def __is_valid_openai_pricing_structure(self, pricing: Any) -> bool:
        if not isinstance(pricing, dict):
            return False
        for outer_dict in pricing.values():
            if not isinstance(outer_dict, dict):
                return False
            for value in outer_dict.values():
                if not isinstance(value, (float, int)):
                    return False
        return True

    def __is_valid_bedrock_pricing_structure(self, pricing: Any) -> bool:
        # First check if it's a dictionary
        if not isinstance(pricing, dict):
            return False

        # Check first level values are dictionaries
        for outer_dict in pricing.values():
            if not isinstance(outer_dict, dict):
                return False

            # Check second level values are dictionaries
            for inner_dict in outer_dict.values():
                if not isinstance(inner_dict, dict):
                    return False

        return True

    def _load_openai_pricing(
        self,
        pricing_source: Dict[str, Dict[str, Any]],
    ) -> Dict[str, ModelPricing]:
        """
        Load openai pricing from dictionary.
        """
        # Price per 1M tokens for different models (USD)
        # https://platform.openai.com/docs/pricing
        pricing_data = pricing_source
        return {
            model: ModelPricing(token_input=data["input"], token_output=data["output"])
            for model, data in pricing_data.items()
        }

    def _load_bedrock_pricing(
        self,
        pricing_source: Dict[str, Dict[str, Dict[str, Any]]],
    ) -> Dict[str, Dict[str, ModelPricing]]:
        """
        Load bedrock pricing from dictionary.
        """
        # Price per 1K tokens for different models (USD)
        # https://aws.amazon.com/bedrock/pricing/
        # https://aws.amazon.com/bedrock/pricing/
        # https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.RegionsAndAvailabilityZones.html
        pricing_data = pricing_source
        return {
            model: {
                region: ModelPricing(
                    token_input=pricing["input"],
                    token_output=pricing["output"],
                )
                for region, pricing in regions.items()
            }
            for model, regions in pricing_data.items()
        }

    def update(
        self,
        provider: ServiceProvider,
        type: ServiceType,
        model: str,
        usage: Dict[str, int],
    ) -> None:
        """
        Update usage statistics and calculate price.

        Args:
            provider (ModelProvider): Model provider
            model (str): Model name
            usage (Dict[str, int]): Dictionary containing token counts
        """
        match type:
            case ServiceType.LLM:
                match provider:
                    case ServiceProvider.OPENAI:
                        self.__openai_update(model=model, usage=usage)
                    case ServiceProvider.BEDROCK:
                        self.__bedrock_update(model=model, usage=usage)
                    case _:
                        pass
            case ServiceType.EMBEDDING:
                match provider:
                    case ServiceProvider.OPENAI:
                        self.__openai_embedding_update(model=model, usage=usage)
                    case ServiceProvider.BEDROCK:
                        self.__bedrock_embedding_update(model=model, usage=usage)
                    case _:
                        pass
            case _:
                pass

    def __openai_update(
        self,
        model: str,
        usage: Dict[str, int],
    ) -> None:
        """
        OPENAI Update usage statistics and calculate price.

        Args:
            model (str): Model name
            usage (Dict[str, int]): Dictionary containing token counts
        """
        ONE_MILLION = 1000000

        self.raw_usages.append(usage)
        usage_dict = vars(usage) if hasattr(usage, "__dict__") else usage

        # usage per-request
        input_tokens = usage_dict.get("prompt_tokens", 0)
        output_tokens = usage_dict.get("completion_tokens", 0)
        total_tokens = input_tokens + output_tokens

        # usage accumulation
        self.total_request += 1
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_tokens += total_tokens

        # Calculate price
        price_info = None
        total_cost_per_request = 0

        if model in self.openai_pricing:
            price_info = self.openai_pricing[model]
            # pricing per-request
            i_price = (input_tokens / ONE_MILLION) * price_info.token_input
            o_price = (output_tokens / ONE_MILLION) * price_info.token_output
            total_cost_per_request = i_price + o_price

            # pricing accumulation
            self.total_cost += total_cost_per_request
        else:
            warnings.warn(
                "MODEL not found at specified openai pricing. You can add in custom prices with `llmfy_usage_tracker(openai_pricing=prices)`"
            )

        # add to details per-requestd
        self.details.append(
            {
                "model": model,
                "provider": ServiceProvider.OPENAI,
                "type": ServiceType.LLM,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "input_price": price_info.token_input if price_info else None,
                "output_price": price_info.token_output if price_info else None,
                "price_per_tokens": ONE_MILLION,
                "total_cost": total_cost_per_request,
            }
        )
        pass

    def __openai_embedding_update(self, model: str, usage: Dict) -> None:
        """
        Update usage statistics and calculate price.

        Args:
            model: Model name
            usage: usage of input token (for embedding use input token only).
        """

        def has_cross_region_inference_id(s):
            return bool(re.match(r"^.{2}\.", s))

        ONE_MILLION = 1000000

        self.raw_usages.append(usage)
        usage_dict = vars(usage) if hasattr(usage, "__dict__") else usage

        # usage per-request
        input_tokens = usage_dict.get("prompt_tokens", 0)
        output_tokens = 0  # in embedding no output tokens usage
        total_tokens = input_tokens + output_tokens

        # usage accumulation
        self.total_request += 1
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_tokens += total_tokens

        # Calculate price
        price_info = None
        total_cost_per_request = 0

        if model in self.openai_pricing:
            price_info = self.openai_pricing[model]
            # pricing per-request
            i_price = (input_tokens / ONE_MILLION) * price_info.token_input
            o_price = (output_tokens / ONE_MILLION) * price_info.token_output
            total_cost_per_request = i_price + o_price

            # pricing accumulation
            self.total_cost += total_cost_per_request
        else:
            warnings.warn(
                "MODEL not found at specified bedrock pricing. You can add in custom prices with `llmfy_usage_tracker(bedrock_pricing=prices)`"
            )

        # add to details per-request
        self.details.append(
            {
                "model": model,
                "provider": ServiceProvider.OPENAI,
                "type": ServiceType.EMBEDDING,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "input_price": price_info.token_input if price_info else None,
                "output_price": price_info.token_output if price_info else None,
                "price_per_tokens": ONE_MILLION,
                "total_cost": total_cost_per_request,
            }
        )
        pass

    def __bedrock_update(self, model: str, usage: Dict[str, int]) -> None:
        """
        Update usage statistics and calculate price.

        Args:
            model: Model name
            usage: Dictionary containing token counts
        """

        def has_cross_region_inference_id(s):
            return bool(re.match(r"^.{2}\.", s))

        ONE_K = 1000
        AWS_REGION = os.getenv("AWS_BEDROCK_REGION") or ""
        MODEL = model[3:] if has_cross_region_inference_id(model) else model

        self.raw_usages.append(usage)
        usage_dict = vars(usage) if hasattr(usage, "__dict__") else usage

        # usage per-request
        input_tokens = usage_dict.get("inputTokens", 0)
        output_tokens = usage_dict.get("outputTokens", 0)
        total_tokens = input_tokens + output_tokens

        # usage accumulation
        self.total_request += 1
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_tokens += total_tokens

        # Calculate price
        price_info = None
        total_cost_per_request = 0

        if MODEL in self.bedrock_pricing:
            price_info = self.bedrock_pricing[MODEL][AWS_REGION]

            # pricing per-request
            i_price = (input_tokens / ONE_K) * price_info.token_input
            o_price = (output_tokens / ONE_K) * price_info.token_output
            total_cost_per_request = i_price + o_price

            # pricing accumulation
            self.total_cost += total_cost_per_request
        else:
            warnings.warn(
                "MODEL not found at specified bedrock pricing. You can add in custom prices with `llmfy_usage_tracker(bedrock_pricing=prices)`"
            )

        # add to details per-request
        self.details.append(
            {
                "model": model,
                "provider": ServiceProvider.BEDROCK,
                "type": ServiceType.LLM,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "input_price": price_info.token_input if price_info else None,
                "output_price": price_info.token_output if price_info else None,
                "price_per_tokens": ONE_K,
                "total_cost": total_cost_per_request,
            }
        )
        pass

    def __bedrock_embedding_update(self, model: str, usage: Dict) -> None:
        """
        Update usage statistics and calculate price.

        Args:
            model: Model name
            usage: usage of input token (for embedding use input token only).
        """

        def has_cross_region_inference_id(s):
            return bool(re.match(r"^.{2}\.", s))

        ONE_K = 1000
        AWS_REGION = os.getenv("AWS_BEDROCK_REGION") or ""
        MODEL = model[3:] if has_cross_region_inference_id(model) else model

        self.raw_usages.append(usage)
        usage_dict = vars(usage) if hasattr(usage, "__dict__") else usage

        # usage per-request
        input_tokens = usage_dict.get("x-amzn-bedrock-input-token-count", 0)
        output_tokens = 0  # in embedding no output tokens usage
        total_tokens = input_tokens + output_tokens

        # usage accumulation
        self.total_request += 1
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_tokens += total_tokens

        # Calculate price
        price_info = None
        total_cost_per_request = 0

        if MODEL in self.bedrock_pricing:
            price_info = self.bedrock_pricing[MODEL][AWS_REGION]

            # pricing per-request
            i_price = (input_tokens / ONE_K) * price_info.token_input
            o_price = 0  # in embedding no output tokens usage
            total_cost_per_request = i_price + o_price

            # pricing accumulation
            self.total_cost += total_cost_per_request
        else:
            warnings.warn(
                "MODEL not found at specified bedrock pricing. You can add in custom prices with `llmfy_usage_tracker(bedrock_pricing=prices)`"
            )

        # add to details per-request
        self.details.append(
            {
                "model": model,
                "provider": ServiceProvider.BEDROCK,
                "type": ServiceType.EMBEDDING,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "input_price": price_info.token_input if price_info else None,
                "output_price": price_info.token_output if price_info else None,
                "price_per_tokens": ONE_K,
                "total_cost": total_cost_per_request,
            }
        )
        pass

    def reset(self):
        """
        Reset usage statistics and calculate price.
        """
        self.total_request = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        self.raw_usages = []
        self.details = []
