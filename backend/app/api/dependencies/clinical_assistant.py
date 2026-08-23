from fastapi import Depends

from app.ai_clinical_assistant.assistant_service import AssistantService
from app.database import get_database


async def get_ai_clinical_assistant_service(
    database=Depends(get_database),
) -> AssistantService:
    service = AssistantService(database=database)
    return service