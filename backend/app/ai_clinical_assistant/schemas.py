"""
Data schemas for the AI Clinical Assistant module.

This module defines every Pydantic model used across the AI Clinical
Assistant module.
"""

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

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

class AttachmentData(BaseModel):
    """Represents a processed attachment for the AI Clinical Assistant."""

    filename: str = Field(
        ...,
        min_length=1,
        description="Original attachment filename.",
    )

    content_type: str = Field(
        ...,
        min_length=1,
        description="MIME type of the attachment.",
    )

    text_content: str | None = Field(
        default=None,
        description="Extracted text from the attachment, when available.",
    )

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

class ChatMessage(BaseModel):
    """Represents a single message in a clinical assistant conversation."""

    role: MessageRole = Field(
        ...,
        description="Role of the message sender.",
    )

    content: str = Field(
        ...,
        min_length=MIN_CONTENT_LENGTH,
        description="The text content of the message.",
    )

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the message was created.",
    )

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )


class ConversationContext(BaseModel):
    """Clinical context for an AI assistant conversation."""

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

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )


class ChatRequest(BaseModel):
    """Request model for a normal text-based chat request."""

    message: str = Field(
        ...,
        min_length=MIN_CONTENT_LENGTH,
        description="The user's message/question.",
    )

    conversation_id: str | None = Field(
        default=None,
        description="Existing conversation ID.",
    )

    context: ConversationContext | None = Field(
        default=None,
        description="Clinical context.",
    )
    
    attachments: list[AttachmentData] = Field(
        default_factory=list,
        description="Processed files attached to the user message.",
    )

    stream: bool = Field(
        default=False,
        description="Whether response streaming is requested.",
    )

    temperature: float = Field(
        default=DEFAULT_TEMPERATURE,
        ge=MIN_TEMPERATURE,
        le=MAX_TEMPERATURE,
        description="Sampling temperature.",
    )

    max_tokens: int = Field(
        default=DEFAULT_MAX_TOKENS,
        ge=MIN_MAX_TOKENS,
        le=MAX_MAX_TOKENS,
        description="Maximum response tokens.",
    )

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )


class AttachmentInfo(BaseModel):
    """Metadata describing an uploaded attachment."""

    filename: str = Field(
        ...,
        min_length=MIN_ID_LENGTH,
    )

    content_type: str = Field(
        ...,
        min_length=MIN_ID_LENGTH,
    )

    size: int = Field(
        ...,
        ge=0,
    )

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )


class ChatResponse(BaseModel):
    """Response returned by the AI Clinical Assistant."""

    response: str = Field(
        ...,
        min_length=MIN_CONTENT_LENGTH,
    )

    provider: str = Field(
        ...,
        min_length=MIN_ID_LENGTH,
    )

    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )

    conversation_id: str | None = Field(
        default=None,
    )

    warnings: list[str] = Field(
        default_factory=list,
    )

    attachments: list[AttachmentInfo] = Field(
        default_factory=list,
        description="Attachments processed for this chat turn.",
    )

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )


class ConversationHistory(BaseModel):
    """Complete history of a conversation."""

    conversation_id: str = Field(
        ...,
        min_length=MIN_ID_LENGTH,
    )

    messages: list[ChatMessage] = Field(
        default_factory=list,
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )


class AssistantConfig(BaseModel):
    """Configuration model for the AI Clinical Assistant."""

    provider_name: ProviderName = Field(
        default=DEFAULT_PROVIDER_NAME,
    )

    temperature: float = Field(
        default=DEFAULT_TEMPERATURE,
        ge=MIN_TEMPERATURE,
        le=MAX_TEMPERATURE,
    )

    max_tokens: int = Field(
        default=DEFAULT_MAX_TOKENS,
        ge=MIN_MAX_TOKENS,
        le=MAX_MAX_TOKENS,
    )

    enable_memory: bool = Field(
        default=True,
    )

    enable_context: bool = Field(
        default=True,
    )

    system_prompt: str | None = Field(
        default=None,
    )

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )