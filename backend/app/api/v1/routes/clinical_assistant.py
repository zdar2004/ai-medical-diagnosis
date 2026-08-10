"""
FastAPI router for AI Clinical Assistant endpoints.

This module provides REST API endpoints for interacting with the AI Clinical
Assistant service, including conversation management and health monitoring.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.ai_clinical_assistant.assistant_service import AIClinicalAssistantService
from app.ai_clinical_assistant.exceptions import (
    InvalidUserInputError,
    ConversationMemoryError,
    ProviderUnavailableError,
    ConfigurationError,
    AIClinicalAssistantError,
)
from app.ai_clinical_assistant.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationHistory,
)
from app.api.dependencies import get_ai_clinical_assistant_service
from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/clinical-assistant",
    tags=["AI Clinical Assistant"],
)


@router.post(
    "/",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Start a new conversation",
    description="Start a new conversation with the AI Clinical Assistant. "
                "This creates a new conversation ID and processes the initial user message.",
    response_description="The assistant's response with conversation ID and metadata.",
)
async def start_conversation(
    request: ChatRequest,
    service: AIClinicalAssistantService = Depends(get_ai_clinical_assistant_service),
) -> ChatResponse:
    """
    Start a new conversation with the AI Clinical Assistant.

    Args:
        request (ChatRequest): The chat request containing user message and context.
        service (AIClinicalAssistantService): The injected assistant service.

    Returns:
        ChatResponse: The assistant's response with conversation details.

    Raises:
        HTTPException: If the request is invalid or the service fails.
    """
    logger.info("Starting new conversation")

    try:
        # Extract context from request if provided
        context_dict = {}
        if request.context:
            context_dict = request.context.model_dump(exclude_none=True)

        # Process the chat request
        result = service.chat(
            user_message=request.message,
            structured_context=context_dict,
            conversation_id=None,
        )

        logger.info(f"New conversation created with ID: {result['conversation_id']}")

        # Build response
        return ChatResponse(
            response=result["response"],
            provider=service._provider.provider_name(),
            conversation_id=result["conversation_id"],
            warnings=[],
        )

    except InvalidUserInputError as e:
        logger.warning(f"Invalid user input: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ProviderUnavailableError as e:
        logger.error(f"Provider unavailable: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except ConfigurationError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except AIClinicalAssistantError as e:
        logger.error(f"AI Clinical Assistant error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error in start_conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your request.",
        )


@router.post(
    "/continue/{conversation_id}",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Continue an existing conversation",
    description="Continue an existing conversation by providing a new user message.",
    response_description="The assistant's response with conversation details.",
)
async def continue_conversation(
    conversation_id: str,
    request: ChatRequest,
    service: AIClinicalAssistantService = Depends(get_ai_clinical_assistant_service),
) -> ChatResponse:
    """
    Continue an existing conversation with the AI Clinical Assistant.

    Args:
        conversation_id (str): The ID of the conversation to continue.
        request (ChatRequest): The chat request containing user message and context.
        service (AIClinicalAssistantService): The injected assistant service.

    Returns:
        ChatResponse: The assistant's response with conversation details.

    Raises:
        HTTPException: If the conversation doesn't exist or the request is invalid.
    """
    logger.info(f"Continuing conversation: {conversation_id}")

    try:
        # Extract context from request if provided
        context_dict = {}
        if request.context:
            context_dict = request.context.model_dump(exclude_none=True)

        # Process the chat request
        result = service.continue_chat(
            conversation_id=conversation_id,
            user_message=request.message,
            structured_context=context_dict,
        )

        logger.info(f"Conversation continued: {conversation_id}")

        # Build response
        return ChatResponse(
            response=result["response"],
            provider=service._provider.provider_name(),
            conversation_id=result["conversation_id"],
            warnings=[],
        )

    except InvalidUserInputError as e:
        logger.warning(f"Invalid user input: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ConversationMemoryError as e:
        logger.warning(f"Conversation not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except KeyError as e:
        logger.warning(f"Conversation not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found.",
        )
    except ProviderUnavailableError as e:
        logger.error(f"Provider unavailable: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except ConfigurationError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except AIClinicalAssistantError as e:
        logger.error(f"AI Clinical Assistant error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error in continue_conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your request.",
        )


@router.get(
    "/history/{conversation_id}",
    response_model=ConversationHistory,
    status_code=status.HTTP_200_OK,
    summary="Get conversation history",
    description="Retrieve the complete history of a conversation including all messages.",
    response_description="The complete conversation history.",
)
async def get_conversation_history(
    conversation_id: str,
    service: AIClinicalAssistantService = Depends(get_ai_clinical_assistant_service),
) -> ConversationHistory:
    """
    Get the complete history of a conversation.

    Args:
        conversation_id (str): The ID of the conversation to retrieve.
        service (AIClinicalAssistantService): The injected assistant service.

    Returns:
        ConversationHistory: The complete conversation history.

    Raises:
        HTTPException: If the conversation doesn't exist.
    """
    logger.info(f"Retrieving conversation history: {conversation_id}")

    try:
        history = service.get_conversation_history(conversation_id)

        if history is None:
            logger.warning(f"Conversation not found: {conversation_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation '{conversation_id}' not found.",
            )

        logger.info(f"Retrieved {len(history.messages)} messages")
        return history

    except ConversationMemoryError as e:
        logger.warning(f"Conversation memory error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except AIClinicalAssistantError as e:
        logger.error(f"AI Clinical Assistant error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_conversation_history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving history.",
        )


@router.delete(
    "/conversation/{conversation_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete conversation",
    description="Permanently delete a conversation and all its messages.",
    response_description="Confirmation message.",
)
async def delete_conversation(
    conversation_id: str,
    service: AIClinicalAssistantService = Depends(get_ai_clinical_assistant_service),
) -> dict:
    """
    Permanently delete a conversation.

    Args:
        conversation_id (str): The ID of the conversation to delete.
        service (AIClinicalAssistantService): The injected assistant service.

    Returns:
        dict: Confirmation message.

    Raises:
        HTTPException: If the conversation doesn't exist.
    """
    logger.info(f"Deleting conversation: {conversation_id}")

    try:
        deleted = service.delete_conversation(conversation_id)

        if not deleted:
            logger.warning(f"Conversation not found for deletion: {conversation_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation '{conversation_id}' not found.",
            )

        logger.info(f"Conversation deleted: {conversation_id}")
        return {"message": "Conversation deleted successfully."}

    except ConversationMemoryError as e:
        logger.warning(f"Conversation memory error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except AIClinicalAssistantError as e:
        logger.error(f"AI Clinical Assistant error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error in delete_conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while deleting conversation.",
        )


@router.delete(
    "/conversation/{conversation_id}/memory",
    status_code=status.HTTP_200_OK,
    summary="Clear conversation messages",
    description="Clear all messages from a conversation while keeping the conversation ID.",
    response_description="Confirmation message.",
)
async def clear_conversation_memory(
    conversation_id: str,
    service: AIClinicalAssistantService = Depends(get_ai_clinical_assistant_service),
) -> dict:
    """
    Clear all messages from a conversation while preserving the conversation ID.

    Args:
        conversation_id (str): The ID of the conversation to clear.
        service (AIClinicalAssistantService): The injected assistant service.

    Returns:
        dict: Confirmation message.

    Raises:
        HTTPException: If the conversation doesn't exist.
    """
    logger.info(f"Clearing conversation memory: {conversation_id}")

    try:
        cleared = service.clear_conversation(conversation_id)

        if not cleared:
            logger.warning(f"Conversation not found for clearing: {conversation_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation '{conversation_id}' not found.",
            )

        logger.info(f"Conversation cleared: {conversation_id}")
        return {"message": "Conversation cleared successfully."}

    except ConversationMemoryError as e:
        logger.warning(f"Conversation memory error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except AIClinicalAssistantError as e:
        logger.error(f"AI Clinical Assistant error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error in clear_conversation_memory: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while clearing conversation.",
        )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check the health status of the AI Clinical Assistant service and its components.",
    response_description="Health status information.",
)
async def health_check(
    service: AIClinicalAssistantService = Depends(get_ai_clinical_assistant_service),
) -> dict:
    """
    Perform a health check of the AI Clinical Assistant service.

    Args:
        service (AIClinicalAssistantService): The injected assistant service.

    Returns:
        dict: Health status information.

    Raises:
        HTTPException: If the service is unhealthy.
    """
    logger.info("Performing health check")

    try:
        health = service.health_check()

        if health.get("status") != "healthy":
            logger.warning(f"Health check failed: {health}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is unhealthy",
            )

        logger.info("Health check passed")
        return health

    except AIClinicalAssistantError as e:
        logger.error(f"AI Clinical Assistant error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error in health_check: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during health check.",
        )