"""Prompt construction for the AI Clinical Assistant.

This module implements :class:`PromptBuilder`, the single component
responsible for converting already-prepared structured clinical context
into plain-text prompts that can later be sent to an LLM provider.

``PromptBuilder`` has exactly one responsibility: prompt construction.
It does not call any LLM, store or load conversation memory, build
context, validate responses, select providers, diagnose disease, or
recommend treatment. It is intentionally provider-independent and has no
dependency on any other module in the AI Clinical Assistant package.
"""

from typing import Any

from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)

NOT_AVAILABLE: str = "Not Available"
MAX_CONVERSATION_MESSAGES: int = 10

_PATIENT_KEYS: tuple[str, ...] = ("patient_information", "patient", "patient_info")
_HISTORY_KEYS: tuple[str, ...] = ("medical_history", "history")
_MEDICATION_KEYS: tuple[str, ...] = ("current_medications", "medications")
_ALLERGY_KEYS: tuple[str, ...] = ("allergies",)
_RISK_KEYS: tuple[str, ...] = ("risk_assessment", "risk")
_LABORATORY_KEYS: tuple[str, ...] = ("laboratory_results", "lab_results", "laboratory")
_SUMMARY_KEYS: tuple[str, ...] = ("clinical_summary", "summary")
_CONVERSATION_KEYS: tuple[str, ...] = (
    "conversation_history",
    "previous_conversation",
    "conversation",
)


def _lookup_first(structured_context: dict[str, Any], keys: tuple[str, ...]) -> Any:
    """Return the first present, truthy value for a set of candidate keys.

    Args:
        structured_context: The structured clinical context dictionary.
        keys: Candidate key names to look up, in priority order.

    Returns:
        Any: The first truthy value found for the given keys, or ``None``
        if none of the keys are present or all associated values are
        falsy.
    """
    for key in keys:
        value = structured_context.get(key)
        if value:
            return value
    return None


def _render_value(value: Any) -> str:
    """Render an arbitrary context value as readable plain text.

    Dictionaries are rendered as ``"Key: Value"`` lines. Lists and tuples
    are rendered as ``"- item"`` lines. Any other value is rendered via
    ``str()``. Falsy values render as :data:`NOT_AVAILABLE`.

    Args:
        value: The value to render.

    Returns:
        str: The rendered plain-text representation of ``value``.
    """
    if not value:
        return NOT_AVAILABLE

    if isinstance(value, dict):
        lines = [f"{str(key).replace('_', ' ')}: {item}" for key, item in value.items()]
        return "\n".join(lines) if lines else NOT_AVAILABLE

    if isinstance(value, (list, tuple)):
        lines = [f"- {item}" for item in value]
        return "\n".join(lines) if lines else NOT_AVAILABLE

    return str(value)


