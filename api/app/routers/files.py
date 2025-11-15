"""
File Management API Routes.

Endpoints for uploading, listing, previewing, and deleting files.
Production-ready with comprehensive error handling.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.logging import get_logger
from app.models.schemas import (
    DataPreviewResponse,
    FileInfo,
    FileListResponse,
    FileUploadResponse,
)
from app.services.file_service import FileService, get_file_service, FileValidationError, FileNotFoundError

logger = get_logger(__name__)

router = APIRouter(prefix="/files", tags=["files"])


@router.post(
    "/upload",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a data file",
    description="Upload a CSV, JSON, TSV, or TXT file for processing",
    responses={
        201: {"description": "File uploaded successfully"},
        400: {"description": "Invalid file or file too large"},
        413: {"description": "File too large"},
        415: {"description": "Unsupported file type"},
    }
)
async def upload_file(
    file: Annotated[UploadFile, File(description="Data file to upload")],
    file_service: FileService = Depends(get_file_service),
):
    """
    Upload a data file for processing.

    Accepts CSV, JSON, TSV, and TXT files up to configured size limit.
    Returns file metadata including record count and field names.
    """
    try:
        result = await file_service.upload_file(file)
        return result

    except FileValidationError as e:
        logger.warning("file_upload_rejected", filename=file.filename, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        logger.error("file_upload_error", filename=file.filename, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file"
        )


@router.get(
    "",
    response_model=FileListResponse,
    summary="List uploaded files",
    description="Get list of all uploaded files with pagination",
)
async def list_files(
    offset: int = 0,
    limit: int = 100,
    file_service: FileService = Depends(get_file_service),
):
    """
    List all uploaded files.

    Returns paginated list of files with metadata.
    """
    try:
        result = file_service.list_files(offset=offset, limit=limit)
        return FileListResponse(**result)

    except Exception as e:
        logger.error("file_list_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list files"
        )


@router.get(
    "/{file_id}",
    response_model=FileInfo,
    summary="Get file information",
    description="Get detailed metadata for a specific file",
    responses={
        200: {"description": "File information retrieved"},
        404: {"description": "File not found"},
    }
)
async def get_file(
    file_id: UUID,
    file_service: FileService = Depends(get_file_service),
):
    """
    Get detailed information about a file.

    Returns complete file metadata including field types and statistics.
    """
    try:
        file_info = file_service.get_file(file_id)
        return file_info

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {file_id}"
        )

    except Exception as e:
        logger.error("file_get_error", file_id=str(file_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get file information"
        )


@router.get(
    "/{file_id}/preview",
    response_model=DataPreviewResponse,
    summary="Preview file data",
    description="Get preview of file records with pagination",
)
async def preview_file(
    file_id: UUID,
    offset: int = 0,
    limit: int = 50,
    file_service: FileService = Depends(get_file_service),
):
    """
    Get preview of file data.

    Returns paginated sample of records from the file.
    """
    try:
        result = await file_service.get_file_preview(
            file_id,
            offset=offset,
            limit=limit
        )
        return DataPreviewResponse(**result)

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {file_id}"
        )

    except Exception as e:
        logger.error("file_preview_error", file_id=str(file_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to preview file"
        )


@router.delete(
    "/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete file",
    description="Delete uploaded file and its metadata",
    responses={
        204: {"description": "File deleted successfully"},
        404: {"description": "File not found"},
    }
)
async def delete_file(
    file_id: UUID,
    file_service: FileService = Depends(get_file_service),
):
    """
    Delete a file.

    Removes file from storage and deletes all associated metadata.
    """
    try:
        await file_service.delete_file(file_id)
        return None

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {file_id}"
        )

    except Exception as e:
        logger.error("file_delete_error", file_id=str(file_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file"
        )
