"""Response validation and sanitization for the AI Clinical Assistant.

This module implements :class:`ResponseValidator`, the single component
responsible for validating and sanitizing AI-generated responses before
they are returned to the user.

``ResponseValidator`` has exactly one responsibility: response
validation and sanitization. It never calls an LLM, builds prompts,
modifies conversation memory, accesses providers, or accesses a
database.
"""

from app.ai_clinical_assistant.exceptions import ResponseValidationError
from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)

DEFAULT_MAX_LENGTH: int = 3000
TRUNCATION_SUFFIX: str = "..."

MEDICAL_DISCLAIMER: str = (
    "This information is for educational purposes only and should not replace "
    "professional medical advice. Please consult a qualified healthcare "
    "professional."
)

# Phrases that read as absolute, unqualified medical statements, mapped to
# safer, hedged wording. Matching is case-insensitive and uses plain
# substring search only (no regex).
DEFAULT_PROHIBITED_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("you definitely have", "The findings may suggest"),
    ("you certainly have", "The findings may suggest"),
    ("you are diagnosed with", "The findings may suggest"),
    ("this confirms", "The available information may indicate"),
    ("diagnosis:", "The available information may indicate:"),
    ("without doubt", "the available information suggests"),
)


class ResponseValidator:
    """Validate and sanitize AI Clinical Assistant responses.

    This class has a single responsibility: taking a raw response
    string produced elsewhere in the system and running it through a
    fixed pipeline of whitespace cleanup, prohibited-claim replacement,
    disclaimer enforcement, and length limiting, before it is returned
    to the user. It never calls an LLM provider, builds prompts,
    modifies conversation memory, or accesses providers or a database.

    Attributes:
        _max_length: The default maximum response length, in
            characters.
        _disclaimer: The standard medical disclaimer text.
        _prohibited_replacements: Ordered pairs of prohibited phrases
            and their safer replacements.
    """

    def __init__(self, max_length: int = DEFAULT_MAX_LENGTH) -> None:
        """Initialize the ResponseValidator.

        Args:
            max_length: The default maximum response length, in
                characters, used by :meth:`validate`. Defaults to
                :data:`DEFAULT_MAX_LENGTH`.
        """
        self._max_length: int = max_length
        self._disclaimer: str = MEDICAL_DISCLAIMER
        self._prohibited_replacements: tuple[tuple[str, str], ...] = DEFAULT_PROHIBITED_REPLACEMENTS

        logger.info("ResponseValidator initialized.")

    def validate(self, response: str) -> str:
        """Run the full validation and sanitization pipeline on a response.

        Pipeline, in order: reject empty input, normalize whitespace,
        replace dangerous absolute medical claims, ensure a medical
        disclaimer is present, and enforce the maximum length.

        Args:
            response: The raw response text to validate.

        Returns:
            str: The cleaned, sanitized response.

        Raises:
            ResponseValidationError: If ``response`` is ``None``, empty,
                or whitespace-only.
        """
        logger.info("Validation started.")

        self.validate_not_empty(response)

        cleaned = self.remove_extra_whitespace(response)
        cleaned = self.remove_prohibited_claims(cleaned)
        cleaned = self.append_disclaimer(cleaned)
        cleaned = self.enforce_length_limit(cleaned, max_length=self._max_length)

        logger.info("Validation completed.")
        return cleaned

    def remove_extra_whitespace(self, response: str) -> str:
        """Normalize whitespace without altering sentence wording.

        Strips leading and trailing whitespace from the overall
        response, removes trailing spaces from each line, and collapses
        multiple consecutive blank lines into a single blank line. No
        word or sentence content is modified.

        Args:
            response: The response text to normalize.

        Returns:
            str: The whitespace-normalized response.
        """
        lines = [line.rstrip() for line in response.split("\n")]

        normalized_lines: list[str] = []
        previous_line_blank = False
        for line in lines:
            is_blank = line == ""
            if is_blank and previous_line_blank:
                continue
            normalized_lines.append(line)
            previous_line_blank = is_blank

        return "\n".join(normalized_lines).strip()

    def enforce_length_limit(self, response: str, max_length: int = DEFAULT_MAX_LENGTH) -> str:
        """Truncate a response that exceeds the maximum allowed length.

        If ``response`` exceeds ``max_length`` characters, it is safely
        truncated at a word boundary (no word is split in half) and an
        ellipsis is appended.

        Args:
            response: The response text to check and, if necessary,
                truncate.
            max_length: The maximum allowed length, in characters.
                Defaults to :data:`DEFAULT_MAX_LENGTH`.

        Returns:
            str: The original response if it is within the limit,
            otherwise a word-safe truncated response ending in
            ``"..."``.
        """
        if len(response) <= max_length:
            return response

        budget = max(max_length - len(TRUNCATION_SUFFIX), 0)
        truncated = response[:budget]

        last_space_index = truncated.rfind(" ")
        if last_space_index > 0:
            truncated = truncated[:last_space_index]

        truncated = truncated.rstrip()

        logger.info("Response truncated.")
        return f"{truncated}{TRUNCATION_SUFFIX}"

    def contains_medical_disclaimer(self, response: str) -> bool:
        """Check whether a response already contains a medical disclaimer.

        The check is case-insensitive and looks for the combination of
        "consult" together with "healthcare professional" anywhere in
        the text, so it recognizes both generic disclaimer wording and
        the exact disclaimer appended by :meth:`append_disclaimer`.

        Args:
            response: The response text to check.

        Returns:
            bool: ``True`` if the response already contains disclaimer
            wording, ``False`` otherwise.
        """
        lowered = response.lower()
        return "consult" in lowered and "healthcare professional" in lowered

    def append_disclaimer(self, response: str) -> str:
        """Append the standard medical disclaimer if it is not already present.

        Args:
            response: The response text to check and, if necessary,
                append the disclaimer to.

        Returns:
            str: The response with the disclaimer appended, or the
            original response unchanged if a disclaimer was already
            present. The disclaimer is never appended more than once.
        """
        if self.contains_medical_disclaimer(response):
            return response

        logger.info("Disclaimer added.")

        if not response:
            return self._disclaimer

        return f"{response}\n\n{self._disclaimer}"

    def remove_prohibited_claims(self, response: str) -> str:
        """Replace absolute medical claims with safer, hedged wording.

        Uses simple, case-insensitive phrase replacement only; no
        regular expressions are used.

        Args:
            response: The response text to sanitize.

        Returns:
            str: The response with any prohibited phrases replaced by
            safer wording.
        """
        updated = response
        replaced_any = False

        for phrase, replacement in self._prohibited_replacements:
            if phrase in updated.lower():
                updated = self._replace_case_insensitive(updated, phrase, replacement)
                replaced_any = True

        if replaced_any:
            logger.info("Prohibited claims replaced.")

        return updated

    def validate_not_empty(self, response: str) -> None:
        """Ensure a response is not empty after stripping whitespace.

        Args:
            response: The response text to check.

        Raises:
            ResponseValidationError: If ``response`` is ``None``, empty,
                or whitespace-only.
        """
        if response is None or not response.strip():
            raise ResponseValidationError("Response must not be empty.")

    def _replace_case_insensitive(self, text: str, target: str, replacement: str) -> str:
        """Replace every case-insensitive occurrence of a phrase in text.

        Performs plain substring search and slicing only; no regular
        expressions are used. The casing of ``text`` outside of matched
        occurrences is preserved.

        Args:
            text: The text to search within.
            target: The phrase to find, matched case-insensitively.
            replacement: The text to substitute in place of each match.

        Returns:
            str: The text with every case-insensitive occurrence of
            ``target`` replaced by ``replacement``.
        """
        lower_text = text.lower()
        lower_target = target.lower()
        target_length = len(target)

        segments: list[str] = []
        search_start = 0

        while True:
            match_index = lower_text.find(lower_target, search_start)
            if match_index == -1:
                segments.append(text[search_start:])
                break
            segments.append(text[search_start:match_index])
            segments.append(replacement)
            search_start = match_index + target_length

        return "".join(segments)