"""Attachment processing for the AI Clinical Assistant."""

from __future__ import annotations

import io
from pathlib import Path

from fastapi import UploadFile

from app.ai_clinical_assistant.exceptions import InvalidUserInputError
from app.ai_clinical_assistant.schemas import AttachmentData
from app.risk_assessment.utils.logging_utils import get_logger


logger = get_logger(__name__)


MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


ALLOWED_EXTENSIONS = {
    ".txt",
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}


ALLOWED_CONTENT_TYPES = {
    "text/plain",
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/webp",
}


class AttachmentService:
    """Validate and process files uploaded to the Clinical Assistant."""

    async def process_files(
        self,
        files: list[UploadFile],
    ) -> list[AttachmentData]:
        """Process all uploaded files."""

        attachments: list[AttachmentData] = []

        for file in files:
            attachment = await self.process_file(file)
            attachments.append(attachment)

        return attachments

    async def process_file(
        self,
        file: UploadFile,
    ) -> AttachmentData:
        """Validate and process one uploaded file."""

        filename = file.filename or "unnamed-file"

        extension = Path(filename).suffix.lower()

        # ---------------------------------------------------------
        # Validate extension
        # ---------------------------------------------------------

        if extension not in ALLOWED_EXTENSIONS:
            raise InvalidUserInputError(
                f"Unsupported file type: {extension or 'unknown'}"
            )

        # ---------------------------------------------------------
        # Validate MIME type
        # ---------------------------------------------------------

        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise InvalidUserInputError(
                f"Unsupported content type: {file.content_type}"
            )

        # ---------------------------------------------------------
        # Read file
        # ---------------------------------------------------------

        content = await file.read()

        # ---------------------------------------------------------
        # Validate file size
        # ---------------------------------------------------------

        if len(content) > MAX_FILE_SIZE:
            raise InvalidUserInputError(
                f"File '{filename}' exceeds the maximum size of "
                f"{MAX_FILE_SIZE // (1024 * 1024)} MB."
            )

        logger.info(
            "Processing attachment '%s' (%s).",
            filename,
            file.content_type,
        )

        # ---------------------------------------------------------
        # Extract text
        # ---------------------------------------------------------

        text_content: str | None = None

        if extension == ".txt":
            text_content = self._extract_text_file(content)

        elif extension == ".pdf":
            text_content = self._extract_pdf_text(content)

        elif extension in {
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
        }:
            # Image processing will be implemented later.
            # For now, we only validate and accept the image.
            text_content = None

        return AttachmentData(
            filename=filename,
            content_type=file.content_type,
            text_content=text_content,
        )

    def _extract_text_file(
        self,
        content: bytes,
    ) -> str:
        """Extract UTF-8 text from a TXT file."""

        try:
            return content.decode("utf-8")

        except UnicodeDecodeError as error:
            raise InvalidUserInputError(
                "The text file must use UTF-8 encoding."
            ) from error

    def _extract_pdf_text(
        self,
        content: bytes,
    ) -> str:
        """Extract text from a PDF file."""

        try:
            from pypdf import PdfReader

        except ImportError as error:
            raise InvalidUserInputError(
                "PDF support requires the 'pypdf' package."
            ) from error

        try:
            reader = PdfReader(
                io.BytesIO(content)
            )

            pages: list[str] = []

            for page in reader.pages:
                page_text = page.extract_text() or ""

                if page_text.strip():
                    pages.append(page_text.strip())

            return "\n\n".join(pages)

        except Exception as error:
            logger.exception(
                "Failed to extract text from PDF '%s'.",
                "uploaded file",
            )

            raise InvalidUserInputError(
                "Unable to read the uploaded PDF."
            ) from error