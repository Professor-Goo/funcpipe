"""
Pydantic schemas for request/response validation.

All API data models with comprehensive validation.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


# ============================================================================
# Enums
# ============================================================================

class FileFormat(str, Enum):
    """Supported file formats."""
    CSV = "csv"
    JSON = "json"
    TSV = "tsv"
    TXT = "txt"


class OperationType(str, Enum):
    """Types of pipeline operations."""
    FILTER = "filter"
    TRANSFORM = "transform"
    SORT = "sort"
    TAKE = "take"
    SKIP = "skip"


class ExecutionStatus(str, Enum):
    """Pipeline execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ============================================================================
# File Models
# ============================================================================

class FileUploadResponse(BaseModel):
    """Response after successful file upload."""
    id: UUID = Field(default_factory=uuid4, description="Unique file identifier")
    filename: str = Field(..., description="Original filename")
    size: int = Field(..., ge=0, description="File size in bytes")
    format: FileFormat = Field(..., description="File format")
    record_count: Optional[int] = Field(None, description="Number of records")
    fields: Optional[List[str]] = Field(None, description="Field names")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "filename": "employees.csv",
                "size": 2048,
                "format": "csv",
                "record_count": 100,
                "fields": ["name", "age", "salary"],
                "uploaded_at": "2025-11-14T10:00:00Z"
            }
        }


class FileInfo(BaseModel):
    """Detailed file information."""
    id: UUID
    filename: str
    size: int
    format: FileFormat
    record_count: Optional[int] = None
    fields: Optional[List[Dict[str, Any]]] = None  # Detailed field info
    uploaded_at: datetime
    path: Optional[str] = None  # Internal use only

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "filename": "employees.csv",
                "size": 2048,
                "format": "csv",
                "record_count": 100,
                "fields": [
                    {"name": "age", "type": "int", "null_count": 0},
                    {"name": "name", "type": "str", "null_count": 2}
                ],
                "uploaded_at": "2025-11-14T10:00:00Z"
            }
        }


class FileListResponse(BaseModel):
    """Response for file list endpoint."""
    files: List[FileInfo]
    total: int = Field(..., ge=0, description="Total number of files")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    limit: int = Field(default=100, ge=1, le=1000, description="Limit for pagination")


class DataPreviewResponse(BaseModel):
    """Response for file data preview."""
    data: List[Dict[str, Any]]
    total: int = Field(..., ge=0, description="Total records in file")
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=1000)


# ============================================================================
# Operation Models
# ============================================================================

class OperationConfig(BaseModel):
    """Base configuration for operations."""
    type: OperationType
    operation: str = Field(..., description="Operation name (e.g., 'greater_than')")
    config: Dict[str, Any] = Field(default_factory=dict, description="Operation parameters")

    @field_validator("config")
    @classmethod
    def validate_config_not_empty_for_most_ops(cls, v, info):
        """Ensure config is provided for operations that need it."""
        # TAKE and SKIP operations might have config in a different format
        # This will be validated more specifically in the operation registry
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "type": "filter",
                "operation": "greater_than",
                "config": {
                    "field": "age",
                    "value": 25
                }
            }
        }


class FilterOperationConfig(OperationConfig):
    """Filter operation configuration."""
    type: OperationType = Field(default=OperationType.FILTER, frozen=True)

    class Config:
        json_schema_extra = {
            "example": {
                "type": "filter",
                "operation": "greater_than",
                "config": {
                    "field": "age",
                    "value": 25
                }
            }
        }


class TransformOperationConfig(OperationConfig):
    """Transform operation configuration."""
    type: OperationType = Field(default=OperationType.TRANSFORM, frozen=True)

    class Config:
        json_schema_extra = {
            "example": {
                "type": "transform",
                "operation": "capitalize_field",
                "config": {
                    "field": "name"
                }
            }
        }


class SortOperationConfig(OperationConfig):
    """Sort operation configuration."""
    type: OperationType = Field(default=OperationType.SORT, frozen=True)
    config: Dict[str, Any] = Field(
        ...,
        description="Sort configuration with 'field' and optional 'reverse'"
    )

    @field_validator("config")
    @classmethod
    def validate_sort_config(cls, v):
        """Ensure sort config has required field."""
        if "field" not in v:
            raise ValueError("Sort operation requires 'field' in config")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "type": "sort",
                "operation": "sort",
                "config": {
                    "field": "age",
                    "reverse": True
                }
            }
        }


class TakeOperationConfig(OperationConfig):
    """Take operation configuration."""
    type: OperationType = Field(default=OperationType.TAKE, frozen=True)
    config: Dict[str, Any] = Field(..., description="Take configuration with 'n'")

    @field_validator("config")
    @classmethod
    def validate_take_config(cls, v):
        """Ensure take config has n parameter."""
        if "n" not in v:
            raise ValueError("Take operation requires 'n' in config")
        if not isinstance(v["n"], int) or v["n"] < 1:
            raise ValueError("Take 'n' must be a positive integer")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "type": "take",
                "operation": "take",
                "config": {
                    "n": 10
                }
            }
        }


