import os
import re
from typing import Any, Dict, List, Optional

from llmfy.llmfy_core.models.bedrock.bedrock_pricing_list import BEDROCK_PRICING
from llmfy.llmfy_core.models.model_pricing import ModelPricing
from llmfy.exception.llmfy_exception import LLMfyException


class BedrockUsage:
    """
    BedrockUsage class.

    Count bedrock token usage.

    Usage in `BedrockModel`, `bedrock_usage_tracker` and `track_bedrock_usage`
    """

    def __init__(self, pricing: Optional[Dict[str, Any]] = None):
        if pricing:
            if not self.__is_valid_pricing_structure(pricing):
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
        self.pricing: Dict[str, Dict[str, ModelPricing]] = (
            self._load_pricing(pricing_source=pricing or BEDROCK_PRICING) or {}
        )
        self.details: List[Dict[str, Any]] = []

    def __repr__(self) -> str:
        # rounded_up = math.ceil(self.total_cost * 1000000) / 1000000
        return (
            f"Total Tokens: {self.total_tokens}\n"
            f"\tInput Tokens: {self.input_tokens}\n"
            f"\tOutput Tokens: {self.output_tokens}\n"
            f"Total Requests: {self.total_request}\n"
            # f"Total Cost (USD): ${rounded_up:.6f}"
            f"Total Cost (USD): ${self.total_cost}\n"
            f"Total Cost (USD formatted): ${self.total_cost:.6f}\n\n"
            f"Details:\n"
            + "\n".join(
                f"{i + 1}. {detail['model']} "
                f"\n\tinput_tokens: {detail['input_tokens']} "
                f"\n\toutput_tokens: {detail['output_tokens']} "
                f"\n\ttotal_tokens: {detail['total_tokens']} "
                f"\n\tinput_price: {detail['input_price']} "
                f"\n\toutput_price: {detail['output_price']} "
                f"\n\tprice_per_tokens: {detail['price_per_tokens']} "
                f"\n\ttotal_cost (USD): {detail['total_cost']} "
                f"\n\ttotal_cost (USD formatted): {detail.get('total_cost', 0):.6f}\n"
                for i, detail in enumerate(self.details)
            )
        )

    def __is_valid_pricing_structure(self, pricing: Any) -> bool:
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

    def _load_pricing(
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

    def update(self, model: str, usage: Dict[str, int]) -> None:
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
        total_cost_per_request = 0
        if MODEL in self.pricing:
            price_info = self.pricing[MODEL][AWS_REGION]
            # pricing per-request
            i_price = (input_tokens / ONE_K) * price_info.token_input
            o_price = (output_tokens / ONE_K) * price_info.token_output
            total_cost_per_request = i_price + o_price

            # pricing accumulation
            input_price = (self.input_tokens / ONE_K) * price_info.token_input
            output_price = (self.output_tokens / ONE_K) * price_info.token_output
            self.total_cost = input_price + output_price

        # add to details per-request
        self.details.append(
            {
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "input_price": price_info.token_input,
                "output_price": price_info.token_output,
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
