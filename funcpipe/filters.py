"""
Functional filters for data processing pipelines.

All filters are curried functions that return predicates.
This allows for easy composition and reuse.
"""

from typing import Any, Callable, Dict, List, Union
from functools import partial
import re
import operator


def equals(field: str, value: Any) -> Callable[[Dict[str, Any]], bool]:
    """
    Create filter for exact equality.
    
    Args:
        field: Field name to check
        value: Value to compare against
        
    Returns:
        Predicate function
        
    Example:
        >>> filter_adults = equals('age', 18)
        >>> filter_adults({'name': 'John', 'age': 18})
        True
    """
    def predicate(item: Dict[str, Any]) -> bool:
        return item.get(field) == value
    
    predicate.__name__ = f"equals_{field}_{value}"
    return predicate


def greater_than(field: str, value: Union[int, float]) -> Callable[[Dict[str, Any]], bool]:
    """
    Create filter for greater than comparison.
    
    Args:
        field: Field name to check
        value: Minimum value (exclusive)
        
    Returns:
        Predicate function
    """
    def predicate(item: Dict[str, Any]) -> bool:
        field_value = item.get(field)
        return field_value is not None and field_value > value
    
    predicate.__name__ = f"greater_than_{field}_{value}"
    return predicate


def greater_than_or_equal(field: str, value: Union[int, float]) -> Callable[[Dict[str, Any]], bool]:
    """
    Create filter for greater than or equal comparison.
    
    Args:
        field: Field name to check
        value: Minimum value (inclusive)
        
    Returns:
        Predicate function
    """
    def predicate(item: Dict[str, Any]) -> bool:
        field_value = item.get(field)
        return field_value is not None and field_value >= value
    
    predicate.__name__ = f"greater_than_or_equal_{field}_{value}"
    return predicate


def less_than(field: str, value: Union[int, float]) -> Callable[[Dict[str, Any]], bool]:
    """Create filter for less than comparison."""
    def predicate(item: Dict[str, Any]) -> bool:
        field_value = item.get(field)
        return field_value is not None and field_value < value
    
    predicate.__name__ = f"less_than_{field}_{value}"
    return predicate


def less_than_or_equal(field: str, value: Union[int, float]) -> Callable[[Dict[str, Any]], bool]:
    """Create filter for less than or equal comparison."""
    def predicate(item: Dict[str, Any]) -> bool:
        field_value = item.get(field)
        return field_value is not None and field_value <= value
    
    predicate.__name__ = f"less_than_or_equal_{field}_{value}"
    return predicate


def contains(field: str, substring: str, case_sensitive: bool = True) -> Callable[[Dict[str, Any]], bool]:
    """
    Create filter for string contains check.
    
    Args:
        field: Field name to check
        substring: Substring to search for
        case_sensitive: Whether search is case sensitive
        
    Returns:
        Predicate function
    """
    def predicate(item: Dict[str, Any]) -> bool:
        field_value = item.get(field)
        if not isinstance(field_value, str):
            return False
        
        if not case_sensitive:
            return substring.lower() in field_value.lower()
        return substring in field_value
    
    predicate.__name__ = f"contains_{field}_{substring}"
    return predicate


def starts_with(field: str, prefix: str, case_sensitive: bool = True) -> Callable[[Dict[str, Any]], bool]:
    """Create filter for string starts with check."""
    def predicate(item: Dict[str, Any]) -> bool:
        field_value = item.get(field)
        if not isinstance(field_value, str):
            return False
        
        if not case_sensitive:
            return field_value.lower().startswith(prefix.lower())
        return field_value.startswith(prefix)
    
    predicate.__name__ = f"starts_with_{field}_{prefix}"
    return predicate


def ends_with(field: str, suffix: str, case_sensitive: bool = True) -> Callable[[Dict[str, Any]], bool]:
    """Create filter for string ends with check."""
    def predicate(item: Dict[str, Any]) -> bool:
        field_value = item.get(field)
        if not isinstance(field_value, str):
            return False
        
        if not case_sensitive:
            return field_value.lower().endswith(suffix.lower())
        return field_value.endswith(suffix)
    
    predicate.__name__ = f"ends_with_{field}_{suffix}"
    return predicate


