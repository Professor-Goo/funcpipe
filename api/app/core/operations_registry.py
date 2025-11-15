"""
Operation Registry - Maps operation names to funcpipe functions.

This module provides the critical translation layer between JSON API requests
and Python funcpipe library calls. Every operation is registered with:
- Type safety and validation
- Parameter schemas
- Examples and documentation
- Runtime execution

NO SHORTCUTS - Production-ready implementation with comprehensive error handling.
"""

import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type

# Add parent directory to path to import funcpipe
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from funcpipe import filters, transforms
from pydantic import BaseModel, Field, ValidationError

from app.core.logging import get_logger
from app.models.schemas import OperationMetadata, OperationParameter, OperationType

logger = get_logger(__name__)


# ============================================================================
# Parameter Validation Schemas
# ============================================================================

class FilterParams(BaseModel):
    """Base class for filter parameters."""
    pass


class ComparisonFilterParams(FilterParams):
    """Parameters for comparison filters (>, <, ==, etc.)."""
    field: str = Field(..., min_length=1, description="Field name to compare")
    value: Any = Field(..., description="Value to compare against")


class StringFilterParams(FilterParams):
    """Parameters for string filters (contains, starts_with, etc.)."""
    field: str = Field(..., min_length=1)
    substring: Optional[str] = Field(None, min_length=1)
    prefix: Optional[str] = None
    suffix: Optional[str] = None
    case_sensitive: bool = Field(default=True)


class RegexFilterParams(FilterParams):
    """Parameters for regex filter."""
    field: str = Field(..., min_length=1)
    pattern: str = Field(..., min_length=1)
    flags: int = Field(default=0, ge=0)


class NullFilterParams(FilterParams):
    """Parameters for null check filters."""
    field: str = Field(..., min_length=1)


class ListFilterParams(FilterParams):
    """Parameters for list membership filters."""
    field: str = Field(..., min_length=1)
    values: List[Any] = Field(..., min_length=1)


class BetweenFilterParams(FilterParams):
    """Parameters for between filter."""
    field: str = Field(..., min_length=1)
    min_val: float = Field(...)
    max_val: float = Field(...)
    inclusive: bool = Field(default=True)

    def __init__(self, **data):
        super().__init__(**data)
        if self.min_val >= self.max_val:
            raise ValueError("min_val must be less than max_val")


class LogicalFilterParams(FilterParams):
    """Parameters for logical combinators (AND, OR, NOT)."""
    predicates: List[Dict[str, Any]] = Field(..., min_length=1)


# Transform parameter schemas

class FieldTransformParams(BaseModel):
    """Parameters for simple field transforms."""
    field: str = Field(..., min_length=1, description="Field name")


class AddFieldParams(BaseModel):
    """Parameters for add_field transform."""
    field: str = Field(..., min_length=1)
    value: Any = Field(...)


class RenameFieldParams(BaseModel):
    """Parameters for rename_field transform."""
    old_name: str = Field(..., min_length=1)
    new_name: str = Field(..., min_length=1)


class NumericTransformParams(BaseModel):
    """Parameters for numeric transforms."""
    field: str = Field(..., min_length=1)
    factor: Optional[float] = None
    value: Optional[float] = None
    decimals: Optional[int] = Field(None, ge=0)


class CastFieldParams(BaseModel):
    """Parameters for cast_field transform."""
    field: str = Field(..., min_length=1)
    target_type: str = Field(..., pattern="^(int|float|str|bool)$")


class ReplaceInFieldParams(BaseModel):
    """Parameters for replace_in_field transform."""
    field: str = Field(..., min_length=1)
    old: str = Field(...)
    new: str = Field(...)
    case_sensitive: bool = Field(default=True)


class SelectFieldsParams(BaseModel):
    """Parameters for select/exclude fields."""
    fields: List[str] = Field(..., min_length=1)


# ============================================================================
# Operation Registry
# ============================================================================

