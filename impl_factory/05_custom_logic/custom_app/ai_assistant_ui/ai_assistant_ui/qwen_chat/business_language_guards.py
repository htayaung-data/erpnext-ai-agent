from __future__ import annotations

import re


_PREDICTIVE_GUARANTEE_PATTERN = re.compile(
	r"\b(?:guarantee|forecast|predict|prediction|default\s+probability)\b",
	re.IGNORECASE,
)
_WHO_WILL_PAYMENT_PATTERN = re.compile(
	r"\b(?:who|which|what)\b.{0,60}\bwill\b.{0,40}\b(?:pay|settle|repay|default)\b",
	re.IGNORECASE,
)
_WILL_PAYMENT_OUTCOME_PATTERN = re.compile(
	r"\bwill\b.{0,80}\b(?:pay|settle|repay|default)\b",
	re.IGNORECASE,
)
_SPECULATIVE_CAUSAL_PATTERN = re.compile(
	r"\b(?:probably|likely|maybe|might|seems?|appears?|suspect|infer|inferred|because|caused?|due\s+to|reason\s+for|why)\b",
	re.IGNORECASE,
)
_SUBJECTIVE_OPERATIONAL_PATTERN = re.compile(
	r"\b(?:dissatisfied|unhappy|angry|complain(?:ed|t|ts)?|disput(?:e|ed|es)|refus(?:e|ed|al)|motive|intent|intention|deliberately|intentionally|fraud|churn)\b",
	re.IGNORECASE,
)
_PROBABLY_BECAUSE_PATTERN = re.compile(
	r"\bprobably\b.{0,80}\bbecause\b",
	re.IGNORECASE,
)
_DELAY_REASON_PATTERN = re.compile(
	r"\bdelay(?:ed)?\b.{0,80}\b(?:because|due\s+to|reason)\b",
	re.IGNORECASE,
)


def looks_like_predictive_guarantee_claim(message: str) -> bool:
	text = " ".join(str(message or "").strip().lower().split())
	if not text:
		return False
	if _PREDICTIVE_GUARANTEE_PATTERN.search(text):
		return True
	return bool(_WHO_WILL_PAYMENT_PATTERN.search(text) or _WILL_PAYMENT_OUTCOME_PATTERN.search(text))


def looks_like_unsupported_operational_inference_claim(message: str) -> bool:
	text = " ".join(str(message or "").strip().lower().split())
	if not text:
		return False
	if _PROBABLY_BECAUSE_PATTERN.search(text) or _DELAY_REASON_PATTERN.search(text):
		return True
	if _SUBJECTIVE_OPERATIONAL_PATTERN.search(text) and _SPECULATIVE_CAUSAL_PATTERN.search(text):
		return True
	return False