def matches_regex(field: str, pattern: str, flags: int = 0) -> Callable[[Dict[str, Any]], bool]:
    """
    Create filter for regex pattern matching.
    
    Args:
        field: Field name to check
        pattern: Regular expression pattern
        flags: Regex flags (e.g., re.IGNORECASE)
        
    Returns:
        Predicate function
    """
    compiled_pattern = re.compile(pattern, flags)
    
    def predicate(item: Dict[str, Any]) -> bool:
        field_value = item.get(field)
        if not isinstance(field_value, str):
            return False
        return bool(compiled_pattern.search(field_value))
    
    predicate.__name__ = f"matches_regex_{field}_{pattern}"
    return predicate


def is_null(field: str) -> Callable[[Dict[str, Any]], bool]:
    """Create filter for null/None values."""
    def predicate(item: Dict[str, Any]) -> bool:
        return item.get(field) is None
    
    predicate.__name__ = f"is_null_{field}"
    return predicate


def is_not_null(field: str) -> Callable[[Dict[str, Any]], bool]:
    """Create filter for non-null values."""
    def predicate(item: Dict[str, Any]) -> bool:
        return item.get(field) is not None
    
    predicate.__name__ = f"is_not_null_{field}"
    return predicate


def in_list(field: str, values: List[Any]) -> Callable[[Dict[str, Any]], bool]:
    """
    Create filter for membership in list.
    
    Args:
        field: Field name to check
        values: List of acceptable values
        
    Returns:
        Predicate function
    """
    value_set = set(values)  # Convert to set for O(1) lookups
    
    def predicate(item: Dict[str, Any]) -> bool:
        return item.get(field) in value_set
    
    predicate.__name__ = f"in_list_{field}"
    return predicate


def not_in_list(field: str, values: List[Any]) -> Callable[[Dict[str, Any]], bool]:
    """Create filter for exclusion from list."""
    value_set = set(values)
    
    def predicate(item: Dict[str, Any]) -> bool:
        return item.get(field) not in value_set
    
    predicate.__name__ = f"not_in_list_{field}"
    return predicate


def between(field: str, min_val: Union[int, float], max_val: Union[int, float], 
           inclusive: bool = True) -> Callable[[Dict[str, Any]], bool]:
    """
    Create filter for range checking.
    
    Args:
        field: Field name to check
        min_val: Minimum value
        max_val: Maximum value
        inclusive: Whether range is inclusive
        
    Returns:
        Predicate function
    """
    def predicate(item: Dict[str, Any]) -> bool:
        field_value = item.get(field)
        if field_value is None:
            return False
        
        if inclusive:
            return min_val <= field_value <= max_val
        return min_val < field_value < max_val
    
    predicate.__name__ = f"between_{field}_{min_val}_{max_val}"
    return predicate


def and_filter(*predicates: Callable[[Dict[str, Any]], bool]) -> Callable[[Dict[str, Any]], bool]:
    """
    Combine filters with AND logic.
    
    Args:
        *predicates: Filter functions to combine
        
    Returns:
        Combined predicate function
    """
    def predicate(item: Dict[str, Any]) -> bool:
        return all(pred(item) for pred in predicates)
    
    predicate.__name__ = f"and_filter({len(predicates)}_conditions)"
    return predicate


def or_filter(*predicates: Callable[[Dict[str, Any]], bool]) -> Callable[[Dict[str, Any]], bool]:
    """
    Combine filters with OR logic.
    
    Args:
        *predicates: Filter functions to combine
        
    Returns:
        Combined predicate function
    """
    def predicate(item: Dict[str, Any]) -> bool:
        return any(pred(item) for pred in predicates)
    
    predicate.__name__ = f"or_filter({len(predicates)}_conditions)"
    return predicate


def not_filter(predicate: Callable[[Dict[str, Any]], bool]) -> Callable[[Dict[str, Any]], bool]:
    """
    Negate a filter.
    
    Args:
        predicate: Filter function to negate
        
    Returns:
        Negated predicate function
    """
    def negated_predicate(item: Dict[str, Any]) -> bool:
        return not predicate(item)
    
    negated_predicate.__name__ = f"not_{predicate.__name__}"
    return negated_predicate