class OperationDefinition:
    """Definition of a single operation with validation and execution."""

    def __init__(
        self,
        name: str,
        operation_type: OperationType,
        display_name: str,
        description: str,
        param_schema: Type[BaseModel],
        executor: Callable,
        parameters: List[OperationParameter],
        examples: Optional[List[Dict[str, Any]]] = None,
    ):
        self.name = name
        self.operation_type = operation_type
        self.display_name = display_name
        self.description = description
        self.param_schema = param_schema
        self.executor = executor
        self.parameters = parameters
        self.examples = examples or []

    def validate_params(self, params: Dict[str, Any]) -> BaseModel:
        """Validate parameters against schema."""
        try:
            return self.param_schema(**params)
        except ValidationError as e:
            logger.error(
                "parameter_validation_failed",
                operation=self.name,
                errors=e.errors()
            )
            raise ValueError(f"Invalid parameters for {self.name}: {e}")

    def execute(self, params: Dict[str, Any]) -> Callable:
        """Execute the operation with validated parameters."""
        validated = self.validate_params(params)
        try:
            return self.executor(validated)
        except Exception as e:
            logger.error(
                "operation_execution_failed",
                operation=self.name,
                error=str(e)
            )
            raise RuntimeError(f"Failed to execute {self.name}: {e}")

    def to_metadata(self) -> OperationMetadata:
        """Convert to API metadata model."""
        return OperationMetadata(
            type=self.operation_type,
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            parameters=self.parameters,
            examples=self.examples,
        )


