"""report_analysis_service.py
=============================
Service layer for the MediSys Medical Report Analysis feature.

Orchestrates the full pipeline::

    UploadFile bytes
        ↓
    ReportParser.extract_from_bytes()   — text extraction
        ↓
    MedicalReportAnalyzer.analyse()     — rule-based findings + summary
        ↓
    ReportAnalysisResult                — returned to the route layer

Responsibilities
----------------
* File validation — size cap, MIME type, extension whitelist.
* Extraction — delegates entirely to the singleton ``report_parser``.
* Analysis — delegates entirely to the singleton ``medical_report_analyzer``.
* Error isolation — wraps both collaborators so infrastructure failures
  (corrupt file, unsupported encoding) become clean ``ValueError`` or
  ``RuntimeError`` with diagnostic messages the route can convert to
  the correct HTTP status code.

This service contains **zero** AI logic and **zero** database calls.
It is intentionally stateless so it can be constructed on every request
without cost and discarded afterward — the same pattern used by
``AuthService`` and ``PatientService``.
"""

import logging
from pathlib import Path
from app.ai.report_analysis.*

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Maximum allowed upload size in bytes (10 MB).
MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024   # 10 MB

# Allowed MIME types sent by the client (Content-Type header).
ALLOWED_MIME_TYPES: frozenset[str] = frozenset({
    "application/pdf",
    "text/plain",
    "application/octet-stream",   # some clients send this for .txt
})

# Allowed file extensions (lower-case, including the dot).
ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".pdf", ".txt"})

# Map from file extension to ReportType enum value.
_EXT_TO_REPORT_TYPE: dict[str, ReportType] = {
    ".pdf": ReportType.PDF,
    ".txt": ReportType.TXT,
}


# ---------------------------------------------------------------------------
# ReportAnalysisService
# ---------------------------------------------------------------------------

class ReportAnalysisService:
    """Stateless service that validates, parses, and analyses medical reports.

    Constructed per-request via FastAPI dependency injection and discarded
    afterward.  All persistent state lives in the module-level singletons
    ``report_parser`` and ``medical_report_analyzer``.

    Example:
        >>> svc = ReportAnalysisService()
        >>> result = await svc.analyse_upload(file_bytes, "cbc_report.pdf", "application/pdf")
        >>> result.extraction_successful
        True
    """

    # ── Public entry point ────────────────────────────────────────────────────

    async def analyse_upload(
        self,
        content: bytes,
        filename: str,
        content_type: str,
    ) -> ReportAnalysisResult:
        """Validate, extract, and analyse an uploaded medical report file.

        This is the single method called by the route handler.  It runs
        three sequential steps:

        1. **Validation** — size, extension, and MIME type checks.
        2. **Extraction** — delegates to :func:`report_parser.extract_from_bytes`.
        3. **Analysis** — delegates to :func:`medical_report_analyzer.analyse`.

        Args:
            content: Raw file bytes as read from ``UploadFile.read()``.
            filename: Original filename from the upload (used for extension
                detection and logging).
            content_type: MIME type declared by the client (``UploadFile.content_type``).

        Returns:
            :class:`~schemas.ReportAnalysisResult` — always returned, even on
            partial failure.  ``extraction_successful`` will be ``False`` if
            the parser could not extract usable text.

        Raises:
            ValueError: For validation failures — file too large, unsupported
                type, or empty file.  The route converts this to HTTP 400.
            RuntimeError: For unexpected failures inside the parser or analyser.
                The route converts this to HTTP 500.
        """
        # ── Step 1: Validate ──────────────────────────────────────────────────
        self._validate(content, filename, content_type)

        # ── Step 2: Detect report type from extension ─────────────────────────
        suffix = Path(filename).suffix.lower()
        report_type = _EXT_TO_REPORT_TYPE.get(suffix, ReportType.UNKNOWN)

        logger.info(
            "Processing upload: filename=%r  size=%d bytes  type=%s",
            filename, len(content), report_type.value,
        )

        # ── Step 3: Extract text ──────────────────────────────────────────────
        try:
            text = report_parser.extract_from_bytes(content, filename, report_type)
        except Exception as exc:
            logger.exception(
                "Unexpected error in report_parser for file %r: %s", filename, exc
            )
            raise RuntimeError(
                f"Text extraction failed for '{filename}': {exc}"
            ) from exc

        if not text:
            logger.warning(
                "Extraction returned empty text for '%s'. "
                "File may be a scanned PDF or corrupted.",
                filename,
            )

        # ── Step 4: Analyse ───────────────────────────────────────────────────
        try:
            result = medical_report_analyzer.analyse(text, report_type=report_type)
        except Exception as exc:
            logger.exception(
                "Unexpected error in medical_report_analyzer for file %r: %s",
                filename, exc,
            )
            raise RuntimeError(
                f"Report analysis failed for '{filename}': {exc}"
            ) from exc

        logger.info(
            "Analysis complete: filename=%r  findings=%d  "
            "abnormal=%d  urgent=%s",
            filename,
            result.total_findings,
            len(result.abnormal_findings),
            result.summary.requires_urgent_review,
        )

        return result

    # ── Private: validation ───────────────────────────────────────────────────

    def _validate(
        self,
        content: bytes,
        filename: str,
        content_type: str,
    ) -> None:
        """Apply size, extension, and MIME-type validation to the upload.

        Args:
            content: Raw file bytes.
            filename: Original filename from the upload.
            content_type: MIME type declared by the HTTP client.

        Raises:
            ValueError: With a descriptive message for each validation failure.
        """
        # ── Empty file ────────────────────────────────────────────────────────
        if not content:
            raise ValueError("Uploaded file is empty.")

        # ── Size cap ──────────────────────────────────────────────────────────
        if len(content) > MAX_FILE_SIZE_BYTES:
            size_mb = len(content) / (1024 * 1024)
            cap_mb  = MAX_FILE_SIZE_BYTES / (1024 * 1024)
            raise ValueError(
                f"File size {size_mb:.1f} MB exceeds the maximum allowed "
                f"size of {cap_mb:.0f} MB."
            )

        # ── Extension whitelist ───────────────────────────────────────────────
        suffix = Path(filename).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise ValueError(
                f"File extension '{suffix}' is not supported. "
                f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
            )

        # ── MIME type whitelist ───────────────────────────────────────────────
        # Some clients send generic types — we accept the extension as
        # authoritative when the MIME type is ambiguous.
        normalised_ct = (content_type or "").split(";")[0].strip().lower()
        if normalised_ct and normalised_ct not in ALLOWED_MIME_TYPES:
            logger.warning(
                "Unexpected content-type '%s' for file '%s' — "
                "proceeding based on file extension.",
                content_type, filename,
            )

        logger.debug(
            "Validation passed: filename=%r  size=%d  ext=%s  content_type=%s",
            filename, len(content), suffix, content_type,
        )