class SkipOperationConfig(OperationConfig):
    """Skip operation configuration."""
    type: OperationType = Field(default=OperationType.SKIP, frozen=True)
    config: Dict[str, Any] = Field(..., description="Skip configuration with 'n'")

    @field_validator("config")
    @classmethod
    def validate_skip_config(cls, v):
        """Ensure skip config has n parameter."""
        if "n" not in v:
            raise ValueError("Skip operation requires 'n' in config")
        if not isinstance(v["n"], int) or v["n"] < 0:
            raise ValueError("Skip 'n' must be a non-negative integer")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "type": "skip",
                "operation": "skip",
                "config": {
                    "n": 5
                }
            }
        }


# ============================================================================
# Pipeline Models
# ============================================================================

class PipelineExecuteRequest(BaseModel):
    """Request to execute a pipeline."""
    file_id: UUID = Field(..., description="ID of file to process")
    operations: List[OperationConfig] = Field(
        ...,
        min_length=1,
        description="List of operations to apply"
    )
    preview: bool = Field(
        default=False,
        description="If true, limit results for preview"
    )
    preview_limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Max records to return in preview"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "file_id": "123e4567-e89b-12d3-a456-426614174000",
                "operations": [
                    {
                        "type": "filter",
                        "operation": "greater_than",
                        "config": {"field": "age", "value": 25}
                    },
                    {
                        "type": "transform",
                        "operation": "capitalize_field",
                        "config": {"field": "name"}
                    }
                ],
                "preview": False,
                "preview_limit": 100
            }
        }


class PipelineValidateRequest(BaseModel):
    """Request to validate a pipeline configuration."""
    operations: List[OperationConfig] = Field(..., min_length=1)
    file_id: Optional[UUID] = Field(
        None,
        description="Optional file ID for field validation"
    )


class PipelineValidateResponse(BaseModel):
    """Response from pipeline validation."""
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ExecutionResult(BaseModel):
    """Result of pipeline execution."""
    execution_id: UUID = Field(default_factory=uuid4)
    status: ExecutionStatus
    data: Optional[List[Dict[str, Any]]] = None
    record_count: Optional[int] = None
    execution_time_ms: Optional[float] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "execution_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "completed",
                "data": [{"name": "Alice", "age": 30}],
                "record_count": 1,
                "execution_time_ms": 125.5,
                "error": None,
                "created_at": "2025-11-14T10:05:00Z"
            }
        }


# ============================================================================
# Saved Pipeline Models
# ============================================================================

class PipelineSaveRequest(BaseModel):
    """Request to save a pipeline configuration."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    operations: List[OperationConfig] = Field(..., min_length=1)
    tags: List[str] = Field(default_factory=list, max_length=10)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        """Validate tags are unique and not empty."""
        if len(v) != len(set(v)):
            raise ValueError("Tags must be unique")
        if any(not tag.strip() for tag in v):
            raise ValueError("Tags cannot be empty")
        return [tag.strip() for tag in v]


class SavedPipeline(BaseModel):
    """Saved pipeline configuration."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    operations: List[OperationConfig]
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    execution_count: int = Field(default=0, ge=0)


class PipelineListResponse(BaseModel):
    """Response for pipeline list endpoint."""
    pipelines: List[SavedPipeline]
    total: int = Field(..., ge=0)
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=1000)


# ============================================================================
# Operation Metadata Models
# ============================================================================

class OperationParameter(BaseModel):
    """Parameter definition for an operation."""
    name: str
    type: str  # Python type name
    required: bool = True
    default: Optional[Any] = None
    description: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "field",
                "type": "str",
                "required": True,
                "description": "Field name to filter"
            }
        }


class OperationMetadata(BaseModel):
    """Metadata about an available operation."""
    type: OperationType
    name: str  # Operation name (e.g., "greater_than")
    display_name: str  # Human-readable name
    description: str
    parameters: List[OperationParameter]
    examples: List[Dict[str, Any]] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "type": "filter",
                "name": "greater_than",
                "display_name": "Greater Than",
                "description": "Filter records where field value is greater than specified value",
                "parameters": [
                    {
                        "name": "field",
                        "type": "str",
                        "required": True,
                        "description": "Field name to compare"
                    },
                    {
                        "name": "value",
                        "type": "Union[int, float]",
                        "required": True,
                        "description": "Value to compare against"
                    }
                ],
                "examples": [
                    {"field": "age", "value": 25},
                    {"field": "salary", "value": 50000.0}
                ]
            }
        }


class OperationsListResponse(BaseModel):
    """Response containing all available operations."""
    filters: List[OperationMetadata]
    transforms: List[OperationMetadata]
    utilities: List[OperationMetadata]  # sort, take, skip


# ============================================================================
# Error Models
# ============================================================================

class ErrorDetail(BaseModel):
    """Detailed error information."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    field: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: ErrorDetail
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid field name 'ageee'",
                    "details": {"valid_fields": ["age", "name", "salary"]},
                    "field": "age"
                },
                "request_id": "req-123456",
                "timestamp": "2025-11-14T10:00:00Z"
            }
        }


# ============================================================================
# Health Check Models
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    checks: Dict[str, str] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2025-11-14T10:00:00Z",
                "checks": {
                    "database": "healthy",
                    "storage": "healthy"
                }
            }
        }
