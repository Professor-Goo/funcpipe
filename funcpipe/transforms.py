"""
Functional transforms for data processing pipelines.

All transforms are pure functions that return new data structures.
Supports currying and composition for flexible data transformations.
"""

from typing import Any, Callable, Dict, List, Union
from functools import partial
import copy
import re
import math


def add_field(field_name: str, value: Any) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Create transform to add a new field with static value.
    
    Args:
        field_name: Name of field to add
        value: Value to set
        
    Returns:
        Transform function
    """
    def transform(item: Dict[str, Any]) -> Dict[str, Any]:
        result = copy.deepcopy(item)
        result[field_name] = value
        return result
    
    transform.__name__ = f"add_field_{field_name}"
    return transform


def remove_field(field_name: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Create transform to remove a field.
    
    Args:
        field_name: Name of field to remove
        
    Returns:
        Transform function
    """
    def transform(item: Dict[str, Any]) -> Dict[str, Any]:
        result = copy.deepcopy(item)
        result.pop(field_name, None)
        return result
    
    transform.__name__ = f"remove_field_{field_name}"
    return transform


def rename_field(old_name: str, new_name: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Create transform to rename a field.
    
    Args:
        old_name: Current field name
        new_name: New field name
        
    Returns:
        Transform function
    """
    def transform(item: Dict[str, Any]) -> Dict[str, Any]:
        result = copy.deepcopy(item)
        if old_name in result:
            result[new_name] = result.pop(old_name)
        return result
    
    transform.__name__ = f"rename_field_{old_name}_to_{new_name}"
    return transform


def capitalize_field(field_name: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Create transform to capitalize a string field.
    
    Args:
        field_name: Name of field to capitalize
        
    Returns:
        Transform function
    """
    def transform(item: Dict[str, Any]) -> Dict[str, Any]:
        result = copy.deepcopy(item)
        if field_name in result and isinstance(result[field_name], str):
            result[field_name] = result[field_name].capitalize()
        return result
    
    transform.__name__ = f"capitalize_field_{field_name}"
    return transform


def upper_field(field_name: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """Create transform to uppercase a string field."""
    def transform(item: Dict[str, Any]) -> Dict[str, Any]:
        result = copy.deepcopy(item)
        if field_name in result and isinstance(result[field_name], str):
            result[field_name] = result[field_name].upper()
        return result
    
    transform.__name__ = f"upper_field_{field_name}"
    return transform


def lower_field(field_name: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """Create transform to lowercase a string field."""
    def transform(item: Dict[str, Any]) -> Dict[str, Any]:
        result = copy.deepcopy(item)
        if field_name in result and isinstance(result[field_name], str):
            result[field_name] = result[field_name].lower()
        return result
    
    transform.__name__ = f"lower_field_{field_name}"
    return transform


def strip_field(field_name: str, chars: str = None) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Create transform to strip whitespace from string field.
    
    Args:
        field_name: Name of field to strip
        chars: Characters to strip (default: whitespace)
        
    Returns:
        Transform function
    """
    def transform(item: Dict[str, Any]) -> Dict[str, Any]:
        result = copy.deepcopy(item)
        if field_name in result and isinstance(result[field_name], str):
            result[field_name] = result[field_name].strip(chars)
        return result
    
    transform.__name__ = f"strip_field_{field_name}"
    return transform


def replace_in_field(field_name: str, old: str, new: str, 
                    case_sensitive: bool = True) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Create transform to replace substring in field.
    
    Args:
        field_name: Name of field to modify
        old: Substring to replace
        new: Replacement substring
        case_sensitive: Whether replacement is case sensitive
        
    Returns:
        Transform function
    """
    def transform(item: Dict[str, Any]) -> Dict[str, Any]:
        result = copy.deepcopy(item)
        if field_name in result and isinstance(result[field_name], str):
            if case_sensitive:
                result[field_name] = result[field_name].replace(old, new)
            else:
                # Case-insensitive replace using regex
                pattern = re.compile(re.escape(old), re.IGNORECASE)
                result[field_name] = pattern.sub(new, result[field_name])
        return result
    
    transform.__name__ = f"replace_in_field_{field_name}"
    return transform


def multiply_field(field_name: str, factor: Union[int, float]) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Create transform to multiply numeric field.
    
    Args:
        field_name: Name of numeric field
        factor: Multiplication factor
        
    Returns:
        Transform function
    """
    def transform(item: Dict[str, Any]) -> Dict[str, Any]:
        result = copy.deepcopy(item)
        if field_name in result and isinstance(result[field_name], (int, float)):
            result[field_name] = result[field_name] * factor
        return result
    
    transform.__name__ = f"multiply_field_{field_name}_by_{factor}"
    return transform


def add_to_field(field_name: str, value: Union[int, float]) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """Create transform to add value to numeric field."""
    def transform(item: Dict[str, Any]) -> Dict[str, Any]:
        result = copy.deepcopy(item)
        if field_name in result and isinstance(result[field_name], (int, float)):
            result[field_name] = result[field_name] + value
        return result
    
    transform.__name__ = f"add_to_field_{field_name}"
    return transform


def round_field(field_name: str, decimals: int = 0) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Create transform to round numeric field.
    
    Args:
        field_name: Name of numeric field
        decimals: Number of decimal places
        
    Returns:
        Transform function
    """
    def transform(item: Dict[str, Any]) -> Dict[str, Any]:
        result = copy.deepcopy(item)
        if field_name in result and isinstance(result[field_name], (int, float)):
            result[field_name] = round(result[field_name], decimals)
        return result
    
    transform.__name__ = f"round_field_{field_name}_{decimals}"
    return transform


def compute_field(field_name: str, computation: Callable[[Dict[str, Any]], Any]) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Create transform to add computed field based on other fields.
    
    Args:
        field_name: Name of new field
        computation: Function that computes value from item
        
    Returns:
        Transform function
        
    Example:
        >>> full_name = compute_field('full_name', lambda item: f"{item['first']} {item['last']}")
    """
    def transform(item: Dict[str, Any]) -> Dict[str, Any]:
        result = copy.deepcopy(item)
        result[field_name] = computation(result)
        return result
    
    transform.__name__ = f"compute_field_{field_name}"
    return transform


def format_field(field_name: str, format_str: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Create transform to format field using format string.
    
    Args:
        field_name: Name of field to format
        format_str: Format string (e.g., "{:.2f}" for 2 decimal places)
        
    Returns:
        Transform function
    """
    def transform(item: Dict[str, Any]) -> Dict[str, Any]:
        result = copy.deepcopy(item)
        if field_name in result:
            try:
                result[field_name] = format_str.format(result[field_name])
            except (ValueError, KeyError):
                pass  # Keep original value if formatting fails
        return result
    
    transform.__name__ = f"format_field_{field_name}"
    return transform


def cast_field(field_name: str, target_type: type) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Create transform to cast field to different type.
    
    Args:
        field_name: Name of field to cast
        target_type: Target type (int, float, str, bool)
        
    Returns:
        Transform function
    """
    def transform(item: Dict[str, Any]) -> Dict[str, Any]:
        result = copy.deepcopy(item)
        if field_name in result:
            try:
                result[field_name] = target_type(result[field_name])
            except (ValueError, TypeError):
                pass  # Keep original value if cast fails
        return result
    
    transform.__name__ = f"cast_field_{field_name}_to_{target_type.__name__}"
    return transform


def extract_regex_field(source_field: str, target_field: str, pattern: str, 
                       group: int = 0) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Create transform to extract value using regex and store in new field.
    
    Args:
        source_field: Field to extract from
        target_field: Field to store result in
        pattern: Regular expression pattern
        group: Regex group to extract (0 for full match)
        
    Returns:
        Transform function
    """
    compiled_pattern = re.compile(pattern)
    
    def transform(item: Dict[str, Any]) -> Dict[str, Any]:
        result = copy.deepcopy(item)
        if source_field in result and isinstance(result[source_field], str):
            match = compiled_pattern.search(result[source_field])
            if match:
                result[target_field] = match.group(group)
        return result
    
    transform.__name__ = f"extract_regex_{source_field}_to_{target_field}"
    return transform


def split_field(source_field: str, target_fields: List[str], 
               separator: str = ' ') -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Create transform to split field into multiple fields.
    
    Args:
        source_field: Field to split
        target_fields: Names of fields to create
        separator: Character/string to split on
        
    Returns:
        Transform function
    """
    def transform(item: Dict[str, Any]) -> Dict[str, Any]:
        result = copy.deepcopy(item)
        if source_field in result and isinstance(result[source_field], str):
            parts = result[source_field].split(separator)
            for i, field_name in enumerate(target_fields):
                result[field_name] = parts[i] if i < len(parts) else ''
        return result
    
    transform.__name__ = f"split_field_{source_field}"
    return transform


def apply_function(field_name: str, func: Callable[[Any], Any]) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Create transform to apply arbitrary function to field.
    
    Args:
        field_name: Name of field to transform
        func: Function to apply to field value
        
    Returns:
        Transform function
    """
    def transform(item: Dict[str, Any]) -> Dict[str, Any]:
        result = copy.deepcopy(item)
        if field_name in result:
            try:
                result[field_name] = func(result[field_name])
            except Exception:
                pass  # Keep original value if function fails
        return result
    
    transform.__name__ = f"apply_function_{field_name}_{func.__name__}"
    return transform


def select_fields(field_names: List[str]) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Create transform to select only specified fields.
    
    Args:
        field_names: List of field names to keep
        
    Returns:
        Transform function
    """
    field_set = set(field_names)
    
    def transform(item: Dict[str, Any]) -> Dict[str, Any]:
        return {k: v for k, v in item.items() if k in field_set}
    
    transform.__name__ = f"select_fields({len(field_names)}_fields)"
    return transform


def exclude_fields(field_names: List[str]) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Create transform to exclude specified fields.
    
    Args:
        field_names: List of field names to exclude
        
    Returns:
        Transform function
    """
    field_set = set(field_names)
    
    def transform(item: Dict[str, Any]) -> Dict[str, Any]:
        return {k: v for k, v in item.items() if k not in field_set}
    
    transform.__name__ = f"exclude_fields({len(field_names)}_fields)"
    return transform


# Common transform combinations
def normalize_name(name_field: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Create transform to normalize a name field (strip, capitalize).
    
    Args:
        name_field: Name of field containing name
        
    Returns:
        Transform function
    """
    from functools import partial
    from . import pipeline
    
    # Compose multiple transforms
    normalize_pipeline = pipeline.pipe(
        strip_field(name_field),
        lower_field(name_field),
        capitalize_field(name_field)
    )
    
    normalize_pipeline.__name__ = f"normalize_name_{name_field}"
    return normalize_pipeline


def add_tax(price_field: str, tax_field: str, tax_rate: float) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Create transform to add tax calculation.
    
    Args:
        price_field: Field containing base price
        tax_field: Field to store tax amount
        tax_rate: Tax rate (e.g., 0.08 for 8%)
        
    Returns:
        Transform function
    """
    def transform(item: Dict[str, Any]) -> Dict[str, Any]:
        result = copy.deepcopy(item)
        if price_field in result and isinstance(result[price_field], (int, float)):
            tax_amount = result[price_field] * tax_rate
            result[tax_field] = round(tax_amount, 2)
        return result
    
    transform.__name__ = f"add_tax_{price_field}_to_{tax_field}"
    return transform
