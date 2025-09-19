"""
Core Pipeline implementation using functional composition.
"""

from typing import List, Dict, Any, Callable, Optional
from functools import reduce
import copy


class Pipeline:
    """
    Immutable data processing pipeline using functional composition.
    
    Each operation returns a new Pipeline instance, maintaining immutability.
    Supports method chaining for readable data transformation workflows.
    """
    
    def __init__(self, operations: Optional[List[Callable]] = None):
        """Initialize pipeline with optional list of operations."""
        self._operations = operations or []
    
    def _add_operation(self, operation: Callable) -> 'Pipeline':
        """Create new pipeline with additional operation (immutable)."""
        return Pipeline(self._operations + [operation])
    
    def filter(self, predicate: Callable[[Dict[str, Any]], bool]) -> 'Pipeline':
        """
        Add filter operation to pipeline.
        
        Args:
            predicate: Function that returns True for items to keep
            
        Returns:
            New Pipeline with filter operation added
        """
        def filter_op(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            return [item for item in data if predicate(item)]
        
        return self._add_operation(filter_op)
    
    def map(self, transform: Callable[[Dict[str, Any]], Dict[str, Any]]) -> 'Pipeline':
        """
        Add map operation to pipeline.
        
        Args:
            transform: Function to transform each item
            
        Returns:
            New Pipeline with map operation added
        """
        def map_op(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            return [transform(copy.deepcopy(item)) for item in data]
        
        return self._add_operation(map_op)
    
    def reduce(self, reducer: Callable, initial_value: Any = None) -> 'Pipeline':
        """
        Add reduce operation to pipeline.
        
        Args:
            reducer: Function to reduce data to single value
            initial_value: Starting value for reduction
            
        Returns:
            New Pipeline with reduce operation added
        """
        def reduce_op(data: List[Dict[str, Any]]) -> Any:
            if initial_value is not None:
                return reduce(reducer, data, initial_value)
            return reduce(reducer, data)
        
        return self._add_operation(reduce_op)
    
    def sort(self, key_func: Callable[[Dict[str, Any]], Any], reverse: bool = False) -> 'Pipeline':
        """
        Add sort operation to pipeline.
        
        Args:
            key_func: Function to extract sort key from each item
            reverse: Sort in descending order if True
            
        Returns:
            New Pipeline with sort operation added
        """
        def sort_op(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            return sorted(data, key=key_func, reverse=reverse)
        
        return self._add_operation(sort_op)
    
    def take(self, n: int) -> 'Pipeline':
        """
        Add take operation to get first n items.
        
        Args:
            n: Number of items to take
            
        Returns:
            New Pipeline with take operation added
        """
        def take_op(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            return data[:n]
        
        return self._add_operation(take_op)
    
    def skip(self, n: int) -> 'Pipeline':
        """
        Add skip operation to skip first n items.
        
        Args:
            n: Number of items to skip
            
        Returns:
            New Pipeline with skip operation added
        """
        def skip_op(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            return data[n:]
        
        return self._add_operation(skip_op)
    
    def run(self, data: List[Dict[str, Any]]) -> Any:
        """
        Execute the pipeline on input data.
        
        Args:
            data: Input data to process
            
        Returns:
            Transformed data after applying all operations
        """
        return reduce(lambda acc, op: op(acc), self._operations, data)
    
    def __len__(self) -> int:
        """Return number of operations in pipeline."""
        return len(self._operations)
    
    def __repr__(self) -> str:
        """String representation of pipeline."""
        op_names = [op.__name__ for op in self._operations]
        return f"Pipeline({len(self._operations)} operations: {' → '.join(op_names)})"


def compose(*functions: Callable) -> Callable:
    """
    Compose multiple functions into a single function.
    Functions are applied right-to-left (mathematical composition).
    
    Args:
        *functions: Functions to compose
        
    Returns:
        Composed function
        
    Example:
        >>> add_one = lambda x: x + 1
        >>> multiply_two = lambda x: x * 2
        >>> composed = compose(add_one, multiply_two)
        >>> composed(5)  # add_one(multiply_two(5)) = 11
        11
    """
    return reduce(lambda f, g: lambda x: f(g(x)), functions, lambda x: x)


def pipe(*functions: Callable) -> Callable:
    """
    Pipe functions left-to-right (Unix pipe style).
    More intuitive for data processing workflows.
    
    Args:
        *functions: Functions to pipe
        
    Returns:
        Piped function
        
    Example:
        >>> add_one = lambda x: x + 1
        >>> multiply_two = lambda x: x * 2
        >>> piped = pipe(multiply_two, add_one)
        >>> piped(5)  # add_one(multiply_two(5)) = 11
        11
    """
    return reduce(lambda f, g: lambda x: g(f(x)), functions, lambda x: x)
