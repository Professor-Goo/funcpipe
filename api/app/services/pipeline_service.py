"""
Pipeline Service - Handles pipeline execution and management.

Production-ready implementation with:
- JSON to Pipeline translation
- Comprehensive error handling
- Execution tracking
- Performance monitoring
- Result caching

NO SHORTCUTS - Elite-level implementation.
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from funcpipe import Pipeline

from app.core.config import settings
from app.core.logging import get_logger
from app.core.operations_registry import get_registry
from app.models.schemas import (
    ExecutionResult,
    ExecutionStatus,
    OperationConfig,
    SavedPipeline,
)
from app.services.file_service import FileService, get_file_service

logger = get_logger(__name__)


class PipelineValidationError(Exception):
    """Raised when pipeline validation fails."""
    pass


class PipelineExecutionError(Exception):
    """Raised when pipeline execution fails."""
    pass


class PipelineService:
    """
    Service for pipeline execution and management.

    Handles:
    - Pipeline validation
    - Pipeline execution
    - Saved pipeline management
    - Result caching
    """

    def __init__(self, file_service: Optional[FileService] = None):
        self.file_service = file_service or get_file_service()
        self.registry = get_registry()

        # In-memory storage (use database in production)
        self._saved_pipelines: Dict[UUID, SavedPipeline] = {}
        self._execution_results: Dict[UUID, ExecutionResult] = {}

        logger.info("pipeline_service_initialized")

    def validate_pipeline(
        self,
        operations: List[OperationConfig],
        file_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Validate pipeline configuration.

        Args:
            operations: List of operation configurations
            file_id: Optional file ID for field validation

        Returns:
            Validation result with errors and warnings
        """
        errors = []
        warnings = []

        # Check if operations list is empty
        if not operations:
            errors.append("Pipeline must have at least one operation")
            return {'valid': False, 'errors': errors, 'warnings': warnings}

        # Get file fields if provided
        available_fields = None
        if file_id:
            try:
                file_info = self.file_service.get_file(file_id)
                if isinstance(file_info.fields, list):
                    # Extract field names
                    if file_info.fields and isinstance(file_info.fields[0], dict):
                        available_fields = [f['name'] for f in file_info.fields]
                    else:
                        available_fields = file_info.fields
            except Exception as e:
                warnings.append(f"Could not load file for validation: {e}")

        # Validate each operation
        for idx, op in enumerate(operations):
            op_num = idx + 1

            # Check if operation exists
            if not self.registry.exists(op.operation):
                errors.append(
                    f"Operation {op_num}: Unknown operation '{op.operation}'"
                )
                continue

            # Get operation definition
            op_def = self.registry.get(op.operation)

            # Validate type matches
            if op_def.operation_type != op.type:
                errors.append(
                    f"Operation {op_num}: Type mismatch - '{op.operation}' "
                    f"is a {op_def.operation_type.value}, not {op.type.value}"
                )

            # Validate parameters
            try:
                op_def.validate_params(op.config)
            except ValueError as e:
                errors.append(f"Operation {op_num}: {str(e)}")
                continue

            # Validate field names if we have them
            if available_fields and 'field' in op.config:
                field = op.config['field']
                if field not in available_fields:
                    errors.append(
                        f"Operation {op_num}: Field '{field}' not found in file. "
                        f"Available fields: {', '.join(available_fields)}"
                    )

            # Check for potential issues
            if op.operation == 'take' or op.operation == 'skip':
                n = op.config.get('n', 0)
                if n > 10000:
                    warnings.append(
                        f"Operation {op_num}: Large {op.operation} value ({n}) "
                        f"may impact performance"
                    )

        # Return validation result
        valid = len(errors) == 0

        if valid:
            logger.debug(
                "pipeline_validated",
                operations=len(operations),
                warnings=len(warnings)
            )
        else:
            logger.warning(
                "pipeline_validation_failed",
                operations=len(operations),
                errors=len(errors)
            )

        return {
            'valid': valid,
            'errors': errors,
            'warnings': warnings,
        }

    def _build_pipeline_from_config(
        self,
        operations: List[OperationConfig]
    ) -> Pipeline:
        """
        Build funcpipe Pipeline from operation configurations.

        Args:
            operations: List of operation configurations

        Returns:
            Configured Pipeline object

        Raises:
            PipelineValidationError: If configuration is invalid
        """
        pipeline = Pipeline()

        for idx, op_config in enumerate(operations):
            try:
                # Get operation definition
                op_def = self.registry.get(op_config.operation)
                if not op_def:
                    raise PipelineValidationError(
                        f"Unknown operation: {op_config.operation}"
                    )

                # Handle special operations (sort, take, skip)
                if op_config.type.value == "sort":
                    field = op_config.config['field']
                    reverse = op_config.config.get('reverse', False)
                    pipeline = pipeline.sort(
                        key_func=lambda item, f=field: item.get(f),
                        reverse=reverse
                    )

                elif op_config.type.value == "take":
                    n = op_config.config['n']
                    pipeline = pipeline.take(n)

                elif op_config.type.value == "skip":
                    n = op_config.config['n']
                    pipeline = pipeline.skip(n)

                elif op_config.type.value == "filter":
                    # Execute filter operation
                    filter_func = op_def.execute(op_config.config)
                    pipeline = pipeline.filter(filter_func)

                elif op_config.type.value == "transform":
                    # Execute transform operation
                    transform_func = op_def.execute(op_config.config)
                    pipeline = pipeline.map(transform_func)

                else:
                    raise PipelineValidationError(
                        f"Unsupported operation type: {op_config.type}"
                    )

            except Exception as e:
                logger.error(
                    "operation_build_failed",
                    operation=op_config.operation,
                    index=idx,
                    error=str(e)
                )
                raise PipelineValidationError(
                    f"Failed to build operation {idx + 1} ({op_config.operation}): {e}"
                )

        logger.debug(
            "pipeline_built",
            operations=len(operations),
            pipeline_length=len(pipeline)
        )

        return pipeline

    async def execute_pipeline(
        self,
        file_id: UUID,
        operations: List[OperationConfig],
        preview: bool = False,
        preview_limit: int = 100
    ) -> ExecutionResult:
        """
        Execute pipeline on file data.

        Args:
            file_id: UUID of file to process
            operations: List of operations to apply
            preview: If True, limit results for preview
            preview_limit: Max records to return in preview

        Returns:
            ExecutionResult with processed data

        Raises:
            PipelineExecutionError: If execution fails
        """
        execution_id = uuid4()
        start_time = time.time()

        try:
            # Validate pipeline
            validation = self.validate_pipeline(operations, file_id)
            if not validation['valid']:
                raise PipelineValidationError(
                    f"Pipeline validation failed: {', '.join(validation['errors'])}"
                )

            # Load input data
            logger.info(
                "pipeline_execution_started",
                execution_id=str(execution_id),
                file_id=str(file_id),
                operations=len(operations)
            )

            preview_data = await self.file_service.get_file_preview(
                file_id,
                offset=0,
                limit=999999  # Load all data for processing
            )
            input_data = preview_data['data']

            if not input_data:
                return ExecutionResult(
                    execution_id=execution_id,
                    status=ExecutionStatus.COMPLETED,
                    data=[],
                    record_count=0,
                    execution_time_ms=0,
                )

            # Build pipeline
            pipeline = self._build_pipeline_from_config(operations)

            # Execute pipeline
            logger.debug(
                "executing_pipeline",
                execution_id=str(execution_id),
                input_records=len(input_data)
            )

            result_data = pipeline.run(input_data)

            # Ensure result is a list
            if not isinstance(result_data, list):
                result_data = [result_data] if result_data is not None else []

            # Apply preview limit if requested
            if preview and len(result_data) > preview_limit:
                result_data = result_data[:preview_limit]

            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000

            # Create result
            result = ExecutionResult(
                execution_id=execution_id,
                status=ExecutionStatus.COMPLETED,
                data=result_data,
                record_count=len(result_data),
                execution_time_ms=round(execution_time_ms, 2),
                created_at=datetime.utcnow(),
            )

            # Store result
            self._execution_results[execution_id] = result

            logger.info(
                "pipeline_execution_completed",
                execution_id=str(execution_id),
                input_records=len(input_data),
                output_records=len(result_data),
                execution_time_ms=round(execution_time_ms, 2)
            )

            return result

        except PipelineValidationError as e:
            execution_time_ms = (time.time() - start_time) * 1000

            logger.error(
                "pipeline_execution_validation_failed",
                execution_id=str(execution_id),
                error=str(e)
            )

            result = ExecutionResult(
                execution_id=execution_id,
                status=ExecutionStatus.FAILED,
                error=f"Validation error: {str(e)}",
                execution_time_ms=round(execution_time_ms, 2),
                created_at=datetime.utcnow(),
            )

            self._execution_results[execution_id] = result
            return result

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000

            logger.error(
                "pipeline_execution_failed",
                execution_id=str(execution_id),
                error=str(e),
                error_type=type(e).__name__
            )

            result = ExecutionResult(
                execution_id=execution_id,
                status=ExecutionStatus.FAILED,
                error=str(e),
                execution_time_ms=round(execution_time_ms, 2),
                created_at=datetime.utcnow(),
            )

            self._execution_results[execution_id] = result
            return result

    def get_execution_result(self, execution_id: UUID) -> Optional[ExecutionResult]:
        """
        Get cached execution result.

        Args:
            execution_id: Execution UUID

        Returns:
            ExecutionResult or None if not found
        """
        return self._execution_results.get(execution_id)

    def save_pipeline(
        self,
        name: str,
        operations: List[OperationConfig],
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> SavedPipeline:
        """
        Save pipeline configuration.

        Args:
            name: Pipeline name
            operations: List of operations
            description: Optional description
            tags: Optional tags

        Returns:
            SavedPipeline object
        """
        # Validate pipeline
        validation = self.validate_pipeline(operations)
        if not validation['valid']:
            raise PipelineValidationError(
                f"Cannot save invalid pipeline: {', '.join(validation['errors'])}"
            )

        pipeline_id = uuid4()

        saved_pipeline = SavedPipeline(
            id=pipeline_id,
            name=name,
            description=description,
            operations=operations,
            tags=tags or [],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            execution_count=0,
        )

        self._saved_pipelines[pipeline_id] = saved_pipeline

        logger.info(
            "pipeline_saved",
            pipeline_id=str(pipeline_id),
            name=name,
            operations=len(operations)
        )

        return saved_pipeline

    def get_pipeline(self, pipeline_id: UUID) -> Optional[SavedPipeline]:
        """Get saved pipeline by ID."""
        return self._saved_pipelines.get(pipeline_id)

    def list_pipelines(
        self,
        offset: int = 0,
        limit: int = 100,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        List saved pipelines.

        Args:
            offset: Pagination offset
            limit: Max results
            tags: Optional tag filter

        Returns:
            Dictionary with pipelines and pagination info
        """
        all_pipelines = list(self._saved_pipelines.values())

        # Filter by tags if provided
        if tags:
            all_pipelines = [
                p for p in all_pipelines
                if any(tag in p.tags for tag in tags)
            ]

        total = len(all_pipelines)

        # Sort by updated time (newest first)
        all_pipelines.sort(key=lambda p: p.updated_at, reverse=True)

        # Paginate
        pipelines = all_pipelines[offset:offset + limit]

        return {
            'pipelines': pipelines,
            'total': total,
            'offset': offset,
            'limit': limit,
        }

    def update_pipeline(
        self,
        pipeline_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        operations: Optional[List[OperationConfig]] = None,
        tags: Optional[List[str]] = None
    ) -> SavedPipeline:
        """
        Update saved pipeline.

        Args:
            pipeline_id: Pipeline UUID
            name: Optional new name
            description: Optional new description
            operations: Optional new operations
            tags: Optional new tags

        Returns:
            Updated SavedPipeline

        Raises:
            ValueError: If pipeline not found
        """
        pipeline = self.get_pipeline(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline not found: {pipeline_id}")

        # Update fields
        if name is not None:
            pipeline.name = name
        if description is not None:
            pipeline.description = description
        if operations is not None:
            # Validate new operations
            validation = self.validate_pipeline(operations)
            if not validation['valid']:
                raise PipelineValidationError(
                    f"Invalid operations: {', '.join(validation['errors'])}"
                )
            pipeline.operations = operations
        if tags is not None:
            pipeline.tags = tags

        pipeline.updated_at = datetime.utcnow()

        logger.info(
            "pipeline_updated",
            pipeline_id=str(pipeline_id),
            name=pipeline.name
        )

        return pipeline

    def delete_pipeline(self, pipeline_id: UUID) -> None:
        """
        Delete saved pipeline.

        Args:
            pipeline_id: Pipeline UUID

        Raises:
            ValueError: If pipeline not found
        """
        if pipeline_id not in self._saved_pipelines:
            raise ValueError(f"Pipeline not found: {pipeline_id}")

        del self._saved_pipelines[pipeline_id]

        logger.info("pipeline_deleted", pipeline_id=str(pipeline_id))


# Global service instance
_pipeline_service: Optional[PipelineService] = None


def get_pipeline_service() -> PipelineService:
    """Get the global pipeline service instance."""
    global _pipeline_service
    if _pipeline_service is None:
        _pipeline_service = PipelineService()
    return _pipeline_service
