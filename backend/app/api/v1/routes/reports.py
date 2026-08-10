"""
routes/reports.py

FastAPI router for the Medical Report Analysis feature.

Endpoint:
POST /api/v1/reports/analyse

Accepts:
- PDF
- DOCX
- TXT

The route delegates the actual processing to the existing
MedicalReportAnalysisService pipeline.
"""

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.dependencies import require_roles
from app.models.user import UserInDB, UserRole
from app.report_analysis.report_analysis_service import (
    MedicalReportAnalysisService,
)

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

def _svc() -> MedicalReportAnalysisService:
    """
    Create the medical report analysis service for this request.
    """
    return MedicalReportAnalysisService()


# ---------------------------------------------------------------------------
# POST /analyse
# ---------------------------------------------------------------------------

@router.post(
    "/analyse",
    status_code=status.HTTP_200_OK,
    summary="Analyse an uploaded medical report",
    responses={
        400: {
            "description": (
                "Invalid file, unsupported format, empty file, "
                "or file exceeds the size limit."
            )
        },
        401: {
            "description": "Not authenticated."
        },
        403: {
            "description": "Insufficient role."
        },
        422: {
            "description": "Missing or malformed file field."
        },
        500: {
            "description": "Medical report analysis failed."
        },
    },
)
async def analyse_report(
    file: UploadFile = File(
        ...,
        description=(
            "Medical report file. "
            "Accepted formats: PDF, DOCX, TXT. "
            "Maximum size: 10 MB."
        ),
    ),
    _user: UserInDB = Depends(
        require_roles(UserRole.ADMIN, UserRole.DOCTOR)
    ),
    svc: MedicalReportAnalysisService = Depends(_svc),
):
    """
    Upload and analyse a medical report.

    Pipeline:

        UploadFile
            ↓
        MedicalReportAnalysisService
            ↓
        ReportParser
            ↓
        ReportCleaner
            ↓
        LaboratoryValueExtractor
            ↓
        ReferenceRangeInterpreter
            ↓
        AbnormalFindingDetector
            ↓
        ClinicalSummaryGenerator
            ↓
        ClinicalInsightsGenerator
            ↓
        JSON response
    """

    # -----------------------------------------------------------------------
    # Read uploaded file
    # -----------------------------------------------------------------------

    try:
        content = await file.read()

    except Exception as exc:
        logger.exception(
            "Failed to read uploaded report '%s'.",
            file.filename,
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read uploaded file: {exc}",
        ) from exc

    finally:
        await file.close()

    filename = file.filename or "upload"

    logger.info(
        "Medical report uploaded: filename=%r size=%d bytes content_type=%s",
        filename,
        len(content),
        file.content_type,
    )

    # -----------------------------------------------------------------------
    # Analyse using existing report-analysis pipeline
    # -----------------------------------------------------------------------

    try:
        result = svc.analyze_bytes(
            file_data=content,
            filename=filename,
        )

    except ValueError as exc:
        logger.warning(
            "Report validation failed for '%s': %s",
            filename,
            exc,
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception(
            "Medical report analysis failed for '%s'.",
            filename,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report analysis failed: {exc}",
        ) from exc

    logger.info(
        "Medical report analysis completed: filename=%r",
        filename,
    )

    return result

