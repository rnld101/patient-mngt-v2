import uuid
from fastapi import UploadFile, HTTPException, status

ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def validate_image_file(file: UploadFile) -> bool:
    """Validate that the uploaded file is an allowed image type."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )
    
    # Check file extension
    file_ext = '.' + file.filename.split('.')[-1].lower()
    if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
        )
    
    return True


async def validate_image_size(file: UploadFile) -> bool:
    """Validate that the file size is within limits."""
    # Read the file to get its size
    content = await file.read()
    file_size = len(content)
    
    # Reset file pointer
    await file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024 * 1024)} MB"
        )
    
    return True


def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename for S3 upload."""
    # Get file extension
    file_ext = '.' + original_filename.split('.')[-1].lower()
    # Generate unique name with uuid
    unique_id = str(uuid.uuid4())
    return f"patient_images/{unique_id}{file_ext}"
