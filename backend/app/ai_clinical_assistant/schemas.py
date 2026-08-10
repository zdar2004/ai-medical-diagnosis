"""Data schemas for the AI Clinical Assistant module.

This module defines every Pydantic model used across the AI Clinical
Assistant module, ensuring type safety, strict validation, and
consistent data structures across conversation memory, context
building, prompt construction, provider calls, and response validation.
"""

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

MIN_CONTENT_LENGTH: int = 1
MIN_ID_LENGTH: int = 1
MIN_PATIENT_AGE: int = 0
MIN_TEMPERATURE: float = 0.0
MAX_TEMPERATURE: float = 1.0
DEFAULT_TEMPERATURE: float = 0.2
MIN_MAX_TOKENS: int = 1
MAX_MAX_TOKENS: int = 4096
DEFAULT_MAX_TOKENS: int = 500
DEFAULT_PROVIDER_NAME: str = "dummy"

MessageRole = Literal["system", "user", "assistant"]
ProviderName = Literal["dummy", "gemini", "openai"]


class ChatMessage(BaseModel):
    """Represents a single message in a clinical assistant conversation.

    Captures the structure of individual messages exchanged between the
    user (clinician) and the AI assistant, including metadata about when
    the message was created.

    Attributes:
        role: The role of the message sender: ``"system"`` for system
            instructions or context, ``"user"`` for messages from the
            clinician or user, or ``"assistant"`` for messages from the
            AI assistant.
        content: The text content of the message.
        timestamp: When the message was created, in UTC. Defaults to the
            current time.
    """

    role: MessageRole = Field(
        ...,
        description="Role of the message sender: 'system', 'user', or 'assistant'.",
    )
    content: str = Field(
        ...,
        min_length=MIN_CONTENT_LENGTH,
        description="The text content of the message.",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the message was created (UTC).",
    )

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class ConversationContext(BaseModel):
    """Clinical context for an AI assistant conversation.

    Encapsulates all relevant clinical information that should be
    considered when generating AI responses, including patient data,
    medical history, current clinical findings, risk assessment results,
    and prior report analysis.

    Attributes:
        patient_id: Unique identifier for the patient, if known.
        patient_age: Patient's age in years, if known.
        patient_gender: Patient's gender, if known.
        medical_history: Relevant medical history items.
        current_medications: Current medications.
        allergies: Known allergies.
        risk_assessment: Results produced by the Risk Assessment module.
        laboratory_results: Current laboratory values.
        clinical_summary: A clinical summary of the patient, if available.
        report_analysis: Results produced by the Medical Report Analysis
            module.
    """

    patient_id: str | None = Field(
        default=None,
        description="Unique identifier for the patient.",
    )
    patient_age: int | None = Field(
        default=None,
        ge=MIN_PATIENT_AGE,
        description="Patient's age in years.",
    )
    patient_gender: str | None = Field(
        default=None,
        description="Patient's gender.",
    )
    medical_history: list[str] = Field(
        default_factory=list,
        description="List of relevant medical history items.",
    )
    current_medications: list[str] = Field(
        default_factory=list,
        description="List of current medications.",
    )
    allergies: list[str] = Field(
        default_factory=list,
        description="List of known allergies.",
    )
    risk_assessment: dict[str, Any] = Field(
        default_factory=dict,
        description="Results from the Risk Assessment module.",
    )
    laboratory_results: dict[str, Any] = Field(
        default_factory=dict,
        description="Current laboratory values.",
    )
    clinical_summary: str | None = Field(
        default=None,
        description="Clinical summary text.",
    )
    report_analysis: dict[str, Any] = Field(
        default_factory=dict,
        description="Results from the Medical Report Analysis module.",
    )

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class ChatRequest(BaseModel):
    """Request model for sending a message to the AI Clinical Assistant.

    Defines all parameters that can be specified when sending a chat
    request to the assistant service.

    Attributes:
        message: The user's message or question to the assistant.
        conversation_id: ID of an existing conversation to continue, or
            ``None`` to start a new conversation.
        context: Clinical context for the conversation, if available.
        stream: Whether the response should be streamed incrementally.
        temperature: Sampling temperature for response generation.
            Higher values increase randomness; lower values make
            responses more deterministic.
        max_tokens: Maximum number of tokens to generate in the response.
    """

    message: str = Field(
        ...,
        min_length=MIN_CONTENT_LENGTH,
        description="The user's message/question to the assistant.",
    )
    conversation_id: str | None = Field(
        default=None,
        description="ID of an existing conversation to continue, or None for new.",
    )
    context: ConversationContext | None = Field(
        default=None,
        description="Clinical context for the conversation.",
    )
    stream: bool = Field(
        default=False,
        description="Whether the response should be streamed incrementally.",
    )
    temperature: float = Field(
        default=DEFAULT_TEMPERATURE,
        ge=MIN_TEMPERATURE,
        le=MAX_TEMPERATURE,
        description="Sampling temperature. Higher values increase randomness.",
    )
    max_tokens: int = Field(
        default=DEFAULT_MAX_TOKENS,
        ge=MIN_MAX_TOKENS,
        le=MAX_MAX_TOKENS,
        description="Maximum number of tokens to generate in the response.",
    )

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class ChatResponse(BaseModel):
    """Response model returned by the AI Clinical Assistant.

    Captures the assistant's response along with metadata about the
    generation process.

    Attributes:
        response: The generated response text.
        provider: Name of the LLM provider used to generate the response.
        generated_at: When the response was generated, in UTC.
        conversation_id: ID of the conversation being continued, if any.
        warnings: Any warnings or notices about the response.
    """

    response: str = Field(
        ...,
        min_length=MIN_CONTENT_LENGTH,
        description="The generated response from the assistant.",
    )
    provider: str = Field(
        ...,
        min_length=MIN_ID_LENGTH,
        description="Name of the LLM provider used to generate the response.",
    )
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the response was generated (UTC).",
    )
    conversation_id: str | None = Field(
        default=None,
        description="ID of the conversation being continued.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="List of warnings or notices about the response.",
    )

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class ConversationHistory(BaseModel):
    """Complete history of a clinical assistant conversation.

    Stores all messages exchanged in a conversation, providing the full
    context needed to continue conversations and maintain memory.

    Attributes:
        conversation_id: Unique identifier for the conversation.
        messages: All messages in the conversation, in chronological
            order.
        created_at: When the conversation was created, in UTC.
        updated_at: When the conversation was last modified, in UTC.
    """

    conversation_id: str = Field(
        ...,
        min_length=MIN_ID_LENGTH,
        description="Unique identifier for the conversation.",
    )
    messages: list[ChatMessage] = Field(
        default_factory=list,
        description="All messages in the conversation in chronological order.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the conversation was created (UTC).",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the conversation was last updated (UTC).",
    )

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class AssistantConfig(BaseModel):
    """Configuration model for the AI Clinical Assistant.

    Defines all configurable parameters for the assistant's behavior,
    allowing runtime configuration without code changes.

    Attributes:
        provider_name: Name of the LLM provider to use.
        temperature: Default sampling temperature for response
            generation.
        max_tokens: Default maximum tokens for responses.
        enable_memory: Whether to maintain conversation memory.
        enable_context: Whether to use clinical context in responses.
        system_prompt: An optional override for the default system
            prompt.
    """

    provider_name: ProviderName = Field(
        default=DEFAULT_PROVIDER_NAME,
        description="Name of the LLM provider to use.",
    )
    temperature: float = Field(
        default=DEFAULT_TEMPERATURE,
        ge=MIN_TEMPERATURE,
        le=MAX_TEMPERATURE,
        description="Default sampling temperature for response generation.",
    )
    max_tokens: int = Field(
        default=DEFAULT_MAX_TOKENS,
        ge=MIN_MAX_TOKENS,
        le=MAX_MAX_TOKENS,
        description="Default maximum tokens for responses.",
    )
    enable_memory: bool = Field(
        default=True,
        description="Whether to maintain conversation memory.",
    )
    enable_context: bool = Field(
        default=True,
        description="Whether to use clinical context in responses.",
    )
    system_prompt: str | None = Field(
        default=None,
        description="Optional override for the default system prompt.",
    )

    model_config = ConfigDict(extra="forbid", validate_assignment=True)