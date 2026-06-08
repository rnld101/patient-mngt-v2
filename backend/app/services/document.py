from sqlalchemy.orm import Session
from app.models import PatientDocument
from typing import Optional


class DocumentService:
    """Service for patient document operations."""

    @staticmethod
    def create_document(
        db: Session,
        patient_id: int,
        user_id: int,
        document_type: str,
        file_name: str,
        s3_key: str
    ) -> PatientDocument:
        """Save document metadata after a successful S3 upload."""
        doc = PatientDocument(
            patient_id=patient_id,
            user_id=user_id,
            document_type=document_type,
            file_name=file_name,
            s3_key=s3_key
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def get_documents_for_patient(
        db: Session,
        patient_id: int,
        user_id: int
    ) -> list[PatientDocument]:
        """List all documents belonging to a patient (ownership enforced via user_id)."""
        return db.query(PatientDocument).filter(
            PatientDocument.patient_id == patient_id,
            PatientDocument.user_id == user_id
        ).order_by(PatientDocument.uploaded_at.desc()).all()

    @staticmethod
    def get_document_by_id(
        db: Session,
        document_id: int,
        user_id: int
    ) -> Optional[PatientDocument]:
        """Get a single document by ID (ownership enforced via user_id)."""
        return db.query(PatientDocument).filter(
            PatientDocument.id == document_id,
            PatientDocument.user_id == user_id
        ).first()

    @staticmethod
    def delete_document(db: Session, document_id: int, user_id: int) -> Optional[str]:
        """
        Delete a document record from the database.
        Returns the S3 key so the caller can delete the file from S3.
        Returns None if the document was not found.
        """
        doc = db.query(PatientDocument).filter(
            PatientDocument.id == document_id,
            PatientDocument.user_id == user_id
        ).first()

        if not doc:
            return None

        s3_key = doc.s3_key
        db.delete(doc)
        db.commit()
        return s3_key
