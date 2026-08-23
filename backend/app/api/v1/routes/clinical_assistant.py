"""
FastAPI router for AI Clinical Assistant endpoints.
"""

from __future__ import annotations

import json

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from app.ai_clinical_assistant.assistant_service import AssistantService
from app.ai_clinical_assistant.exceptions import (
    AIClinicalAssistantError,
    ConversationMemoryError,
    InvalidUserInputError,
    ProviderUnavailableError,
)
from app.ai_clinical_assistant.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationContext,
    ConversationHistory,
)
from app.api.dependencies.clinical_assistant import (
    get_ai_clinical_assistant_service,
)
from app.risk_assessment.utils.logging_utils import get_logger


logger = get_logger(__name__)


router = APIRouter(
    prefix="/clinical-assistant",
    tags=["AI Clinical Assistant"],
)


# =========================================================
# Helper
# =========================================================

def parse_context(
    context: str | None,
) -> ConversationContext | None:
    """Parse optional JSON clinical context."""

    if not context:
        return None

    try:
        parsed = json.loads(context)

        return ConversationContext(**parsed)

    except Exception as error:
        raise InvalidUserInputError(
            "Invalid clinical context format."
        ) from error


# =========================================================
# Start Conversation
# =========================================================

@router.post(
    "/",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Start a new conversation",
)
async def chat(
    message: str = Form(...),
    conversation_id: str | None = Form(None),
    context: str | None = Form(None),
    stream: bool = Form(False),
    temperature: float = Form(0.2),
    max_tokens: int = Form(500),
    files: list[UploadFile] | None = File(None),
    service: AssistantService = Depends(
        get_ai_clinical_assistant_service
    ),
) -> ChatResponse:

    logger.info(
        "AI Clinical Assistant chat request received."
    )

    try:
        clinical_context = parse_context(context)

        request = ChatRequest(
            message=message,
            conversation_id=conversation_id,
            context=clinical_context,
            stream=stream,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return await service.chat(
            request,
            files=files,
        )

    except InvalidUserInputError as error:
        logger.warning(
            "Invalid chat request: %s",
            error,
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except ConversationMemoryError as error:
        logger.warning(
            "Conversation error: %s",
            error,
        )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except ProviderUnavailableError as error:
        logger.error(
            "Provider unavailable: %s",
            error,
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error

    except AIClinicalAssistantError as error:
        logger.error(
            "AI Clinical Assistant error: %s",
            error,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception(
            "Unexpected error in AI Clinical Assistant."
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "An unexpected error occurred while "
                "processing your request."
            ),
        ) from error


# =========================================================
# Continue Conversation
# =========================================================

@router.post(
    "/continue/{conversation_id}",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Continue an existing conversation",
)
async def continue_conversation(
    conversation_id: str,
    message: str = Form(...),
    context: str | None = Form(None),
    stream: bool = Form(False),
    temperature: float = Form(0.2),
    max_tokens: int = Form(500),
    files: list[UploadFile] | None = File(None),
    service: AssistantService = Depends(
        get_ai_clinical_assistant_service
    ),
) -> ChatResponse:

    logger.info(
        "Continuing conversation: %s",
        conversation_id,
    )

    try:
        clinical_context = parse_context(context)

        request = ChatRequest(
            message=message,
            conversation_id=conversation_id,
            context=clinical_context,
            stream=stream,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return await service.chat(
            request,
            files=files,
        )

    except InvalidUserInputError as error:
        logger.warning(
            "Invalid continue request: %s",
            error,
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except ConversationMemoryError as error:
        logger.warning(
            "Conversation error: %s",
            error,
        )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except ProviderUnavailableError as error:
        logger.error(
            "Provider unavailable: %s",
            error,
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error

    except AIClinicalAssistantError as error:
        logger.error(
            "AI Clinical Assistant error: %s",
            error,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception(
            "Unexpected error continuing conversation."
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "An unexpected error occurred while "
                "processing your request."
            ),
        ) from error


# =========================================================
# Conversation History
# =========================================================

@router.get(
    "/history/{conversation_id}",
    response_model=ConversationHistory,
    status_code=status.HTTP_200_OK,
    summary="Get conversation history",
)
async def get_conversation_history(
    conversation_id: str,
    service: AssistantService = Depends(
        get_ai_clinical_assistant_service
    ),
) -> ConversationHistory:

    try:
        return await service.get_conversation(
            conversation_id
        )

    except ConversationMemoryError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except AIClinicalAssistantError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error


# =========================================================
# Delete Conversation
# =========================================================

@router.delete(
    "/conversation/{conversation_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_conversation(
    conversation_id: str,
    service: AssistantService = Depends(
        get_ai_clinical_assistant_service
    ),
) -> dict:

    try:
        await service.delete_conversation(
            conversation_id
        )

        return {
            "message": "Conversation deleted successfully."
        }

    except ConversationMemoryError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except AIClinicalAssistantError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error


# =========================================================
# Clear Conversation Memory
# =========================================================

@router.delete(
    "/conversation/{conversation_id}/memory",
    status_code=status.HTTP_200_OK,
)
async def clear_conversation_memory(
    conversation_id: str,
    service: AssistantService = Depends(
        get_ai_clinical_assistant_service
    ),
) -> dict:

    try:
        await service.clear_conversation(
            conversation_id
        )

        return {
            "message": "Conversation cleared successfully."
        }

    except ConversationMemoryError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except AIClinicalAssistantError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error


# =========================================================
# Health
# =========================================================

@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
)
async def health_check(
    service: AssistantService = Depends(
        get_ai_clinical_assistant_service
    ),
) -> dict:

    try:
        return await service.health()

    except AIClinicalAssistantError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception(
            "Unexpected error during health check."
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "An unexpected error occurred during "
                "health check."
            ),
        ) from error