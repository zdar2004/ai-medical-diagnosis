import logging
from datetime import date, datetime, time, timezone
from typing import List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.patient import (
    PatientCreate,
    PatientInDB,
    PatientResponse,
    PatientUpdate,
    calculate_age,
)

logger = logging.getLogger(__name__)


# ── Module-level helper ───────────────────────────────────────────────────────

def _patient_to_response(doc: dict) -> PatientResponse:
    """
    Convert a raw MongoDB document into a PatientResponse.

    Responsibilities
    ----------------
    - Converts _id (ObjectId) to a plain string.
    - Parses the raw dict through PatientInDB for type safety.
    - Calculates age from date_of_birth via calculate_age() — never reads
      a stored age field because none exists in the document.
    """
    # Normalise _id to string before feeding into Pydantic
    doc = {**doc, "_id": str(doc["_id"])}

    # MongoDB stores date_of_birth as a datetime (UTC midnight).
    # Convert back to a plain date so PatientInDB, calculate_age(),
    # and PatientResponse.date_of_birth all receive the correct type.
    if isinstance(doc.get("date_of_birth"), datetime):
        doc = {**doc, "date_of_birth": doc["date_of_birth"].date()}

    # MongoDB also stores diagnosed_on inside each previous_diagnoses entry
    # as a datetime. Convert each non-null value back to a plain date so
    # DiagnosisEntry.diagnosed_on (typed date) parses without error.
    if doc.get("previous_diagnoses"):
        fixed_entries = []
        for entry in doc["previous_diagnoses"]:
            if isinstance(entry.get("diagnosed_on"), datetime):
                entry = {**entry, "diagnosed_on": entry["diagnosed_on"].date()}
            fixed_entries.append(entry)
        doc = {**doc, "previous_diagnoses": fixed_entries}

    patient = PatientInDB(**doc)

    return PatientResponse(
        id=str(patient.id),
        first_name=patient.first_name,
        last_name=patient.last_name,
        gender=patient.gender,
        age=calculate_age(patient.date_of_birth),   # derived, never stored
        date_of_birth=patient.date_of_birth,
        phone=patient.phone,
        email=patient.email,
        address=patient.address,
        blood_group=patient.blood_group,
        emergency_contact=patient.emergency_contact,
        allergies=patient.allergies,
        medications=patient.medications,
        previous_diagnoses=patient.previous_diagnoses,
        medical_history=patient.medical_history,
        created_by=patient.created_by,
        created_at=patient.created_at,
        updated_at=patient.updated_at,
    )


# ── Service class ─────────────────────────────────────────────────────────────

