"""Structured clinical context construction for the AI Clinical Assistant.

This module implements :class:`ContextBuilder`, the single component
responsible for assembling structured clinical context from a
:class:`~app.ai_clinical_assistant.schemas.ConversationContext` and
conversation history stored in :class:`ConversationMemory`.

``ContextBuilder`` never calls an LLM, builds prompts, validates
responses, generates AI responses, or accesses providers. Its only
responsibility is preparing a structured context dictionary.
"""

from typing import Any

from app.ai_clinical_assistant.conversation_memory import ConversationMemory
from app.ai_clinical_assistant.exceptions import ContextBuilderError
from app.ai_clinical_assistant.schemas import ConversationContext
from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)


class ContextBuilder:
    """Build structured clinical context for the AI Clinical Assistant.

    This class has a single responsibility: assembling a structured
    context dictionary from a
    :class:`~app.ai_clinical_assistant.schemas.ConversationContext` and
    the conversation history stored in :class:`ConversationMemory`. It
    never interprets, summarizes, or performs medical reasoning over
    the data it assembles; values are copied through as received.

    Attributes:
        _memory: The :class:`ConversationMemory` instance used to load
            conversation history.
    """

    def __init__(self, memory: ConversationMemory) -> None:
        """Initialize the ContextBuilder.

        Args:
            memory: The :class:`ConversationMemory` instance to use for
                loading conversation history.
        """
        self._memory: ConversationMemory = memory
        logger.info("ContextBuilder initialized.")

    def build_context(
        self,
        conversation_id: str | None,
        context: ConversationContext | None,
    ) -> dict[str, Any]:
        """Build a structured clinical context dictionary.

        Only sections with actual available data are included in the
        result; empty sections are omitted entirely. Original input
        objects are never modified; new dictionaries and lists are
        always returned.

        Args:
            conversation_id: The id of the conversation to load history
                from, or ``None`` if no conversation history should be
                included.
            context: The clinical context to build from, or ``None`` if
                no clinical context is available.

        Returns:
            dict[str, Any]: A structured context dictionary containing
            only the sections for which data was available. Possible
            keys are ``"patient"``, ``"medical_history"``,
            ``"medications"``, ``"allergies"``, ``"risk_assessment"``,
            ``"laboratory_results"``, ``"clinical_summary"``,
            ``"report_analysis"``, and ``"conversation_history"``.

        Raises:
            ContextBuilderError: If ``context`` is neither ``None`` nor
                a valid :class:`ConversationContext`, or if context
                assembly otherwise fails unexpectedly.
        """
        logger.info("Context build started.")

        if context is not None and not isinstance(context, ConversationContext):
            raise ContextBuilderError(
                "Invalid context structure: expected ConversationContext or None."
            )

        try:
            patient_section = self._build_patient_section(context)
            logger.info("Patient section built.")

            history_section = self._build_history_section(context)
            risk_section = self._build_risk_section(context)

            report_section = self._build_report_section(context)
            logger.info("Report section built.")

            conversation_section = self._build_conversation_section(conversation_id)
            logger.info("Conversation history loaded.")

            merged_context = self._merge_sections(
                patient_section,
                history_section,
                risk_section,
                report_section,
                conversation_section,
            )
        except ContextBuilderError:
            raise
        except Exception as error:
            raise ContextBuilderError("Failed to build structured clinical context.") from error

        logger.info("Context build completed.")
        return merged_context

    def _build_patient_section(self, context: ConversationContext | None) -> dict[str, Any]:
        """Build the patient identification section.

        Args:
            context: The clinical context to read patient fields from,
                or ``None``.

        Returns:
            dict[str, Any]: A dictionary with a single ``"patient"`` key
            containing only the available identifying fields
            (``"patient_id"``, ``"age"``, ``"gender"``), or an empty
            dictionary if no patient data is available.
        """
        if context is None:
            return {}

        patient_data: dict[str, Any] = {}
        if context.patient_id:
            patient_data["patient_id"] = context.patient_id
        if context.patient_age is not None:
            patient_data["age"] = context.patient_age
        if context.patient_gender:
            patient_data["gender"] = context.patient_gender

        if not patient_data:
            return {}

        return {"patient": patient_data}

    def _build_history_section(self, context: ConversationContext | None) -> dict[str, Any]:
        """Build the medical history, medications, and allergies section.

        Args:
            context: The clinical context to read history fields from,
                or ``None``.

        Returns:
            dict[str, Any]: A dictionary containing only the
            ``"medical_history"``, ``"medications"``, and
            ``"allergies"`` keys for which data is available, as new
            list copies.
        """
        if context is None:
            return {}

        section: dict[str, Any] = {}
        if context.medical_history:
            section["medical_history"] = list(context.medical_history)
        if context.current_medications:
            section["medications"] = list(context.current_medications)
        if context.allergies:
            section["allergies"] = list(context.allergies)

        return section

    def _build_risk_section(self, context: ConversationContext | None) -> dict[str, Any]:
        """Build the risk assessment section.

        The risk assessment data is copied exactly as received; no
        scores or values are modified, interpreted, or recalculated.

        Args:
            context: The clinical context to read risk assessment data
                from, or ``None``.

        Returns:
            dict[str, Any]: A dictionary with a single
            ``"risk_assessment"`` key containing a new copy of the
            original risk assessment data, or an empty dictionary if no
            risk assessment data is available.
        """
        if context is None or not context.risk_assessment:
            return {}

        return {"risk_assessment": dict(context.risk_assessment)}

    def _build_report_section(self, context: ConversationContext | None) -> dict[str, Any]:
        """Build the laboratory results, clinical summary, and report analysis section.

        Values are copied through exactly as received; this method does
        not interpret, summarize, or perform any medical reasoning over
        the data.

        Args:
            context: The clinical context to read report data from, or
                ``None``.

        Returns:
            dict[str, Any]: A dictionary containing only the
            ``"laboratory_results"``, ``"clinical_summary"``, and
            ``"report_analysis"`` keys for which data is available.
        """
        if context is None:
            return {}

        section: dict[str, Any] = {}
        if context.laboratory_results:
            section["laboratory_results"] = dict(context.laboratory_results)
        if context.clinical_summary:
            section["clinical_summary"] = context.clinical_summary
        if context.report_analysis:
            section["report_analysis"] = dict(context.report_analysis)

        return section

    def _build_conversation_section(self, conversation_id: str | None) -> dict[str, Any]:
        """Build the conversation history section.

        Args:
            conversation_id: The id of the conversation to load history
                from, or ``None``.

        Returns:
            dict[str, Any]: A dictionary with a single
            ``"conversation_history"`` key mapping to a new list of
            ``{"role": ..., "content": ...}`` dictionaries in
            chronological order. The list is empty if
            ``conversation_id`` is ``None`` or does not correspond to an
            existing conversation.
        """
        if conversation_id is None or not self._memory.conversation_exists(conversation_id):
            return {"conversation_history": []}

        recent_messages = self._memory.get_recent_messages(conversation_id)
        conversation_history = [
            {"role": message.role, "content": message.content} for message in recent_messages
        ]

        return {"conversation_history": conversation_history}

    def _merge_sections(self, *sections: dict[str, Any]) -> dict[str, Any]:
        """Merge partial context sections into a single context dictionary.

        Keys with empty or falsy values (empty dictionaries, empty
        lists, empty strings, ``None``) are omitted from the result, so
        the final context contains only genuinely available data.

        Args:
            *sections: Partial context dictionaries to merge, in order.

        Returns:
            dict[str, Any]: A new dictionary containing only the
            non-empty keys found across all provided sections.
        """
        merged: dict[str, Any] = {}
        for section in sections:
            for key, value in section.items():
                if value:
                    merged[key] = value

        return merged