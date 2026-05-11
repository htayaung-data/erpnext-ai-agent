from __future__ import annotations

import re
from typing import Any


_NUMBER_WORDS = {
	"one": 1,
	"two": 2,
	"three": 3,
	"four": 4,
	"five": 5,
	"six": 6,
	"seven": 7,
	"eight": 8,
	"nine": 9,
	"ten": 10,
	"eleven": 11,
	"twelve": 12,
	"thirteen": 13,
	"fourteen": 14,
	"fifteen": 15,
	"sixteen": 16,
	"seventeen": 17,
	"eighteen": 18,
	"nineteen": 19,
	"twenty": 20,
}
_NUMBER_TOKEN_PATTERN = r"\d{1,3}|" + "|".join(sorted(_NUMBER_WORDS, key=len, reverse=True))
_RANKED_SUBJECT_PATTERN = (
	r"products?|items?|suppliers?|vendors?|customers?|clients?|parties?|accounts?|"
	r"regions?|territor(?:y|ies)|documents?|invoices?|entries|rows"
)
_RANKING_ADJECTIVE_PATTERN = (
	r"top|leading|highest|highest[-\s]+revenue|largest|biggest|best|main|"
	r"lowest|least|bottom"
)
_TIME_UNIT_PATTERN = r"(?:day|days|week|weeks|month|months|year|years|quarter|quarters)"


def _normalize_text(value: Any) -> str:
	text = str(value or "").strip().lower()
	text = re.sub(r"[–—]", "-", text)
	text = re.sub(r"\s+", " ", text)
	return text


def _parse_number_token(value: str) -> int:
	token = _normalize_text(value)
	if not token:
		return 0
	if token.isdigit():
		try:
			return int(token)
		except Exception:
			return 0
	return _NUMBER_WORDS.get(token, 0)


def _bounded_limit(value: int, max_limit: int) -> int:
	limit = int(max(0, value or 0))
	if limit <= 0:
		return 0
	return max(1, min(limit, max(1, int(max_limit or 1))))


def _is_time_window_after(text: str, end_index: int) -> bool:
	return bool(re.match(r"\s+" + _TIME_UNIT_PATTERN + r"\b", text[end_index:]))


def extract_requested_top_n(message: Any, *, default_limit: int = 0, max_limit: int = 100) -> int:
	"""Extract an explicit ranked-row limit from governed business language.

	This intentionally stays structural: it recognizes row-count requests such
	as "top five suppliers" and "seven highest-revenue products" while avoiding
	time windows like "last 7 days".
	"""

	text = _normalize_text(message)
	if not text:
		return default_limit
	prefix_match = re.search(r"\b(?:top|last|latest)\s+(?P<num>" + _NUMBER_TOKEN_PATTERN + r")\b", text)
	if prefix_match and not _is_time_window_after(text, prefix_match.end()):
		limit = _bounded_limit(_parse_number_token(prefix_match.group("num")), max_limit)
		if limit:
			return limit

	subject_match = re.search(
		r"\b(?P<num>"
		+ _NUMBER_TOKEN_PATTERN
		+ r")\s+(?:(?:"
		+ _RANKING_ADJECTIVE_PATTERN
		+ r")[-\s]+){1,4}(?:[a-z0-9()&/.-]+[-\s]+){0,4}(?:"
		+ _RANKED_SUBJECT_PATTERN
		+ r")\b",
		text,
	)
	if subject_match:
		limit = _bounded_limit(_parse_number_token(subject_match.group("num")), max_limit)
		if limit:
			return limit
	return default_limit