class PromptBuilder:
    """Convert structured clinical context into plain-text LLM prompts.

    This class has a single responsibility: prompt construction. It
    receives structured context that has already been prepared upstream
    (typically by a context-building component) and converts it into a
    deterministic, plain-text prompt. It never modifies the context it
    receives, never calls an LLM provider, and never stores conversation
    state.
    """

    def __init__(self) -> None:
        """Initialize the PromptBuilder.

        Takes no parameters and creates no global or mutable module-level
        state. Every instance is fully independent and safe to use with
        dependency injection.
        """
        logger.info("PromptBuilder initialized.")

    def build_system_prompt(self) -> str:
        """Build the deterministic system prompt for the AI Clinical Assistant.

        Returns:
            str: A plain-text system prompt instructing the assistant on
            its role, capabilities, and strict safety boundaries. The
            output is fully deterministic: it contains no randomness,
            timestamps, or identifiers, and will be identical on every
            call.
        """
        system_prompt = (
            "You are an AI Clinical Assistant.\n"
            "You provide educational clinical support to healthcare professionals and patients.\n"
            "You summarize laboratory findings in clear, plain language.\n"
            "You explain medical terminology so it is easy to understand.\n"
            "You may explain what abnormal laboratory values typically indicate.\n"
            "You never diagnose disease.\n"
            "You never prescribe medication.\n"
            "You never replace licensed physicians or other qualified healthcare providers.\n"
            "You never fabricate laboratory values that were not provided to you.\n"
            "You never fabricate patient history that was not provided to you.\n"
            "You must clearly state when the available information is insufficient to answer.\n"
            "You avoid hallucinations and do not invent facts.\n"
            "You respond professionally at all times.\n"
            "You remain strictly factual and grounded in the information provided.\n"
            "You avoid unnecessary repetition in your responses."
        )

        logger.info("System prompt generated.")
        return system_prompt

    def build_user_prompt(
        self,
        user_message: str,
        structured_context: dict[str, Any],
    ) -> str:
        """Build the user-facing prompt from structured context and a question.

        The structured context is read from but never modified. The
        returned prompt always contains every required section, in a
        fixed order, using ``"Not Available"`` for any section with no
        corresponding data.

        Args:
            user_message: The current question or message from the user.
            structured_context: Already-prepared structured clinical
                context (e.g., patient information, medical history,
                medications, allergies, risk assessment, laboratory
                results, clinical summary, and conversation history).

        Returns:
            str: A deterministic, plain-text prompt containing the
            ``PATIENT INFORMATION``, ``MEDICAL HISTORY``,
            ``CURRENT MEDICATIONS``, ``ALLERGIES``, ``RISK ASSESSMENT``,
            ``LABORATORY RESULTS``, ``CLINICAL SUMMARY``,
            ``PREVIOUS CONVERSATION``, and ``USER QUESTION`` sections, in
            that exact order.
        """
        user_question = user_message.strip() if user_message and user_message.strip() else NOT_AVAILABLE

        sections: list[tuple[str, str]] = [
            ("PATIENT INFORMATION", self._format_patient(structured_context)),
            ("MEDICAL HISTORY", self._format_history(structured_context)),
            ("CURRENT MEDICATIONS", self._format_medications(structured_context)),
            ("ALLERGIES", self._format_allergies(structured_context)),
            ("RISK ASSESSMENT", self._format_risk(structured_context)),
            ("LABORATORY RESULTS", self._format_laboratory(structured_context)),
            ("CLINICAL SUMMARY", self._format_summary(structured_context)),
            ("PREVIOUS CONVERSATION", self._format_conversation(structured_context)),
            ("USER QUESTION", user_question),
        ]

        prompt_blocks = [f"{title}\n\n{content}" for title, content in sections]
        user_prompt = "\n\n".join(prompt_blocks)

        logger.info("User prompt generated with %d sections.", len(sections))
        return user_prompt

    def build_complete_prompt(
        self,
        user_message: str,
        structured_context: dict[str, Any],
    ) -> str:
        """Build the complete prompt combining the system and user prompts.

        Args:
            user_message: The current question or message from the user.
            structured_context: Already-prepared structured clinical
                context, as consumed by :meth:`build_user_prompt`.

        Returns:
            str: A single plain-text string consisting of the system
            prompt followed by the user prompt.
        """
        system_prompt = self.build_system_prompt()
        user_prompt = self.build_user_prompt(user_message, structured_context)
        complete_prompt = f"{system_prompt}\n\n{user_prompt}"

        logger.info("Complete prompt generated.")
        return complete_prompt

    def _format_patient(self, structured_context: dict[str, Any]) -> str:
        """Format the patient information section.

        Args:
            structured_context: The structured clinical context.

        Returns:
            str: Plain-text patient information, or ``"Not Available"``.
        """
        value = _lookup_first(structured_context, _PATIENT_KEYS)
        return _render_value(value)

    def _format_history(self, structured_context: dict[str, Any]) -> str:
        """Format the medical history section.

        Args:
            structured_context: The structured clinical context.

        Returns:
            str: Plain-text medical history, or ``"Not Available"``.
        """
        value = _lookup_first(structured_context, _HISTORY_KEYS)
        return _render_value(value)

    def _format_medications(self, structured_context: dict[str, Any]) -> str:
        """Format the current medications section.

        Args:
            structured_context: The structured clinical context.

        Returns:
            str: Plain-text current medications, or ``"Not Available"``.
        """
        value = _lookup_first(structured_context, _MEDICATION_KEYS)
        return _render_value(value)

    def _format_allergies(self, structured_context: dict[str, Any]) -> str:
        """Format the allergies section.

        Args:
            structured_context: The structured clinical context.

        Returns:
            str: Plain-text allergy information, or ``"Not Available"``.
        """
        value = _lookup_first(structured_context, _ALLERGY_KEYS)
        return _render_value(value)

    def _format_risk(self, structured_context: dict[str, Any]) -> str:
        """Format the risk assessment section.

        Args:
            structured_context: The structured clinical context.

        Returns:
            str: Plain-text risk assessment information, or
            ``"Not Available"``.
        """
        value = _lookup_first(structured_context, _RISK_KEYS)
        return _render_value(value)

    def _format_laboratory(self, structured_context: dict[str, Any]) -> str:
        """Format the laboratory results section.

        Args:
            structured_context: The structured clinical context.

        Returns:
            str: Plain-text laboratory results, or ``"Not Available"``.
        """
        value = _lookup_first(structured_context, _LABORATORY_KEYS)
        return _render_value(value)

    def _format_summary(self, structured_context: dict[str, Any]) -> str:
        """Format the clinical summary section.

        Args:
            structured_context: The structured clinical context.

        Returns:
            str: Plain-text clinical summary, or ``"Not Available"``.
        """
        value = _lookup_first(structured_context, _SUMMARY_KEYS)
        return _render_value(value)

    def _format_conversation(self, structured_context: dict[str, Any]) -> str:
        """Format the previous conversation section.

        Only the most recent 10 messages are included; older messages
        are ignored. Each message is rendered as a ``"User:"`` or
        ``"Assistant:"`` block, without numbering. Messages are expected
        as ``{"role": ..., "content": ...}`` dictionaries (the
        conventional chat-message schema); plain strings and other
        shapes are also handled gracefully.

        Args:
            structured_context: The structured clinical context.

        Returns:
            str: Plain-text conversation history, or ``"Not Available"``
            if no conversation history is present.
        """

        def extract_role_and_content(message: Any) -> tuple[str, str]:
            """Extract a display role and content string from one message."""
            if isinstance(message, dict) and "role" in message:
                role_value = str(message.get("role", "")).strip().lower()
                content_value = message.get("content", NOT_AVAILABLE)
                rendered_content = str(content_value) if content_value else NOT_AVAILABLE

                if role_value == "user":
                    return "User", rendered_content
                if role_value in ("assistant", "ai"):
                    return "Assistant", rendered_content

                display_role = role_value.capitalize() if role_value else "Message"
                return display_role, rendered_content

            if isinstance(message, str):
                return "Message", message

            return "Message", str(message)

        messages = _lookup_first(structured_context, _CONVERSATION_KEYS)

        if not messages or not isinstance(messages, (list, tuple)):
            return NOT_AVAILABLE

        if len(messages) > MAX_CONVERSATION_MESSAGES:
            logger.info(
                "Conversation history truncated from %d to the most recent %d messages.",
                len(messages),
                MAX_CONVERSATION_MESSAGES,
            )

        recent_messages = list(messages)[-MAX_CONVERSATION_MESSAGES:]

        blocks: list[str] = [
            f"{role}:\n{content}"
            for role, content in (extract_role_and_content(message) for message in recent_messages)
        ]

        return "\n\n".join(blocks) if blocks else NOT_AVAILABLE