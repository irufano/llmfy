from pydantic import BaseModel


class ModelPricing(BaseModel):
    """ModelPricing Class"""
    token_input: float
    token_output: float
    token_unit: int = 1_000_000

    def __repr__(self) -> str:
        return str(self.model_dump())