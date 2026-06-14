"""Reference consumer tests — the consumption half of the living loop (offline)."""

from __future__ import annotations

from pathlib import Path

from ontowiz_factory.consume import Consultation, consult
from ontowiz_runtime.registry import load_pack

PACK_DIR = Path(__file__).resolve().parents[3] / "packs" / "commercial_analytics" / "0.1.0"


class _FixedAgent:
    """A ChatAgent stub that returns a preset answer (no network)."""

    def __init__(self, answer: str) -> None:
        self.answer = answer

    def run(self, *, system, user, tools=None, tool_handler=None, max_tokens=1024):  # noqa: ANN001
        return self.answer


def test_consult_returns_answer_trust_and_helpful_signal():
    pack = load_pack(PACK_DIR)
    c = consult("Why did volume drop after a formulary change?", pack, _FixedAgent(
        "Formulary exclusion: the payer moved the brand to a non-preferred tier."
    ))
    assert isinstance(c, Consultation)
    assert c.answer
    assert c.trust.pack == "commercial_analytics@0.1.0"
    assert c.trust.artifacts_used  # provenance surfaced
    assert c.usage.helpful is True
    assert c.usage.artifact_id  # attributed to the top-ranked artifact


def test_low_confidence_answer_is_recorded_unhelpful():
    pack = load_pack(PACK_DIR)
    # the CTX router's own low-confidence phrase => the pack didn't cover it
    c = consult("Anything on quantum widgets?", pack, _FixedAgent(
        "I do not have enough information in the provided context to answer."
    ))
    assert c.usage.helpful is False


def test_correction_marks_unhelpful_and_carries_the_fix():
    pack = load_pack(PACK_DIR)
    c = consult(
        "Why did share drop?", pack, _FixedAgent("Generic guess."),
        correction="It was a biosimilar entry.",
    )
    assert c.usage.helpful is False
    assert c.usage.correction == "It was a biosimilar entry."
