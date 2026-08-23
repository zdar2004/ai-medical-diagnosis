"""
Attachment processing for the AI Clinical Assistant.

Uploaded files are validated and converted into an internal structure
that can be consumed by multimodal providers.

Files are not permanently stored by this component.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import UploadFile

from app.ai_clinical_assistant.exceptions import InvalidUserInputError
from app.risk_assessment.utils.logging_utils import get_logger


logger = get_logger(__name__)


# =========================================================
# Configuration
# =========================================================

MAX_ATTACHMENTS = 5

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
    "text/plain",
}


@dataclass
class Attachment:
    """Internal representation of an uploaded attachment."""

    filename: str
    content_type: str
    data: bytes


class AttachmentProcessor:
    """Validate and prepare uploaded attachments."""

    async def process(
        self,
        files: list[UploadFile] | None,
    ) -> list[Attachment]:
        """Process uploaded files."""

        if not files:
            return []

        if len(files) > MAX_ATTACHMENTS:
            raise InvalidUserInputError(
                f"You can upload a maximum of {MAX_ATTACHMENTS} files at once."
            )

        processed: list[Attachment] = []

        for upload in files:
            attachment = await self._process_single(upload)
            processed.append(attachment)

        logger.info(
            "Processed %d attachment(s).",
            len(processed),
        )

        return processed

    async def _process_single(
        self,
        upload: UploadFile,
    ) -> Attachment:
        """Validate and read one uploaded file."""

        filename = upload.filename or "unnamed-file"

        content_type = (
            upload.content_type or ""
        ).lower().strip()

        if content_type not in ALLOWED_MIME_TYPES:
            raise InvalidUserInputError(
                f"Unsupported file type for '{filename}'. "
                "Supported files are PNG, JPG, JPEG, WEBP, PDF and TXT."
            )

        data = await upload.read()

        if not data:
            raise InvalidUserInputError(
                f"The uploaded file '{filename}' is empty."
            )

        if len(data) > MAX_FILE_SIZE:
            raise InvalidUserInputError(
                f"The file '{filename}' exceeds the maximum "
                f"allowed size of {MAX_FILE_SIZE // (1024 * 1024)} MB."
            )

        logger.info(
            "Attachment validated: filename='%s', type='%s', size=%d bytes.",
            filename,
            content_type,
            len(data),
        )

        return Attachment(
            filename=filename,
            content_type=content_type,
            data=data,
        )