"""
Pipeline builder component for FuncPipe Web UI.

Provides interactive interface for building data processing pipelines
with visual operation selection and configuration.
"""

import streamlit as st
from typing import List, Dict, Any, Optional, Callable
from ..utils.session_state import (
    get_pipeline_operations, add_pipeline_operation, remove_pipeline_operation,
    reorder_pipeline_operations, get_field_names, get_numeric_fields, get_string_fields
)

# Import funcpipe components
from funcpipe import Pipeline, filters, transforms


def render_pipeline_builder() -> List[Dict[str, Any]]:
    """
    Render the pipeline builder interface.
    
    Returns:
        List of current pipeline operations
    """
    st.subheader("🔧 Pipeline Builder")
    
    operations = get_pipeline_operations()
    
    # Display current pipeline
    if operations:
        _render_pipeline_overview(operations)
    
    # Add new operation
    _render_add_operation_form()
    
    return operations


def _render_pipeline_overview(operations: List[Dict[str, Any]]) -> None:
    """Render overview of current pipeline operations."""
    st.write("**Current Pipeline:**")
    
    for i, operation in enumerate(operations):
        with st.expander(f"Step {i+1}: {operation.get('type', 'Unknown')} - {operation.get('description', '')}", expanded=False):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.write(f"**Type:** {operation.get('type', 'Unknown')}")
                if 'config' in operation:
                    for key, value in operation['config'].items():
                        st.write(f"  - {key}: {value}")
            
            with col2:
                if st.button("↑", key=f"up_{i}", disabled=(i == 0)):
                    reorder_pipeline_operations(i, i-1)
                    st.rerun()
            
            with col3:
                if st.button("↓", key=f"down_{i}", disabled=(i == len(operations)-1)):
                    reorder_pipeline_operations(i, i+1)
                    st.rerun()
            
            with col4:
                if st.button("🗑️", key=f"remove_{i}"):
                    remove_pipeline_operation(i)
                    st.rerun()


def _render_add_operation_form() -> None:
    """Render form for adding new operations."""
    st.write("**Add New Operation:**")
    
    operation_type = st.selectbox(
        "Operation Type:",
        ["Filter", "Transform", "Sort", "Limit"],
        key="new_operation_type"
    )
    
    if operation_type == "Filter":
        _render_filter_form()
    elif operation_type == "Transform":
        _render_transform_form()
    elif operation_type == "Sort":
        _render_sort_form()
    elif operation_type == "Limit":
        _render_limit_form()


def _render_filter_form() -> None:
    """Render filter operation form."""
    field_names = get_field_names()
    
    if not field_names:
        st.warning("Please upload data first to see available fields.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        filter_type = st.selectbox(
            "Filter Type:",
            ["equals", "greater_than", "greater_than_or_equal", "less_than", 
             "less_than_or_equal", "contains", "starts_with", "ends_with", 
             "is_null", "is_not_null", "between", "in_list"],
            key="filter_type"
        )
        
        field = st.selectbox(
            "Field:",
            field_names,
            key="filter_field"
        )
    
    with col2:
        config = {"field": field, "filter_type": filter_type}
        
        if filter_type in ["equals", "greater_than", "greater_than_or_equal", "less_than", "less_than_or_equal"]:
            value = _get_filter_value_input(field, filter_type)
            config["value"] = value
            
        elif filter_type in ["contains", "starts_with", "ends_with"]:
            value = st.text_input("Value:", key="filter_value")
            config["value"] = value
            
        elif filter_type == "between":
            col_a, col_b = st.columns(2)
            with col_a:
                min_val = st.number_input("Min Value:", key="filter_min")
            with col_b:
                max_val = st.number_input("Max Value:", key="filter_max")
            config["min_value"] = min_val
            config["max_value"] = max_val
            
        elif filter_type == "in_list":
            values_text = st.text_area(
                "Values (one per line):", 
                placeholder="value1\nvalue2\nvalue3",
                key="filter_list"
            )
            config["values"] = [v.strip() for v in values_text.split('\n') if v.strip()]
    
    if st.button("Add Filter", key="add_filter"):
        operation = {
            "type": "filter",
            "filter_type": filter_type,
            "config": config,
            "description": _get_filter_description(config)
        }
        add_pipeline_operation(operation)
        st.rerun()


