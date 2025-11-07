"""
Session state management utilities for FuncPipe Web UI.

Provides helper functions for managing Streamlit session state
and persisting pipeline configurations.
"""

import streamlit as st
from typing import Dict, List, Any, Optional
import json


def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    if 'uploaded_data' not in st.session_state:
        st.session_state.uploaded_data = None
    
    if 'pipeline_operations' not in st.session_state:
        st.session_state.pipeline_operations = []
    
    if 'processed_data' not in st.session_state:
        st.session_state.processed_data = None
    
    if 'pipeline_results' not in st.session_state:
        st.session_state.pipeline_results = {}
    
    if 'current_stage' not in st.session_state:
        st.session_state.current_stage = 0


def get_pipeline_operations() -> List[Dict[str, Any]]:
    """Get current pipeline operations from session state."""
    return st.session_state.get('pipeline_operations', [])


def add_pipeline_operation(operation: Dict[str, Any]) -> None:
    """Add a new operation to the pipeline."""
    operations = get_pipeline_operations()
    operations.append(operation)
    st.session_state.pipeline_operations = operations


def remove_pipeline_operation(index: int) -> None:
    """Remove an operation from the pipeline by index."""
    operations = get_pipeline_operations()
    if 0 <= index < len(operations):
        operations.pop(index)
        st.session_state.pipeline_operations = operations


def reorder_pipeline_operations(from_index: int, to_index: int) -> None:
    """Move an operation from one position to another."""
    operations = get_pipeline_operations()
    if 0 <= from_index < len(operations) and 0 <= to_index < len(operations):
        operation = operations.pop(from_index)
        operations.insert(to_index, operation)
        st.session_state.pipeline_operations = operations


def clear_pipeline() -> None:
    """Clear all pipeline operations and results."""
    st.session_state.pipeline_operations = []
    st.session_state.processed_data = None
    st.session_state.pipeline_results = {}
    st.session_state.current_stage = 0


def save_pipeline_config(filename: str) -> None:
    """Save current pipeline configuration to a JSON file."""
    config = {
        'operations': get_pipeline_operations(),
        'metadata': {
            'created': str(st.session_state.get('pipeline_created', 'unknown')),
            'version': '1.0'
        }
    }
    
    with open(filename, 'w') as f:
        json.dump(config, f, indent=2)


def load_pipeline_config(config: Dict[str, Any]) -> None:
    """Load pipeline configuration from JSON data."""
    if 'operations' in config:
        st.session_state.pipeline_operations = config['operations']
        clear_pipeline_results()


def clear_pipeline_results() -> None:
    """Clear pipeline execution results."""
    st.session_state.processed_data = None
    st.session_state.pipeline_results = {}
    st.session_state.current_stage = 0


def set_pipeline_results(stage: int, data: List[Dict[str, Any]]) -> None:
    """Store pipeline results for a specific stage."""
    st.session_state.pipeline_results[str(stage)] = data
    st.session_state.processed_data = data
    st.session_state.current_stage = stage


def get_pipeline_results(stage: int) -> Optional[List[Dict[str, Any]]]:
    """Get pipeline results for a specific stage."""
    return st.session_state.pipeline_results.get(str(stage))


def get_current_data() -> Optional[List[Dict[str, Any]]]:
    """Get the most recent processed data."""
    return st.session_state.get('processed_data')


def get_uploaded_data() -> Optional[List[Dict[str, Any]]]:
    """Get uploaded data."""
    return st.session_state.get('uploaded_data')


def set_uploaded_data(data: List[Dict[str, Any]]) -> None:
    """Set uploaded data and clear pipeline."""
    st.session_state.uploaded_data = data
    clear_pipeline()


def get_field_names() -> List[str]:
    """Get field names from uploaded data."""
    data = get_uploaded_data()
    if data and len(data) > 0:
        return list(data[0].keys())
    return []


def get_field_types() -> Dict[str, str]:
    """Get field types from uploaded data."""
    data = get_uploaded_data()
    if not data or len(data) == 0:
        return {}
    
    field_types = {}
    for item in data:
        for key, value in item.items():
            if key not in field_types:
                field_types[key] = type(value).__name__
    return field_types


def get_numeric_fields() -> List[str]:
    """Get list of numeric field names."""
    field_types = get_field_types()
    return [field for field, type_name in field_types.items() 
            if type_name in ['int', 'float']]


def get_string_fields() -> List[str]:
    """Get list of string field names."""
    field_types = get_field_types()
    return [field for field, type_name in field_types.items() 
            if type_name == 'str']
