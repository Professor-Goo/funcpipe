"""
Pipeline Execution and Management API Routes.

Endpoints for executing, validating, and managing pipelines.
Production-ready with comprehensive error handling.
"""

from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.logging import get_logger
from app.models.schemas import (
    ExecutionResult,
    PipelineExecuteRequest,
    PipelineListResponse,
    PipelineSaveRequest,
    PipelineValidateRequest,
    PipelineValidateResponse,
    SavedPipeline,
)
from app.services.pipeline_service import (
    PipelineExecutionError,
    PipelineService,
    PipelineValidationError,
    get_pipeline_service,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


@router.post(
    "/execute",
    response_model=ExecutionResult,
    summary="Execute pipeline",
    description="Execute a data processing pipeline on uploaded file",
    responses={
        200: {"description": "Pipeline executed successfully"},
        400: {"description": "Invalid pipeline configuration"},
        404: {"description": "File not found"},
    }
)
async def execute_pipeline(
    request: PipelineExecuteRequest,
    pipeline_service: PipelineService = Depends(get_pipeline_service),
):
    """
    Execute a data processing pipeline.

    Applies the specified operations to the file data and returns results.
    Can optionally limit results for preview purposes.
    """
    try:
        result = await pipeline_service.execute_pipeline(
            file_id=request.file_id,
            operations=request.operations,
            preview=request.preview,
            preview_limit=request.preview_limit,
        )
        return result

    except PipelineValidationError as e:
        logger.warning(
            "pipeline_execution_validation_failed",
            file_id=str(request.file_id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        logger.error(
            "pipeline_execution_failed",
            file_id=str(request.file_id),
            error=str(e)
        )
        # Don't raise - execution result contains error
        # This allows client to handle gracefully
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline execution failed: {str(e)}"
        )


@router.post(
    "/validate",
    response_model=PipelineValidateResponse,
    summary="Validate pipeline",
    description="Validate pipeline configuration without executing",
)
async def validate_pipeline(
    request: PipelineValidateRequest,
    pipeline_service: PipelineService = Depends(get_pipeline_service),
):
    """
    Validate pipeline configuration.

    Checks if pipeline operations are valid and provides warnings.
    Can optionally validate against specific file fields.
    """
    try:
        result = pipeline_service.validate_pipeline(
            operations=request.operations,
            file_id=request.file_id,
        )
        return PipelineValidateResponse(**result)

    except Exception as e:
        logger.error("pipeline_validation_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate pipeline"
        )


@router.get(
    "/executions/{execution_id}",
    response_model=ExecutionResult,
    summary="Get execution result",
    description="Retrieve cached execution result by ID",
    responses={
        200: {"description": "Execution result found"},
        404: {"description": "Execution result not found"},
    }
)
async def get_execution_result(
    execution_id: UUID,
    pipeline_service: PipelineService = Depends(get_pipeline_service),
):
    """
    Get cached execution result.

    Returns previously executed pipeline result if still in cache.
    """
    result = pipeline_service.get_execution_result(execution_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution result not found: {execution_id}"
        )

    return result


@router.post(
    "",
    response_model=SavedPipeline,
    status_code=status.HTTP_201_CREATED,
    summary="Save pipeline",
    description="Save pipeline configuration for reuse",
    responses={
        201: {"description": "Pipeline saved successfully"},
        400: {"description": "Invalid pipeline configuration"},
    }
)
async def save_pipeline(
    request: PipelineSaveRequest,
    pipeline_service: PipelineService = Depends(get_pipeline_service),
):
    """
    Save pipeline configuration.

    Stores pipeline for future use with name, description, and tags.
    """
    try:
        saved = pipeline_service.save_pipeline(
            name=request.name,
            operations=request.operations,
            description=request.description,
            tags=request.tags,
        )
        return saved

    except PipelineValidationError as e:
        logger.warning("pipeline_save_validation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        logger.error("pipeline_save_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save pipeline"
        )


@router.get(
    "",
    response_model=PipelineListResponse,
    summary="List saved pipelines",
    description="Get list of saved pipeline configurations",
)
async def list_pipelines(
    offset: int = 0,
    limit: int = 100,
    tags: Annotated[Optional[List[str]], Query()] = None,
    pipeline_service: PipelineService = Depends(get_pipeline_service),
):
    """
    List saved pipelines.

    Returns paginated list of saved pipelines, optionally filtered by tags.
    """
    try:
        result = pipeline_service.list_pipelines(
            offset=offset,
            limit=limit,
            tags=tags,
        )
        return PipelineListResponse(**result)

    except Exception as e:
        logger.error("pipeline_list_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list pipelines"
        )


@router.get(
    "/{pipeline_id}",
    response_model=SavedPipeline,
    summary="Get saved pipeline",
    description="Get specific saved pipeline by ID",
    responses={
        200: {"description": "Pipeline found"},
        404: {"description": "Pipeline not found"},
    }
)
async def get_pipeline(
    pipeline_id: UUID,
    pipeline_service: PipelineService = Depends(get_pipeline_service),
):
    """
    Get saved pipeline.

    Returns complete pipeline configuration including all operations.
    """
    pipeline = pipeline_service.get_pipeline(pipeline_id)

    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline not found: {pipeline_id}"
        )

    return pipeline


@router.put(
    "/{pipeline_id}",
    response_model=SavedPipeline,
    summary="Update saved pipeline",
    description="Update existing pipeline configuration",
    responses={
        200: {"description": "Pipeline updated"},
        400: {"description": "Invalid pipeline configuration"},
        404: {"description": "Pipeline not found"},
    }
)
async def update_pipeline(
    pipeline_id: UUID,
    request: PipelineSaveRequest,
    pipeline_service: PipelineService = Depends(get_pipeline_service),
):
    """
    Update saved pipeline.

    Modifies existing pipeline with new configuration.
    """
    try:
        updated = pipeline_service.update_pipeline(
            pipeline_id=pipeline_id,
            name=request.name,
            description=request.description,
            operations=request.operations,
            tags=request.tags,
        )
        return updated

    except PipelineValidationError as e:
        logger.warning(
            "pipeline_update_validation_failed",
            pipeline_id=str(pipeline_id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    except Exception as e:
        logger.error(
            "pipeline_update_error",
            pipeline_id=str(pipeline_id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update pipeline"
        )


@router.delete(
    "/{pipeline_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete saved pipeline",
    description="Delete pipeline configuration",
    responses={
        204: {"description": "Pipeline deleted"},
        404: {"description": "Pipeline not found"},
    }
)
async def delete_pipeline(
    pipeline_id: UUID,
    pipeline_service: PipelineService = Depends(get_pipeline_service),
):
    """
    Delete saved pipeline.

    Permanently removes pipeline configuration.
    """
    try:
        pipeline_service.delete_pipeline(pipeline_id)
        return None

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline not found: {pipeline_id}"
        )

    except Exception as e:
        logger.error(
            "pipeline_delete_error",
            pipeline_id=str(pipeline_id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete pipeline"
        )
