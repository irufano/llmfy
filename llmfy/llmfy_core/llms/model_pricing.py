from pydantic import BaseModel


class ModelPricing(BaseModel):
    """ModelPricing Class"""
    token_input: float
    token_output: float

    def __repr__(self) -> str:
        return str(self.model_dump())