def _render_transform_form() -> None:
    """Render transform operation form."""
    field_names = get_field_names()
    
    if not field_names:
        st.warning("Please upload data first to see available fields.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        transform_type = st.selectbox(
            "Transform Type:",
            ["capitalize_field", "upper_field", "lower_field", "strip_field",
             "add_field", "remove_field", "rename_field", "multiply_field",
             "add_to_field", "round_field", "compute_field"],
            key="transform_type"
        )
    
    with col2:
        config = {"transform_type": transform_type}
        
        if transform_type in ["capitalize_field", "upper_field", "lower_field", "strip_field", "remove_field"]:
            field = st.selectbox("Field:", field_names, key="transform_field")
            config["field"] = field
            
        elif transform_type in ["add_field"]:
            field_name = st.text_input("New Field Name:", key="new_field_name")
            value = st.text_input("Value:", key="new_field_value")
            config["field_name"] = field_name
            config["value"] = value
            
        elif transform_type == "rename_field":
            old_field = st.selectbox("Old Field:", field_names, key="old_field")
            new_field = st.text_input("New Field Name:", key="new_field")
            config["old_field"] = old_field
            config["new_field"] = new_field
            
        elif transform_type in ["multiply_field", "add_to_field", "round_field"]:
            field = st.selectbox("Field:", field_names, key="transform_field")
            if transform_type == "round_field":
                decimals = st.number_input("Decimal Places:", min_value=0, max_value=10, value=0, key="decimals")
                config["decimals"] = decimals
            else:
                value = st.number_input("Value:", key="transform_value")
                config["value"] = value
            config["field"] = field
            
        elif transform_type == "compute_field":
            field_name = st.text_input("New Field Name:", key="compute_field_name")
            expression = st.text_area(
                "Expression (use 'item' to refer to current record):",
                placeholder="item['field1'] + item['field2']",
                key="compute_expression"
            )
            config["field_name"] = field_name
            config["expression"] = expression
    
    if st.button("Add Transform", key="add_transform"):
        operation = {
            "type": "transform",
            "transform_type": transform_type,
            "config": config,
            "description": _get_transform_description(config)
        }
        add_pipeline_operation(operation)
        st.rerun()


