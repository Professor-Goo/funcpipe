"""
Operations Metadata API Routes.

Endpoints for retrieving available operations and their parameters.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.logging import get_logger
from app.core.operations_registry import OperationsRegistry, get_registry
from app.models.schemas import OperationMetadata, OperationsListResponse, OperationType

logger = get_logger(__name__)

router = APIRouter(prefix="/operations", tags=["operations"])


@router.get(
    "",
    response_model=OperationsListResponse,
    summary="List all available operations",
    description="Get complete list of all available filter, transform, and utility operations",
)
async def list_operations(
    registry: OperationsRegistry = Depends(get_registry),
):
    """
    List all available operations.

    Returns comprehensive list of all operations with their parameters,
    descriptions, and examples. Use this to build pipeline configurations.
    """
    try:
        filters = [
            op.to_metadata()
            for op in registry.get_by_type(OperationType.FILTER)
        ]

        transforms = [
            op.to_metadata()
            for op in registry.get_by_type(OperationType.TRANSFORM)
        ]

        # Utility operations (sort, take, skip) are implicitly available
        # They don't need to be registered as they're built into Pipeline
        utilities = [
            OperationMetadata(
                type=OperationType.SORT,
                name="sort",
                display_name="Sort",
                description="Sort records by field value",
                parameters=[
                    {
                        "name": "field",
                        "type": "str",
                        "required": True,
                        "description": "Field name to sort by"
                    },
                    {
                        "name": "reverse",
                        "type": "bool",
                        "required": False,
                        "default": False,
                        "description": "Sort in descending order"
                    }
                ],
                examples=[
                    {"field": "age", "reverse": False},
                    {"field": "salary", "reverse": True}
                ]
            ),
            OperationMetadata(
                type=OperationType.TAKE,
                name="take",
                display_name="Take First N",
                description="Take first N records",
                parameters=[
                    {
                        "name": "n",
                        "type": "int",
                        "required": True,
                        "description": "Number of records to take"
                    }
                ],
                examples=[
                    {"n": 10},
                    {"n": 100}
                ]
            ),
            OperationMetadata(
                type=OperationType.SKIP,
                name="skip",
                display_name="Skip First N",
                description="Skip first N records",
                parameters=[
                    {
                        "name": "n",
                        "type": "int",
                        "required": True,
                        "description": "Number of records to skip"
                    }
                ],
                examples=[
                    {"n": 10},
                    {"n": 100}
                ]
            ),
        ]

        return OperationsListResponse(
            filters=filters,
            transforms=transforms,
            utilities=utilities,
        )

    except Exception as e:
        logger.error("operations_list_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list operations"
        )


@router.get(
    "/{operation_name}",
    response_model=OperationMetadata,
    summary="Get operation details",
    description="Get detailed information about a specific operation",
    responses={
        200: {"description": "Operation found"},
        404: {"description": "Operation not found"},
    }
)
async def get_operation(
    operation_name: str,
    registry: OperationsRegistry = Depends(get_registry),
):
    """
    Get details for specific operation.

    Returns complete parameter specifications and examples for the operation.
    """
    operation = registry.get(operation_name)

    if not operation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operation not found: {operation_name}"
        )

    return operation.to_metadata()
