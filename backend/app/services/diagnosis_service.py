import logging
import inspect
from datetime import datetime, timezone
from typing import List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.ai.inference.predictor import disease_predictor
from app.ai.inference.recommendation_engine import recommendation_engine
from app.models.diagnosis import (
    DiagnosisCreate,
    DiagnosisInDB,
    DiagnosisResponse,
    DiagnosisStatus,
    DiagnosisUpdate,
)

logger = logging.getLogger(__name__)
logger.info(inspect.getfile(recommendation_engine.__class__))


# ── Module-level helper ───────────────────────────────────────────────────────

def _diagnosis_to_response(doc: dict) -> DiagnosisResponse:
    """
    Convert a raw MongoDB document into a DiagnosisResponse.

    Responsibilities
    ----------------
    - Converts _id (ObjectId) to a plain string.
    - Parses the raw dict through DiagnosisInDB for type safety.
    - All fields in this model are already datetime — no date conversion
      is required (unlike patient_service).
    """
    # Normalise _id to string before feeding into Pydantic
    if "_id" not in doc:
        raise ValueError("Diagnosis document is missing '_id' field.")
    doc = {**doc, "_id": str(doc["_id"])}

    diagnosis = DiagnosisInDB(**doc)

    return DiagnosisResponse(
        id=str(diagnosis.id),
        patient_id=diagnosis.patient_id,
        symptoms=diagnosis.symptoms,
        predicted_disease=diagnosis.predicted_disease,
        confidence_score=diagnosis.confidence_score,
        doctor_final_diagnosis=diagnosis.doctor_final_diagnosis,
        doctor_notes=diagnosis.doctor_notes,
        recommended_tests=diagnosis.recommended_tests,
        status=diagnosis.status,
        created_by=diagnosis.created_by,
        created_at=diagnosis.created_at,
        updated_at=diagnosis.updated_at,
    )


# ── Service class ─────────────────────────────────────────────────────────────