def _render_sort_form() -> None:
    """Render sort operation form."""
    field_names = get_field_names()
    
    if not field_names:
        st.warning("Please upload data first to see available fields.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        field = st.selectbox("Sort Field:", field_names, key="sort_field")
    
    with col2:
        reverse = st.checkbox("Descending Order", key="sort_reverse")
    
    if st.button("Add Sort", key="add_sort"):
        operation = {
            "type": "sort",
            "config": {
                "field": field,
                "reverse": reverse
            },
            "description": f"Sort by {field} ({'desc' if reverse else 'asc'})"
        }
        add_pipeline_operation(operation)
        st.rerun()


def _render_limit_form() -> None:
    """Render limit operation form."""
    operation_subtype = st.selectbox(
        "Limit Type:",
        ["take", "skip"],
        key="limit_type"
    )
    
    value = st.number_input(
        "Number of records:",
        min_value=1,
        key="limit_value"
    )
    
    if st.button("Add Limit", key="add_limit"):
        operation = {
            "type": "limit",
            "config": {
                "operation": operation_subtype,
                "value": value
            },
            "description": f"{operation_subtype.title()} first {value} records"
        }
        add_pipeline_operation(operation)
        st.rerun()


def _get_filter_value_input(field: str, filter_type: str) -> Any:
    """Get appropriate input widget for filter value based on field type."""
    numeric_fields = get_numeric_fields()
    
    if field in numeric_fields:
        return st.number_input("Value:", key="filter_value")
    else:
        return st.text_input("Value:", key="filter_value")


def _get_filter_description(config: Dict[str, Any]) -> str:
    """Generate human-readable description for filter operation."""
    field = config.get("field", "")
    filter_type = config.get("filter_type", "")
    
    if filter_type == "equals":
        value = config.get("value", "")
        return f"Keep records where {field} = {value}"
    elif filter_type == "greater_than":
        value = config.get("value", "")
        return f"Keep records where {field} > {value}"
    elif filter_type == "greater_than_or_equal":
        value = config.get("value", "")
        return f"Keep records where {field} >= {value}"
    elif filter_type == "less_than":
        value = config.get("value", "")
        return f"Keep records where {field} < {value}"
    elif filter_type == "less_than_or_equal":
        value = config.get("value", "")
        return f"Keep records where {field} <= {value}"
    elif filter_type == "contains":
        value = config.get("value", "")
        return f"Keep records where {field} contains '{value}'"
    elif filter_type == "starts_with":
        value = config.get("value", "")
        return f"Keep records where {field} starts with '{value}'"
    elif filter_type == "ends_with":
        value = config.get("value", "")
        return f"Keep records where {field} ends with '{value}'"
    elif filter_type == "is_null":
        return f"Keep records where {field} is null"
    elif filter_type == "is_not_null":
        return f"Keep records where {field} is not null"
    elif filter_type == "between":
        min_val = config.get("min_value", "")
        max_val = config.get("max_value", "")
        return f"Keep records where {field} is between {min_val} and {max_val}"
    elif filter_type == "in_list":
        values = config.get("values", [])
        return f"Keep records where {field} is in [{', '.join(values)}]"
    else:
        return f"Filter {field} with {filter_type}"


def _get_transform_description(config: Dict[str, Any]) -> str:
    """Generate human-readable description for transform operation."""
    transform_type = config.get("transform_type", "")
    
    if transform_type == "capitalize_field":
        field = config.get("field", "")
        return f"Capitalize {field}"
    elif transform_type == "upper_field":
        field = config.get("field", "")
        return f"Convert {field} to uppercase"
    elif transform_type == "lower_field":
        field = config.get("field", "")
        return f"Convert {field} to lowercase"
    elif transform_type == "strip_field":
        field = config.get("field", "")
        return f"Strip whitespace from {field}"
    elif transform_type == "add_field":
        field_name = config.get("field_name", "")
        value = config.get("value", "")
        return f"Add field '{field_name}' with value '{value}'"
    elif transform_type == "remove_field":
        field = config.get("field", "")
        return f"Remove field {field}"
    elif transform_type == "rename_field":
        old_field = config.get("old_field", "")
        new_field = config.get("new_field", "")
        return f"Rename {old_field} to {new_field}"
    elif transform_type == "multiply_field":
        field = config.get("field", "")
        value = config.get("value", "")
        return f"Multiply {field} by {value}"
    elif transform_type == "add_to_field":
        field = config.get("field", "")
        value = config.get("value", "")
        return f"Add {value} to {field}"
    elif transform_type == "round_field":
        field = config.get("field", "")
        decimals = config.get("decimals", 0)
        return f"Round {field} to {decimals} decimal places"
    elif transform_type == "compute_field":
        field_name = config.get("field_name", "")
        return f"Compute new field '{field_name}'"
    else:
        return f"Transform: {transform_type}"


def execute_pipeline(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Execute the current pipeline on the given data.
    
    Args:
        data: Input data to process
        
    Returns:
        Processed data
    """
    if not data:
        return []
    
    pipeline = Pipeline()
    operations = get_pipeline_operations()
    
    for operation in operations:
        if operation["type"] == "filter":
            filter_func = _create_filter_function(operation["config"])
            pipeline = pipeline.filter(filter_func)
            
        elif operation["type"] == "transform":
            transform_func = _create_transform_function(operation["config"])
            pipeline = pipeline.map(transform_func)
            
        elif operation["type"] == "sort":
            config = operation["config"]
            key_func = lambda item: item.get(config["field"])
            pipeline = pipeline.sort(key_func, config["reverse"])
            
        elif operation["type"] == "limit":
            config = operation["config"]
            if config["operation"] == "take":
                pipeline = pipeline.take(config["value"])
            elif config["operation"] == "skip":
                pipeline = pipeline.skip(config["value"])
    
    return pipeline.run(data)


def _create_filter_function(config: Dict[str, Any]) -> Callable:
    """Create a filter function from configuration."""
    filter_type = config["filter_type"]
    field = config["field"]
    
    if filter_type == "equals":
        return filters.equals(field, config["value"])
    elif filter_type == "greater_than":
        return filters.greater_than(field, config["value"])
    elif filter_type == "greater_than_or_equal":
        return filters.greater_than_or_equal(field, config["value"])
    elif filter_type == "less_than":
        return filters.less_than(field, config["value"])
    elif filter_type == "less_than_or_equal":
        return filters.less_than_or_equal(field, config["value"])
    elif filter_type == "contains":
        return filters.contains(field, config["value"])
    elif filter_type == "starts_with":
        return filters.starts_with(field, config["value"])
    elif filter_type == "ends_with":
        return filters.ends_with(field, config["value"])
    elif filter_type == "is_null":
        return filters.is_null(field)
    elif filter_type == "is_not_null":
        return filters.is_not_null(field)
    elif filter_type == "between":
        return filters.between(field, config["min_value"], config["max_value"])
    elif filter_type == "in_list":
        return filters.in_list(field, config["values"])
    else:
        raise ValueError(f"Unknown filter type: {filter_type}")


def _create_transform_function(config: Dict[str, Any]) -> Callable:
    """Create a transform function from configuration."""
    transform_type = config["transform_type"]
    
    if transform_type == "capitalize_field":
        return transforms.capitalize_field(config["field"])
    elif transform_type == "upper_field":
        return transforms.upper_field(config["field"])
    elif transform_type == "lower_field":
        return transforms.lower_field(config["field"])
    elif transform_type == "strip_field":
        return transforms.strip_field(config["field"])
    elif transform_type == "add_field":
        return transforms.add_field(config["field_name"], config["value"])
    elif transform_type == "remove_field":
        return transforms.remove_field(config["field"])
    elif transform_type == "rename_field":
        return transforms.rename_field(config["old_field"], config["new_field"])
    elif transform_type == "multiply_field":
        return transforms.multiply_field(config["field"], config["value"])
    elif transform_type == "add_to_field":
        return transforms.add_to_field(config["field"], config["value"])
    elif transform_type == "round_field":
        return transforms.round_field(config["field"], config["decimals"])
    elif transform_type == "compute_field":
        # Create lambda function from expression
        expression = config["expression"]
        func = eval(f"lambda item: {expression}")
        return transforms.compute_field(config["field_name"], func)
    else:
        raise ValueError(f"Unknown transform type: {transform_type}")
