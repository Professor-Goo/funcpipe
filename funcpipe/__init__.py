"""
FuncPipe - Functional Data Processing Pipeline

A library for processing data through composable functional transformations.
Built on functional programming principles with immutable data structures.
"""

from .pipeline import Pipeline
from . import filters, transforms, readers, writers

__version__ = "0.1.0"
__all__ = ["Pipeline", "filters", "transforms", "readers", "writers"]
