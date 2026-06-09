import uuid
from fastapi import UploadFile, HTTPException, status

# Accepted file extensions for patient documents
ALLOWED_DOCUMENT_EXTENSIONS = {
    '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.webp', '.dcm'
}

# 10 MB limit for medical documents
MAX_FILE_SIZE = 10 * 1024 * 1024


def validate_document_file(file: UploadFile) -> bool:
    """Validate that the uploaded file is an accepted document type."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )

    file_ext = '.' + file.filename.rsplit('.', 1)[-1].lower()
    if file_ext not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(sorted(ALLOWED_DOCUMENT_EXTENSIONS))}"
        )

    return True


def validate_file_size(file: UploadFile) -> bool:
    """Validate that the uploaded file does not exceed the size limit."""
    content = file.file.read()
    file_size = len(content)

    # Reset file pointer so the file can be read again for upload
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds the maximum allowed size of {MAX_FILE_SIZE // (1024 * 1024)} MB"
        )

    return True


def generate_unique_filename(original_filename: str, prefix: str = "patient_documents") -> str:
    """Generate a unique S3 key for an uploaded file."""
    file_ext = '.' + original_filename.rsplit('.', 1)[-1].lower()
    unique_id = str(uuid.uuid4())
    return f"{prefix}/{unique_id}{file_ext}"