class DiagnosisService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.diagnoses = db["diagnoses"]

    # ── Create ────────────────────────────────────────────────────────────────

    async def create_diagnosis(
        self,
        payload: DiagnosisCreate,
        created_by: str,
    ) -> DiagnosisResponse:
        """
        Persist a new diagnosis record and return the public response.

        Notes
        -----
        - AI fields (predicted_disease, confidence_score) are always None
          at creation time. The AI prediction service will populate them
          in a subsequent update step (Phase 9).
        - Status is set to PENDING until AI analysis runs.
        - created_by stores the authenticated user's ObjectId string.
        - Raises ValueError if patient_id is malformed or patient does not exist.
        """
        # ── Validate patient exists ───────────────────────────────────────────
        if not ObjectId.is_valid(payload.patient_id):
            raise ValueError(f"'{payload.patient_id}' is not a valid patient ID.")

        patient = await self.db["patients"].find_one(
            {"_id": ObjectId(payload.patient_id)}
        )
        if patient is None:
            raise ValueError(
                f"Patient '{payload.patient_id}' does not exist."
            )

        now = datetime.now(timezone.utc)

        doc = {
            # ── Core ──────────────────────────────────────────────────────────
            "patient_id": payload.patient_id,
            "symptoms": payload.symptoms,

            # ── AI output — reserved for Phase 8 ─────────────────────────────
            "predicted_disease": None,     # populated by AI prediction service
            "confidence_score": None,      # populated by AI prediction service

            # ── Doctor review — reserved for doctor update ────────────────────
            "doctor_final_diagnosis": None,
            "doctor_notes": None,
            "recommended_tests": [],

            # ── Status ────────────────────────────────────────────────────────
            "status": DiagnosisStatus.PENDING.value,

            # ── Meta ──────────────────────────────────────────────────────────
            "created_by": created_by,
            "created_at": now,
            "updated_at": now,
        }

        result = await self.diagnoses.insert_one(doc)
        doc["_id"] = result.inserted_id

        logger.info(
            "Diagnosis created: patient_id=%s  id=%s  by=%s",
            payload.patient_id,
            result.inserted_id,
            created_by,
        )

        return _diagnosis_to_response(doc)

    # ── AI Orchestration: predict + recommend ───────────────────────────────────

    async def generate_ai_diagnosis(
        self,
        diagnosis_id: str,
    ) -> Optional[DiagnosisResponse]:
        """
        Run AI prediction and clinical recommendation for an existing diagnosis,
        then persist both outputs to the record.

        Orchestrates the full AI workflow in four independent steps:

            symptoms → DiseasePredictor.predict() → PredictionResult
                     → RecommendationEngine.get_recommendation() → RecommendationResult
                     → DiagnosisResponse

        This method is a pure orchestrator. It does not perform prediction or
        recommendation logic itself — it only sequences two independent,
        single-responsibility collaborators and writes their combined output
        to MongoDB via the existing update_diagnosis() pathway, so PATCH
        semantics, automatic status transitions, and updated_at refresh are
        all reused rather than duplicated.

        Separation of concerns
        -----------------------
        - disease_predictor   (app.ai.inference.predictor)
          Responsible ONLY for turning symptoms into a predicted disease and
          confidence score. Knows nothing about recommendations or MongoDB.
        - recommendation_engine (app.ai.recommendation.recommendation_engine)
          Responsible ONLY for turning a disease name into clinical guidance.
          Knows nothing about the ML model or MongoDB.
        - DiagnosisService (this method)
          Responsible ONLY for sequencing the two collaborators above and
          persisting their combined output. Contains no prediction logic and
          no recommendation logic of its own.

        Parameters
        ----------
        diagnosis_id : MongoDB ObjectId string of the diagnosis record to
                       analyse. The record's existing `symptoms` field is
                       used as the prediction input — no symptoms are
                       supplied directly to this method.

        Returns
        -------
        Updated DiagnosisResponse if the diagnosis record exists, None otherwise.

        Raises
        ------
        ValueError
            If diagnosis_id is not a syntactically valid ObjectId.
        RuntimeError
            Propagated from DiseasePredictor or RecommendationEngine if a
            system-level failure occurs (e.g. missing model artefacts or a
            corrupt knowledge base) — these are deployment-configuration
            problems and are intentionally allowed to surface rather than
            being silently swallowed.
        """
        if not ObjectId.is_valid(diagnosis_id):
            raise ValueError(f"'{diagnosis_id}' is not a valid diagnosis ID.")

        # ── Step 1: Load the existing diagnosis record ─────────────────────────
        doc = await self.diagnoses.find_one({"_id": ObjectId(diagnosis_id)})
        if doc is None:
            return None

        symptoms: List[str] = doc["symptoms"]

        logger.info(
            "Generating AI diagnosis: id=%s  symptoms=%s",
            diagnosis_id,
            symptoms,
        )

        # ── Step 2: Predict disease from symptoms ───────────────────────────────
        # disease_predictor remains solely responsible for prediction.
        # It has no awareness of the diagnosis record, MongoDB, or recommendations.
        prediction = disease_predictor.predict(symptoms)

        logger.info(
            "Prediction complete: id=%s  disease=%s  confidence=%.2f%%",
            diagnosis_id,
            prediction.disease,
            prediction.confidence,
        )

        # ── Step 3: Retrieve clinical recommendation for the predicted disease ──
        # recommendation_engine remains solely responsible for recommendations.
        # It has no awareness of the ML model, symptoms, or MongoDB.
        recommendation = recommendation_engine.get_recommendation(
            prediction.disease
        )

        logger.info(
            "Recommendation retrieved: id=%s  disease=%s  severity=%s  "
            "found_in_knowledge_base=%s",
            diagnosis_id,
            prediction.disease,
            recommendation.severity,
            recommendation.found_in_knowledge_base,
        )

        # ── Step 4: Persist combined AI output via the existing update pathway ──
        # confidence_score is stored as a 0.0-1.0 probability (DiagnosisUpdate
        # contract), while PredictionResult.confidence is a 0-100 percentage —
        # convert here at the orchestration boundary.
        #
        # IMPORTANT: recommended_tests is intentionally excluded from the
        # DiagnosisUpdate payload here. update_diagnosis() treats
        # recommended_tests as a _doctor_field for status-transition purposes
        # (because doctors also write to it during review). If we passed
        # recommended_tests via DiagnosisUpdate, the doctor-fields block would
        # fire and override status to DOCTOR_REVIEWED — which is wrong.
        # Instead we pass only the two AI-specific fields so the AI_REVIEWED
        # transition fires cleanly, then fold recommended_tests into the
        # same $set by patching it directly into the changes dict before
        # the database write. This avoids duplicating the update_diagnosis
        # logic while keeping the status transition correct.
        update_payload = DiagnosisUpdate(
            predicted_disease=prediction.disease,
            confidence_score=round(prediction.confidence / 100, 4),
        )

        # Reuse update_diagnosis() so PATCH semantics, automatic status
        # transitions (→ AI_REVIEWED), and updated_at refresh are not duplicated.
        # Then inject recommended_tests from the recommendation engine directly
        # into MongoDB alongside the AI fields in a single atomic write.
        if not ObjectId.is_valid(diagnosis_id):
            raise ValueError(f"'{diagnosis_id}' is not a valid diagnosis ID.")

        changes = update_payload.to_update_dict()

        _ai_fields = {"predicted_disease", "confidence_score"}
        if _ai_fields & changes.keys():
            if changes.get("status") not in (
                DiagnosisStatus.DOCTOR_REVIEWED,
                DiagnosisStatus.DOCTOR_REVIEWED.value,
            ):
                changes["status"] = DiagnosisStatus.AI_REVIEWED.value

        # Write recommended_tests from the recommendation engine directly —
        # bypassing the doctor-field status-transition guard intentionally.
        changes["recommended_tests"] = recommendation.recommended_tests
        changes["updated_at"] = datetime.now(timezone.utc)

        result = await self.diagnoses.find_one_and_update(
            {"_id": ObjectId(diagnosis_id)},
            {"$set": changes},
            return_document=True,
        )

        if result is None:
            return None

        logger.info(
            "AI diagnosis persisted: id=%s  disease=%s  status=%s  "
            "recommended_tests=%d",
            diagnosis_id,
            prediction.disease,
            changes["status"],
            len(recommendation.recommended_tests),
        )

        return _diagnosis_to_response(result)

    # ── Read: single ──────────────────────────────────────────────────────────

    async def get_diagnosis_by_id(self, diagnosis_id: str) -> Optional[DiagnosisResponse]:
        """
        Fetch one diagnosis record by its MongoDB ObjectId string.

        Returns
        -------
        DiagnosisResponse if found, None if not found.

        Raises
        ------
        ValueError for a syntactically invalid ObjectId.
        """
        if not ObjectId.is_valid(diagnosis_id):
            raise ValueError(f"'{diagnosis_id}' is not a valid diagnosis ID.")

        doc = await self.diagnoses.find_one({"_id": ObjectId(diagnosis_id)})
        if doc is None:
            return None

        return _diagnosis_to_response(doc)

    # ── Read: list ────────────────────────────────────────────────────────────

    async def list_diagnoses(
        self,
        skip: int = 0,
        limit: int = 20,
        patient_id: Optional[str] = None,
    ) -> List[DiagnosisResponse]:
        """
        Return a paginated, newest-first list of diagnosis records.

        Parameters
        ----------
        skip       : number of records to skip (offset pagination)
        limit      : maximum records to return (capped by the route layer)
        patient_id : when supplied, restricts results to a single patient.
                     Raises ValueError if the value is not a valid ObjectId.
        """
        query: dict = {}

        if patient_id is not None:
            if not ObjectId.is_valid(patient_id):
                raise ValueError(f"'{patient_id}' is not a valid patient ID.")
            query["patient_id"] = patient_id

        cursor = (
            self.diagnoses
            .find(query)
            .sort("created_at", -1)   # -1 = descending → newest first
            .skip(skip)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        return [_diagnosis_to_response(doc) for doc in docs]

    # ── Update ────────────────────────────────────────────────────────────────

    async def update_diagnosis(
        self,
        diagnosis_id: str,
        payload: DiagnosisUpdate,
    ) -> Optional[DiagnosisResponse]:
        """
        Apply a partial update (PATCH semantics) to an existing diagnosis record.

        Only fields explicitly supplied by the caller are written.
        updated_at is always refreshed regardless of which fields changed.

        This method is used by two distinct callers:
        - AI prediction service  → writes predicted_disease and/or confidence_score;
                                   status advances to AI_REVIEWED automatically.
        - Doctor review endpoint → writes doctor_final_diagnosis, doctor_notes,
                                   and/or recommended_tests; status advances to
                                   DOCTOR_REVIEWED automatically.

        Status transitions are derived from the fields present in the payload —
        callers never need to set status manually.

        Returns
        -------
        Updated DiagnosisResponse if the record exists, None otherwise.

        Raises
        ------
        ValueError for a syntactically invalid ObjectId.
        """
        if not ObjectId.is_valid(diagnosis_id):
            raise ValueError(f"'{diagnosis_id}' is not a valid diagnosis ID.")

        # to_update_dict() excludes unset and None fields — pure PATCH semantics
        changes = payload.to_update_dict()

        # ── Automatic status transitions ──────────────────────────────────────
        # Derived from which fields the caller supplied — no manual status needed.
        _ai_fields     = {"predicted_disease", "confidence_score"}
        _doctor_fields = {"doctor_final_diagnosis", "doctor_notes", "recommended_tests"}

        if _ai_fields & changes.keys():
            # At least one AI field is being written → advance to AI_REVIEWED
            # unless the doctor has already reviewed (never downgrade status).
            if changes.get("status") not in (
                DiagnosisStatus.DOCTOR_REVIEWED,
                DiagnosisStatus.DOCTOR_REVIEWED.value,
            ):
                changes["status"] = DiagnosisStatus.AI_REVIEWED.value

        if _doctor_fields & changes.keys():
            # At least one doctor field is being written → advance to DOCTOR_REVIEWED.
            # This always takes precedence over AI_REVIEWED.
            changes["status"] = DiagnosisStatus.DOCTOR_REVIEWED.value

        # DiagnosisStatus enum must be stored as a plain string
        if "status" in changes and hasattr(changes["status"], "value"):
            changes["status"] = changes["status"].value

        # Always refresh updated_at — even if no other fields changed
        changes["updated_at"] = datetime.now(timezone.utc)

        result = await self.diagnoses.find_one_and_update(
            {"_id": ObjectId(diagnosis_id)},
            {"$set": changes},
            return_document=True,   # return the document AFTER the update
        )

        if result is None:
            return None

        logger.info(
            "Diagnosis updated: id=%s  fields=%s",
            diagnosis_id,
            list(changes.keys()),
        )

        return _diagnosis_to_response(result)