class OperationsRegistry:
    """
    Registry of all available operations.

    This is the source of truth for operation mapping.
    Production-ready with full validation and error handling.
    """

    def __init__(self):
        self._operations: Dict[str, OperationDefinition] = {}
        self._register_all_operations()
        logger.info(
            "operations_registry_initialized",
            total_operations=len(self._operations)
        )

    def _register_all_operations(self):
        """Register all available operations."""
        # Register filters
        self._register_filter_operations()
        # Register transforms
        self._register_transform_operations()

    def _register_filter_operations(self):
        """Register all filter operations."""

        # Comparison filters
        self.register(OperationDefinition(
            name="equals",
            operation_type=OperationType.FILTER,
            display_name="Equals",
            description="Filter records where field value equals specified value",
            param_schema=ComparisonFilterParams,
            executor=lambda p: filters.equals(p.field, p.value),
            parameters=[
                OperationParameter(
                    name="field",
                    type="str",
                    required=True,
                    description="Field name to check"
                ),
                OperationParameter(
                    name="value",
                    type="Any",
                    required=True,
                    description="Value to match"
                ),
            ],
            examples=[
                {"field": "status", "value": "active"},
                {"field": "age", "value": 25},
            ],
        ))

        self.register(OperationDefinition(
            name="greater_than",
            operation_type=OperationType.FILTER,
            display_name="Greater Than",
            description="Filter records where field value is greater than specified value",
            param_schema=ComparisonFilterParams,
            executor=lambda p: filters.greater_than(p.field, p.value),
            parameters=[
                OperationParameter(
                    name="field",
                    type="str",
                    required=True,
                    description="Field name to compare"
                ),
                OperationParameter(
                    name="value",
                    type="Union[int, float]",
                    required=True,
                    description="Minimum value (exclusive)"
                ),
            ],
            examples=[
                {"field": "age", "value": 25},
                {"field": "salary", "value": 50000.0},
            ],
        ))

        self.register(OperationDefinition(
            name="greater_than_or_equal",
            operation_type=OperationType.FILTER,
            display_name="Greater Than or Equal",
            description="Filter records where field value is >= specified value",
            param_schema=ComparisonFilterParams,
            executor=lambda p: filters.greater_than_or_equal(p.field, p.value),
            parameters=[
                OperationParameter(name="field", type="str", required=True),
                OperationParameter(name="value", type="Union[int, float]", required=True),
            ],
            examples=[{"field": "age", "value": 18}],
        ))

        self.register(OperationDefinition(
            name="less_than",
            operation_type=OperationType.FILTER,
            display_name="Less Than",
            description="Filter records where field value is less than specified value",
            param_schema=ComparisonFilterParams,
            executor=lambda p: filters.less_than(p.field, p.value),
            parameters=[
                OperationParameter(name="field", type="str", required=True),
                OperationParameter(name="value", type="Union[int, float]", required=True),
            ],
            examples=[{"field": "price", "value": 100.0}],
        ))

        self.register(OperationDefinition(
            name="less_than_or_equal",
            operation_type=OperationType.FILTER,
            display_name="Less Than or Equal",
            description="Filter records where field value is <= specified value",
            param_schema=ComparisonFilterParams,
            executor=lambda p: filters.less_than_or_equal(p.field, p.value),
            parameters=[
                OperationParameter(name="field", type="str", required=True),
                OperationParameter(name="value", type="Union[int, float]", required=True),
            ],
            examples=[{"field": "quantity", "value": 10}],
        ))

        # String filters
        self.register(OperationDefinition(
            name="contains",
            operation_type=OperationType.FILTER,
            display_name="Contains",
            description="Filter records where field contains substring",
            param_schema=StringFilterParams,
            executor=lambda p: filters.contains(
                p.field,
                p.substring or "",
                p.case_sensitive
            ),
            parameters=[
                OperationParameter(name="field", type="str", required=True),
                OperationParameter(name="substring", type="str", required=True),
                OperationParameter(
                    name="case_sensitive",
                    type="bool",
                    required=False,
                    default=True
                ),
            ],
            examples=[
                {"field": "name", "substring": "john", "case_sensitive": False},
            ],
        ))

        self.register(OperationDefinition(
            name="starts_with",
            operation_type=OperationType.FILTER,
            display_name="Starts With",
            description="Filter records where field starts with prefix",
            param_schema=StringFilterParams,
            executor=lambda p: filters.starts_with(
                p.field,
                p.prefix or "",
                p.case_sensitive
            ),
            parameters=[
                OperationParameter(name="field", type="str", required=True),
                OperationParameter(name="prefix", type="str", required=True),
                OperationParameter(name="case_sensitive", type="bool", default=True),
            ],
            examples=[{"field": "email", "prefix": "admin@"}],
        ))

        self.register(OperationDefinition(
            name="ends_with",
            operation_type=OperationType.FILTER,
            display_name="Ends With",
            description="Filter records where field ends with suffix",
            param_schema=StringFilterParams,
            executor=lambda p: filters.ends_with(
                p.field,
                p.suffix or "",
                p.case_sensitive
            ),
            parameters=[
                OperationParameter(name="field", type="str", required=True),
                OperationParameter(name="suffix", type="str", required=True),
                OperationParameter(name="case_sensitive", type="bool", default=True),
            ],
            examples=[{"field": "filename", "suffix": ".csv"}],
        ))

        # Regex filter
        self.register(OperationDefinition(
            name="matches_regex",
            operation_type=OperationType.FILTER,
            display_name="Matches Regex",
            description="Filter records where field matches regular expression",
            param_schema=RegexFilterParams,
            executor=lambda p: filters.matches_regex(p.field, p.pattern, p.flags),
            parameters=[
                OperationParameter(name="field", type="str", required=True),
                OperationParameter(name="pattern", type="str", required=True),
                OperationParameter(name="flags", type="int", default=0),
            ],
            examples=[{"field": "email", "pattern": r"^[\w\.-]+@[\w\.-]+\.\w+$"}],
        ))

        # Null filters
        self.register(OperationDefinition(
            name="is_null",
            operation_type=OperationType.FILTER,
            display_name="Is Null",
            description="Filter records where field is null/None",
            param_schema=NullFilterParams,
            executor=lambda p: filters.is_null(p.field),
            parameters=[
                OperationParameter(name="field", type="str", required=True),
            ],
            examples=[{"field": "middle_name"}],
        ))

        self.register(OperationDefinition(
            name="is_not_null",
            operation_type=OperationType.FILTER,
            display_name="Is Not Null",
            description="Filter records where field is not null",
            param_schema=NullFilterParams,
            executor=lambda p: filters.is_not_null(p.field),
            parameters=[
                OperationParameter(name="field", type="str", required=True),
            ],
            examples=[{"field": "email"}],
        ))

        # List filters
        self.register(OperationDefinition(
            name="in_list",
            operation_type=OperationType.FILTER,
            display_name="In List",
            description="Filter records where field value is in list",
            param_schema=ListFilterParams,
            executor=lambda p: filters.in_list(p.field, p.values),
            parameters=[
                OperationParameter(name="field", type="str", required=True),
                OperationParameter(name="values", type="List[Any]", required=True),
            ],
            examples=[
                {"field": "status", "values": ["active", "pending"]},
            ],
        ))

        self.register(OperationDefinition(
            name="not_in_list",
            operation_type=OperationType.FILTER,
            display_name="Not In List",
            description="Filter records where field value is not in list",
            param_schema=ListFilterParams,
            executor=lambda p: filters.not_in_list(p.field, p.values),
            parameters=[
                OperationParameter(name="field", type="str", required=True),
                OperationParameter(name="values", type="List[Any]", required=True),
            ],
            examples=[
                {"field": "status", "values": ["deleted", "archived"]},
            ],
        ))

        # Between filter
        self.register(OperationDefinition(
            name="between",
            operation_type=OperationType.FILTER,
            display_name="Between",
            description="Filter records where field value is between min and max",
            param_schema=BetweenFilterParams,
            executor=lambda p: filters.between(
                p.field,
                p.min_val,
                p.max_val,
                p.inclusive
            ),
            parameters=[
                OperationParameter(name="field", type="str", required=True),
                OperationParameter(name="min_val", type="float", required=True),
                OperationParameter(name="max_val", type="float", required=True),
                OperationParameter(name="inclusive", type="bool", default=True),
            ],
            examples=[
                {"field": "age", "min_val": 18, "max_val": 65, "inclusive": True},
            ],
        ))

    def _register_transform_operations(self):
        """Register all transform operations."""

        # Field manipulation
        self.register(OperationDefinition(
            name="add_field",
            operation_type=OperationType.TRANSFORM,
            display_name="Add Field",
            description="Add a new field with static value",
            param_schema=AddFieldParams,
            executor=lambda p: transforms.add_field(p.field, p.value),
            parameters=[
                OperationParameter(name="field", type="str", required=True),
                OperationParameter(name="value", type="Any", required=True),
            ],
            examples=[
                {"field": "status", "value": "processed"},
                {"field": "version", "value": 1},
            ],
        ))

        self.register(OperationDefinition(
            name="remove_field",
            operation_type=OperationType.TRANSFORM,
            display_name="Remove Field",
            description="Remove a field from records",
            param_schema=FieldTransformParams,
            executor=lambda p: transforms.remove_field(p.field),
            parameters=[
                OperationParameter(name="field", type="str", required=True),
            ],
            examples=[{"field": "internal_id"}],
        ))

        self.register(OperationDefinition(
            name="rename_field",
            operation_type=OperationType.TRANSFORM,
            display_name="Rename Field",
            description="Rename a field",
            param_schema=RenameFieldParams,
            executor=lambda p: transforms.rename_field(p.old_name, p.new_name),
            parameters=[
                OperationParameter(name="old_name", type="str", required=True),
                OperationParameter(name="new_name", type="str", required=True),
            ],
            examples=[{"old_name": "fname", "new_name": "first_name"}],
        ))

        # String transforms
        self.register(OperationDefinition(
            name="capitalize_field",
            operation_type=OperationType.TRANSFORM,
            display_name="Capitalize Field",
            description="Capitalize first letter of string field",
            param_schema=FieldTransformParams,
            executor=lambda p: transforms.capitalize_field(p.field),
            parameters=[
                OperationParameter(name="field", type="str", required=True),
            ],
            examples=[{"field": "name"}],
        ))

        self.register(OperationDefinition(
            name="upper_field",
            operation_type=OperationType.TRANSFORM,
            display_name="Uppercase Field",
            description="Convert string field to uppercase",
            param_schema=FieldTransformParams,
            executor=lambda p: transforms.upper_field(p.field),
            parameters=[
                OperationParameter(name="field", type="str", required=True),
            ],
            examples=[{"field": "country_code"}],
        ))

        self.register(OperationDefinition(
            name="lower_field",
            operation_type=OperationType.TRANSFORM,
            display_name="Lowercase Field",
            description="Convert string field to lowercase",
            param_schema=FieldTransformParams,
            executor=lambda p: transforms.lower_field(p.field),
            parameters=[
                OperationParameter(name="field", type="str", required=True),
            ],
            examples=[{"field": "email"}],
        ))

        self.register(OperationDefinition(
            name="strip_field",
            operation_type=OperationType.TRANSFORM,
            display_name="Strip Whitespace",
            description="Remove leading/trailing whitespace from field",
            param_schema=FieldTransformParams,
            executor=lambda p: transforms.strip_field(p.field),
            parameters=[
                OperationParameter(name="field", type="str", required=True),
            ],
            examples=[{"field": "name"}],
        ))

        # Numeric transforms
        self.register(OperationDefinition(
            name="multiply_field",
            operation_type=OperationType.TRANSFORM,
            display_name="Multiply Field",
            description="Multiply numeric field by factor",
            param_schema=NumericTransformParams,
            executor=lambda p: transforms.multiply_field(p.field, p.factor or 1.0),
            parameters=[
                OperationParameter(name="field", type="str", required=True),
                OperationParameter(name="factor", type="float", required=True),
            ],
            examples=[
                {"field": "price", "factor": 1.1},  # 10% increase
                {"field": "quantity", "factor": 2.0},  # Double
            ],
        ))

        self.register(OperationDefinition(
            name="add_to_field",
            operation_type=OperationType.TRANSFORM,
            display_name="Add to Field",
            description="Add value to numeric field",
            param_schema=NumericTransformParams,
            executor=lambda p: transforms.add_to_field(p.field, p.value or 0.0),
            parameters=[
                OperationParameter(name="field", type="str", required=True),
                OperationParameter(name="value", type="float", required=True),
            ],
            examples=[{"field": "score", "value": 10}],
        ))

        self.register(OperationDefinition(
            name="round_field",
            operation_type=OperationType.TRANSFORM,
            display_name="Round Field",
            description="Round numeric field to specified decimals",
            param_schema=NumericTransformParams,
            executor=lambda p: transforms.round_field(p.field, p.decimals or 0),
            parameters=[
                OperationParameter(name="field", type="str", required=True),
                OperationParameter(name="decimals", type="int", default=0),
            ],
            examples=[{"field": "price", "decimals": 2}],
        ))

        # Type casting
        self.register(OperationDefinition(
            name="cast_field",
            operation_type=OperationType.TRANSFORM,
            display_name="Cast Field Type",
            description="Convert field to different type",
            param_schema=CastFieldParams,
            executor=lambda p: transforms.cast_field(
                p.field,
                {"int": int, "float": float, "str": str, "bool": bool}[p.target_type]
            ),
            parameters=[
                OperationParameter(name="field", type="str", required=True),
                OperationParameter(
                    name="target_type",
                    type="str",
                    required=True,
                    description="Target type: int, float, str, or bool"
                ),
            ],
            examples=[
                {"field": "age", "target_type": "int"},
                {"field": "price", "target_type": "float"},
            ],
        ))

        # String replacement
        self.register(OperationDefinition(
            name="replace_in_field",
            operation_type=OperationType.TRANSFORM,
            display_name="Replace in Field",
            description="Replace substring in field",
            param_schema=ReplaceInFieldParams,
            executor=lambda p: transforms.replace_in_field(
                p.field,
                p.old,
                p.new,
                p.case_sensitive
            ),
            parameters=[
                OperationParameter(name="field", type="str", required=True),
                OperationParameter(name="old", type="str", required=True),
                OperationParameter(name="new", type="str", required=True),
                OperationParameter(name="case_sensitive", type="bool", default=True),
            ],
            examples=[
                {"field": "description", "old": "color", "new": "colour"},
            ],
        ))

        # Field selection
        self.register(OperationDefinition(
            name="select_fields",
            operation_type=OperationType.TRANSFORM,
            display_name="Select Fields",
            description="Keep only specified fields",
            param_schema=SelectFieldsParams,
            executor=lambda p: transforms.select_fields(p.fields),
            parameters=[
                OperationParameter(name="fields", type="List[str]", required=True),
            ],
            examples=[{"fields": ["name", "email", "age"]}],
        ))

        self.register(OperationDefinition(
            name="exclude_fields",
            operation_type=OperationType.TRANSFORM,
            display_name="Exclude Fields",
            description="Remove specified fields",
            param_schema=SelectFieldsParams,
            executor=lambda p: transforms.exclude_fields(p.fields),
            parameters=[
                OperationParameter(name="fields", type="List[str]", required=True),
            ],
            examples=[{"fields": ["password", "ssn", "internal_id"]}],
        ))

    def register(self, operation: OperationDefinition):
        """Register an operation."""
        if operation.name in self._operations:
            raise ValueError(f"Operation '{operation.name}' already registered")
        self._operations[operation.name] = operation
        logger.debug("operation_registered", name=operation.name, type=operation.operation_type)

    def get(self, name: str) -> Optional[OperationDefinition]:
        """Get operation by name."""
        return self._operations.get(name)

    def get_all(self) -> List[OperationDefinition]:
        """Get all registered operations."""
        return list(self._operations.values())

    def get_by_type(self, operation_type: OperationType) -> List[OperationDefinition]:
        """Get all operations of specific type."""
        return [
            op for op in self._operations.values()
            if op.operation_type == operation_type
        ]

    def exists(self, name: str) -> bool:
        """Check if operation exists."""
        return name in self._operations


# Global registry instance
_registry: Optional[OperationsRegistry] = None


def get_registry() -> OperationsRegistry:
    """Get the global operations registry instance."""
    global _registry
    if _registry is None:
        _registry = OperationsRegistry()
    return _registry
