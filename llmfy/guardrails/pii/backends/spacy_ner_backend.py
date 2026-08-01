from typing import ClassVar

from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.guardrails.pii.backends.base_ner_backend import BaseNERBackend, NEREntity

try:
    import xx_ent_pii_sm
except ImportError:
    xx_ent_pii_sm = None


class SpacyNERBackend(BaseNERBackend):
    """NER backend backed by the `xx_ent_pii_sm` spaCy pipeline
    (https://github.com/irufano/spacy_ner_pii). Not on PyPI — installed
    from a GitHub release wheel; see README for the install command.
    """

    # Loaded once per process, on first actual use — never at import time
    # or at SpacyNERBackend()/PIIGuard() construction time.
    _nlp: ClassVar[object | None] = None

    def __init__(self) -> None:
        if xx_ent_pii_sm is None:
            raise LLMfyException(
                "xx_ent_pii_sm package is not installed. It is required to "
                "detect PERSON_NAME/ADDRESS PII. Install spaCy with "
                '`pip install "llmfy[spacy]"`, then install the model with '
                "`pip install https://github.com/irufano/spacy_ner_pii/"
                "releases/download/v0.1.0/xx_ent_pii_sm-0.1.0-py3-none-any.whl`. "
                "Alternatively, exclude these two types: "
                "PIIGuard(exclude_types=[PIIType.PERSON_NAME, PIIType.ADDRESS])."
            )

    @classmethod
    def _get_pipeline(cls):
        if cls._nlp is None:
            cls._nlp = xx_ent_pii_sm.load()
        return cls._nlp

    def detect_entities(self, text: str) -> list[NEREntity]:
        nlp = self._get_pipeline()
        doc = nlp(text)
        return [
            NEREntity(
                text=ent.text,
                label=ent.label_,
                start=ent.start_char,
                end=ent.end_char,
            )
            for ent in doc.ents
        ]
