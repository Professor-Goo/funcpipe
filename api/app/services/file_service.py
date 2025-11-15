"""
File Service - Handles file upload, storage, and retrieval.

Production-ready implementation with:
- Secure file validation
- Metadata extraction
- File cleanup
- Error handling
- Comprehensive logging

NO MOCK DATA - Real file operations only.
"""

import hashlib
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from uuid import UUID, uuid4

import aiofiles
from fastapi import UploadFile

# Import funcpipe for file reading
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from funcpipe import readers

from app.core.config import settings
from app.core.logging import get_logger
from app.models.schemas import FileFormat, FileInfo, FileUploadResponse

logger = get_logger(__name__)


class FileValidationError(Exception):
    """Raised when file validation fails."""
    pass


class FileNotFoundError(Exception):
    """Raised when file is not found."""
    pass


class FileService:
    """
    Service for managing uploaded files.

    Handles:
    - File upload and validation
    - Metadata extraction
    - File storage and retrieval
    - File cleanup
    """

    def __init__(self):
        self.upload_dir = settings.upload_dir
        self.result_dir = settings.result_dir
        self.temp_dir = settings.temp_dir
        self.max_size = settings.max_upload_size_bytes
        self.allowed_extensions = settings.allowed_extensions

        # Ensure directories exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.result_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # In-memory file metadata store (in production, use database)
        self._file_metadata: Dict[UUID, FileInfo] = {}

        logger.info(
            "file_service_initialized",
            upload_dir=str(self.upload_dir),
            max_size_mb=settings.max_upload_size_mb
        )

    def _validate_file(self, filename: str, size: int) -> None:
        """
        Validate file before accepting upload.

        Args:
            filename: Original filename
            size: File size in bytes

        Raises:
            FileValidationError: If validation fails
        """
        # Check size
        if size > self.max_size:
            raise FileValidationError(
                f"File too large: {size} bytes (max: {self.max_size})"
            )

        if size == 0:
            raise FileValidationError("File is empty")

        # Check extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.allowed_extensions:
            raise FileValidationError(
                f"Invalid file type: {file_ext}. "
                f"Allowed: {', '.join(self.allowed_extensions)}"
            )

        # Sanitize filename
        if any(char in filename for char in ['..', '/', '\\']):
            raise FileValidationError("Invalid filename: contains illegal characters")

        logger.debug(
            "file_validated",
            filename=filename,
            size=size,
            extension=file_ext
        )

    def _get_file_format(self, filename: str) -> FileFormat:
        """Determine file format from extension."""
        ext = Path(filename).suffix.lower()
        format_map = {
            '.csv': FileFormat.CSV,
            '.json': FileFormat.JSON,
            '.tsv': FileFormat.TSV,
            '.txt': FileFormat.TXT,
        }
        return format_map.get(ext, FileFormat.CSV)

    def _extract_metadata(self, file_path: Path, file_format: FileFormat) -> Dict:
        """
        Extract metadata from uploaded file.

        Args:
            file_path: Path to file
            file_format: File format

        Returns:
            Dictionary with metadata (record_count, fields, etc.)
        """
        try:
            # Use funcpipe to get file info
            file_info = readers.get_file_info(str(file_path))

            metadata = {
                'record_count': file_info.get('record_count'),
                'fields': file_info.get('fields', []),
            }

            # Get detailed field info if possible
            if 'record_count' in file_info and file_info['record_count'] not in [None, 'large_file']:
                try:
                    # Read sample to analyze field types
                    sample = readers.read_sample(str(file_path), n=100)
                    if sample:
                        field_details = []
                        fields = list(sample[0].keys())

                        for field in fields:
                            # Analyze field type
                            types = set()
                            null_count = 0

                            for record in sample:
                                value = record.get(field)
                                if value is None or value == '':
                                    null_count += 1
                                else:
                                    types.add(type(value).__name__)

                            field_details.append({
                                'name': field,
                                'type': ', '.join(sorted(types)) if types else 'null',
                                'null_count': null_count,
                            })

                        metadata['fields'] = field_details

                except Exception as e:
                    logger.warning(
                        "failed_to_extract_detailed_metadata",
                        file=str(file_path),
                        error=str(e)
                    )

            return metadata

        except Exception as e:
            logger.error(
                "metadata_extraction_failed",
                file=str(file_path),
                error=str(e)
            )
            return {'record_count': None, 'fields': None}

    async def upload_file(self, file: UploadFile) -> FileUploadResponse:
        """
        Upload and store file.

        Args:
            file: Uploaded file from FastAPI

        Returns:
            FileUploadResponse with file metadata

        Raises:
            FileValidationError: If validation fails
        """
        # Generate unique ID
        file_id = uuid4()

        # Read file content
        content = await file.read()
        file_size = len(content)

        # Validate
        self._validate_file(file.filename or "upload", file_size)

        # Determine format
        file_format = self._get_file_format(file.filename or "upload.csv")

        # Create safe filename
        safe_filename = f"{file_id}{Path(file.filename or 'upload').suffix}"
        file_path = self.upload_dir / safe_filename

        try:
            # Write file
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)

            logger.info(
                "file_uploaded",
                file_id=str(file_id),
                filename=file.filename,
                size=file_size,
                path=str(file_path)
            )

            # Extract metadata
            metadata = self._extract_metadata(file_path, file_format)

            # Create response
            response = FileUploadResponse(
                id=file_id,
                filename=file.filename or "upload",
                size=file_size,
                format=file_format,
                record_count=metadata.get('record_count'),
                fields=metadata.get('fields') if isinstance(metadata.get('fields'), list) else None,
                uploaded_at=datetime.utcnow(),
            )

            # Store metadata
            file_info = FileInfo(
                **response.model_dump(),
                path=str(file_path)
            )
            self._file_metadata[file_id] = file_info

            return response

        except Exception as e:
            # Cleanup on error
            if file_path.exists():
                file_path.unlink()

            logger.error(
                "file_upload_failed",
                file_id=str(file_id),
                filename=file.filename,
                error=str(e)
            )
            raise RuntimeError(f"Failed to upload file: {e}")

    def get_file(self, file_id: UUID) -> FileInfo:
        """
        Get file metadata.

        Args:
            file_id: File UUID

        Returns:
            FileInfo object

        Raises:
            FileNotFoundError: If file not found
        """
        if file_id not in self._file_metadata:
            raise FileNotFoundError(f"File not found: {file_id}")

        return self._file_metadata[file_id]

    def get_file_path(self, file_id: UUID) -> Path:
        """
        Get file system path for file.

        Args:
            file_id: File UUID

        Returns:
            Path to file

        Raises:
            FileNotFoundError: If file not found
        """
        file_info = self.get_file(file_id)

        if not file_info.path:
            raise FileNotFoundError(f"File path not available for {file_id}")

        file_path = Path(file_info.path)

        if not file_path.exists():
            logger.error(
                "file_missing_from_disk",
                file_id=str(file_id),
                path=str(file_path)
            )
            raise FileNotFoundError(f"File missing from disk: {file_id}")

        return file_path

    def list_files(self, offset: int = 0, limit: int = 100) -> Dict:
        """
        List all uploaded files.

        Args:
            offset: Pagination offset
            limit: Max results

        Returns:
            Dictionary with files list and pagination info
        """
        all_files = list(self._file_metadata.values())
        total = len(all_files)

        # Sort by upload time (newest first)
        all_files.sort(key=lambda f: f.uploaded_at, reverse=True)

        # Paginate
        files = all_files[offset:offset + limit]

        return {
            'files': files,
            'total': total,
            'offset': offset,
            'limit': limit,
        }

    async def get_file_preview(
        self,
        file_id: UUID,
        offset: int = 0,
        limit: int = 50
    ) -> Dict:
        """
        Get preview of file data.

        Args:
            file_id: File UUID
            offset: Record offset
            limit: Max records

        Returns:
            Dictionary with data and pagination info
        """
        file_path = self.get_file_path(file_id)

        try:
            # Read full file
            data = readers.auto_read(str(file_path))
            total = len(data)

            # Paginate
            preview_data = data[offset:offset + limit]

            logger.debug(
                "file_preview_generated",
                file_id=str(file_id),
                total_records=total,
                preview_records=len(preview_data)
            )

            return {
                'data': preview_data,
                'total': total,
                'offset': offset,
                'limit': limit,
            }

        except Exception as e:
            logger.error(
                "file_preview_failed",
                file_id=str(file_id),
                error=str(e)
            )
            raise RuntimeError(f"Failed to preview file: {e}")

    async def delete_file(self, file_id: UUID) -> None:
        """
        Delete file and metadata.

        Args:
            file_id: File UUID

        Raises:
            FileNotFoundError: If file not found
        """
        file_info = self.get_file(file_id)

        try:
            # Delete from disk
            if file_info.path:
                file_path = Path(file_info.path)
                if file_path.exists():
                    file_path.unlink()

            # Remove metadata
            del self._file_metadata[file_id]

            logger.info("file_deleted", file_id=str(file_id))

        except Exception as e:
            logger.error(
                "file_deletion_failed",
                file_id=str(file_id),
                error=str(e)
            )
            raise RuntimeError(f"Failed to delete file: {e}")

    async def cleanup_old_files(self):
        """
        Clean up old result files based on retention policy.

        Should be called periodically (e.g., via cron job).
        """
        cutoff_time = datetime.utcnow() - timedelta(
            hours=settings.result_retention_hours
        )

        cleaned = 0
        for file_path in self.result_dir.glob("*"):
            if file_path.is_file():
                # Check file modification time
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        cleaned += 1
                    except Exception as e:
                        logger.warning(
                            "failed_to_cleanup_file",
                            file=str(file_path),
                            error=str(e)
                        )

        if cleaned > 0:
            logger.info("old_files_cleaned", count=cleaned)

        return cleaned


# Global service instance
_file_service: Optional[FileService] = None


def get_file_service() -> FileService:
    """Get the global file service instance."""
    global _file_service
    if _file_service is None:
        _file_service = FileService()
    return _file_service
