from enum import Enum


class PIIType(str, Enum):
    """Categories of Personally Identifiable Information."""

    EMAIL = "EMAIL"
    PHONE_NUMBER = "PHONE_NUMBER"
    SSN = "SSN"
    CREDIT_CARD = "CREDIT_CARD"
    IP_ADDRESS = "IP_ADDRESS"
    DATE_OF_BIRTH = "DATE_OF_BIRTH"
    PASSPORT_NUMBER = "PASSPORT_NUMBER"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"'{self.value}'"
