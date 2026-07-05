"""routes/reports.py
====================
FastAPI router for the Medical Report Analysis feature.

Exposes:
    POST /reports/analyse — accept a PDF or TXT medical report, run the
                            AI analysis pipeline, return structured findings.

Registered in ``main.py`` under ``/api/v1`` so the full path is:
    POST /api/v1/reports/analyse
"""

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.ai.report_analysis.schemas import ReportAnalysisResult
from app.core.dependencies import require_roles
from app.models.user import UserInDB, UserRole
from app.services.report_analysis_service import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE_BYTES,
    ReportAnalysisService,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(
    prefix="/reports",
    tags=["Medical Report Analysis"],
)

# ---------------------------------------------------------------------------
# Dependency injection
# ---------------------------------------------------------------------------


def _svc() -> ReportAnalysisService:
    """Instantiate a stateless ReportAnalysisService for this request."""
    return ReportAnalysisService()


# ---------------------------------------------------------------------------
# POST /analyse
# ---------------------------------------------------------------------------

@router.post(
    "/analyse",
    response_model=ReportAnalysisResult,
    status_code=status.HTTP_200_OK,
    summary="Analyse an uploaded medical report",
    responses={
        400: {"description": "Validation failure — empty file, wrong type, or exceeds size limit"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient role"},
        422: {"description": "Missing or malformed file field"},
        500: {"description": "Parser or analyser failure — file may be corrupt or unreadable"},
    },
)
async def analyse_report(
    file: UploadFile = File(
        ...,
        description=(
            f"Medical report file to analyse. "
            f"Accepted formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}. "
            f"Maximum size: {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."
        ),
    ),
    _user: UserInDB = Depends(
        require_roles(UserRole.ADMIN, UserRole.DOCTOR)
    ),
    svc: ReportAnalysisService = Depends(_svc),
) -> ReportAnalysisResult:
    """
    Upload and analyse a medical report file.

    Runs the complete AI pipeline:

    ```
    UploadFile → ReportParser (text extraction)
               → MedicalReportAnalyzer (rule-based findings + summary)
               → ReportAnalysisResult
    ```

    **Accepted file types:** `.pdf` · `.txt`

    **Maximum file size:** 10 MB

    **Response includes:**
    - `abnormal_findings` — findings outside the reference range, ordered by severity
    - `normal_findings` — findings within the reference range
    - `unclassified_findings` — findings the engine could not classify (review required)
    - `summary.overview` — plain-English summary of the report
    - `summary.critical_alerts` — findings requiring immediate clinical attention
    - `summary.recommendations` — rule-based suggested next steps
    - `summary.requires_urgent_review` — `true` if any HIGH or CRITICAL findings exist
    - `disclaimer` — mandatory statement that results require clinical review

    **Notes:**
    - Scanned (image-only) PDFs cannot be extracted without OCR — the response
      will have `extraction_successful: false` and empty findings lists.
    - All findings are produced by a rule-based engine and **must** be
      reviewed by a qualified clinician before any clinical decision is made.

    **Role required:** Admin · Doctor
    """
    # ── Read file bytes ───────────────────────────────────────────────────────
    # UploadFile.read() is async and returns the full content as bytes.
    try:
        content = await file.read()
    except Exception as exc:
        logger.error("Failed to read uploaded file '%s': %s", file.filename, exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read uploaded file: {exc}",
        )
    finally:
        await file.close()

    logger.info(
        "Report upload received: filename=%r  size=%d bytes  content_type=%s",
        file.filename, len(content), file.content_type,
    )

    # ── Delegate to service ───────────────────────────────────────────────────
    try:
        result = await svc.analyse_upload(
            content=content,
            filename=file.filename or "upload",
            content_type=file.content_type or "",
        )
    except ValueError as exc:
        # Validation errors: wrong type, size exceeded, empty file
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except RuntimeError as exc:
        # Parser/analyser failures: corrupt file, unexpected error
        logger.error(
            "Runtime error analysing '%s': %s", file.filename, exc
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report analysis failed: {exc}",
        )

    return result