class PatientService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.patients = db["patients"]

    # ── Create ────────────────────────────────────────────────────────────────

    async def create_patient(
        self,
        payload: PatientCreate,
        created_by: str,
    ) -> PatientResponse:
        """
        Persist a new patient document and return the public response.

        Notes
        -----
        - Age is never stored. Only date_of_birth goes into MongoDB.
        - created_by stores the authenticated user's ObjectId string.
        - Embedded sub-documents (emergency_contact, previous_diagnoses)
          are serialised via model_dump() so Pydantic handles nesting.
        """
        now = datetime.now(timezone.utc)

        # Motor/PyMongo cannot encode datetime.date — convert to UTC midnight datetime.
        dob_datetime = datetime.combine(
            payload.date_of_birth,
            time.min,
            tzinfo=timezone.utc,
        )

        doc = {
            # ── Identity ──────────────────────────────────────────────────────
            "first_name": payload.first_name,
            "last_name": payload.last_name,
            "gender": payload.gender.value,
            "date_of_birth": dob_datetime,           # stored as UTC midnight datetime

            # ── Contact ───────────────────────────────────────────────────────
            "phone": payload.phone,
            "email": payload.email,
            "address": payload.address,

            # ── Medical ───────────────────────────────────────────────────────
            "blood_group": payload.blood_group.value,
            "emergency_contact": (
                payload.emergency_contact.model_dump()
                if payload.emergency_contact is not None
                else None
            ),
            "allergies": payload.allergies,
            "medications": payload.medications,
            "previous_diagnoses": [
                {
                    **entry.model_dump(),
                    # diagnosed_on is typed date; Motor requires datetime.
                    "diagnosed_on": datetime.combine(
                        entry.diagnosed_on, time.min, tzinfo=timezone.utc
                    ) if entry.diagnosed_on is not None else None,
                }
                for entry in payload.previous_diagnoses
            ],
            "medical_history": payload.medical_history,

            # ── Meta ──────────────────────────────────────────────────────────
            "created_by": created_by,
            "created_at": now,
            "updated_at": now,
        }

        result = await self.patients.insert_one(doc)
        doc["_id"] = result.inserted_id

        logger.info(
            "Patient created: %s %s  id=%s  by=%s",
            payload.first_name,
            payload.last_name,
            result.inserted_id,
            created_by,
        )

        return _patient_to_response(doc)

    # ── Read: single ──────────────────────────────────────────────────────────

    async def get_patient_by_id(self, patient_id: str) -> Optional[PatientResponse]:
        """
        Fetch one patient by their MongoDB ObjectId string.

        Returns
        -------
        PatientResponse if found, None if not found.

        Raises
        ------
        ValueError for a syntactically invalid ObjectId.
        """
        if not ObjectId.is_valid(patient_id):
            raise ValueError(f"'{patient_id}' is not a valid patient ID.")

        doc = await self.patients.find_one({"_id": ObjectId(patient_id)})
        if doc is None:
            return None

        return _patient_to_response(doc)

    # ── Read: list ────────────────────────────────────────────────────────────

    async def list_patients(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> List[PatientResponse]:
        """
        Return a paginated, newest-first list of patients.

        Parameters
        ----------
        skip  : number of records to skip (offset pagination)
        limit : maximum records to return (capped by the route layer)
        """
        cursor = (
            self.patients
            .find({})
            .sort("created_at", -1)   # -1 = descending → newest first
            .skip(skip)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        return [_patient_to_response(doc) for doc in docs]

    # ── Update ────────────────────────────────────────────────────────────────

    async def update_patient(
        self,
        patient_id: str,
        payload: PatientUpdate,
    ) -> Optional[PatientResponse]:
        """
        Apply a partial update (PATCH semantics) to an existing patient.

        Only fields explicitly supplied by the caller are written.
        updated_at is always refreshed regardless of which fields changed.

        Returns
        -------
        Updated PatientResponse if the patient exists, None otherwise.

        Raises
        ------
        ValueError for a syntactically invalid ObjectId.
        """
        if not ObjectId.is_valid(patient_id):
            raise ValueError(f"'{patient_id}' is not a valid patient ID.")

        # to_update_dict() excludes unset and None fields — pure PATCH semantics
        changes = payload.to_update_dict()

        # Serialise nested Pydantic objects that survived to_update_dict()
        if "emergency_contact" in changes and changes["emergency_contact"] is not None:
            ec = changes["emergency_contact"]
            # May already be a dict (from model_dump) or still a Pydantic model
            if hasattr(ec, "model_dump"):
                changes["emergency_contact"] = ec.model_dump()

        if "previous_diagnoses" in changes and changes["previous_diagnoses"] is not None:
            serialised = []
            for entry in changes["previous_diagnoses"]:
                # Pydantic model → dict first
                if hasattr(entry, "model_dump"):
                    entry = entry.model_dump()
                # diagnosed_on arrives as date; Motor requires datetime.
                if isinstance(entry.get("diagnosed_on"), date):
                    entry = {
                        **entry,
                        "diagnosed_on": datetime.combine(
                            entry["diagnosed_on"], time.min, tzinfo=timezone.utc
                        ),
                    }
                serialised.append(entry)
            changes["previous_diagnoses"] = serialised

        # Enum values must be stored as plain strings
        if "gender" in changes and hasattr(changes["gender"], "value"):
            changes["gender"] = changes["gender"].value
        if "blood_group" in changes and hasattr(changes["blood_group"], "value"):
            changes["blood_group"] = changes["blood_group"].value

        # Motor cannot encode datetime.date — convert to UTC midnight datetime if present.
        if "date_of_birth" in changes and isinstance(changes["date_of_birth"], date):
            changes["date_of_birth"] = datetime.combine(
                changes["date_of_birth"],
                time.min,
                tzinfo=timezone.utc,
            )

        # Always refresh updated_at — even if changes is empty after filtering
        changes["updated_at"] = datetime.now(timezone.utc)

        result = await self.patients.find_one_and_update(
            {"_id": ObjectId(patient_id)},
            {"$set": changes},
            return_document=True,   # return the document AFTER the update
        )

        if result is None:
            return None

        logger.info("Patient updated: id=%s  fields=%s", patient_id, list(changes.keys()))

        return _patient_to_response(result)

    # ── Delete ────────────────────────────────────────────────────────────────

    async def delete_patient(self, patient_id: str) -> bool:
        """
        Hard-delete a patient document by ObjectId.

        Returns
        -------
        True  — document was found and deleted.
        False — no document matched the given ID.

        Raises
        ------
        ValueError for a syntactically invalid ObjectId.

        Notes
        -----
        Week 1 implementation: hard delete only.
        Soft-delete (is_deleted flag + updated_at) can be introduced later
        by replacing the delete_one call with a find_one_and_update.
        """
        if not ObjectId.is_valid(patient_id):
            raise ValueError(f"'{patient_id}' is not a valid patient ID.")

        result = await self.patients.delete_one({"_id": ObjectId(patient_id)})

        deleted = result.deleted_count == 1

        if deleted:
            logger.info("Patient hard-deleted: id=%s", patient_id)
        else:
            logger.warning("Delete requested for non-existent patient: id=%s", patient_id)

        return deleted