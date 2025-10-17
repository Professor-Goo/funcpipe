"""
Export handler component for FuncPipe Web UI.

Provides functionality for downloading results and generating Python code
from the current pipeline configuration.
"""

import streamlit as st
import json
import io
from typing import List, Dict, Any, Optional
from ..utils.session_state import get_current_data, get_pipeline_operations, get_uploaded_data


def render_export_handler() -> None:
    """Render the export handler interface."""
    st.subheader("💾 Export Results")
    
    current_data = get_current_data()
    
    if not current_data:
        st.info("Run pipeline to export results")
        return
    
    # Create tabs for different export options
    tab1, tab2, tab3 = st.tabs(["📁 Download Data", "🐍 Generate Python Code", "💾 Save Pipeline"])
    
    with tab1:
        _render_download_tab(current_data)
    
    with tab2:
        _render_python_code_tab()
    
    with tab3:
        _render_save_pipeline_tab()


def _render_download_tab(data: List[Dict[str, Any]]) -> None:
    """Render data download options."""
    st.write("**Download processed data in various formats:**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Download JSON", key="download_json"):
            json_data = _convert_to_json(data)
            st.download_button(
                label="Download JSON file",
                data=json_data,
                file_name="processed_data.json",
                mime="application/json",
                key="download_json_file"
            )
    
    with col2:
        if st.button("📊 Download CSV", key="download_csv"):
            csv_data = _convert_to_csv(data)
            st.download_button(
                label="Download CSV file",
                data=csv_data,
                file_name="processed_data.csv",
                mime="text/csv",
                key="download_csv_file"
            )
    
    with col3:
        if st.button("📋 Download TSV", key="download_tsv"):
            tsv_data = _convert_to_tsv(data)
            st.download_button(
                label="Download TSV file",
                data=tsv_data,
                file_name="processed_data.tsv",
                mime="text/tab-separated-values",
                key="download_tsv_file"
            )
    
    # Show data summary
    st.write(f"**Export Summary:** {len(data)} records, {len(data[0].keys()) if data else 0} fields")


def _render_python_code_tab() -> None:
    """Render Python code generation."""
    st.write("**Generate Python code for your pipeline:**")
    
    operations = get_pipeline_operations()
    uploaded_data = get_uploaded_data()
    
    if not operations:
        st.info("Add operations to generate Python code")
        return
    
    # Generate code
    python_code = _generate_python_code(operations, uploaded_data)
    
    # Display code
    st.code(python_code, language="python")
    
    # Download button
    st.download_button(
        label="📄 Download Python Script",
        data=python_code,
        file_name="funcpipe_pipeline.py",
        mime="text/x-python",
        key="download_python"
    )
    
    # Copy to clipboard button
    if st.button("📋 Copy to Clipboard"):
        st.code("Code copied! Use Ctrl+V to paste.", language="bash")


def _render_save_pipeline_tab() -> None:
    """Render pipeline save/load functionality."""
    st.write("**Save and load pipeline configurations:**")
    
    operations = get_pipeline_operations()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Save Current Pipeline:**")
        if operations:
            pipeline_config = {
                "operations": operations,
                "metadata": {
                    "name": "My Pipeline",
                    "description": "Custom pipeline configuration",
                    "version": "1.0"
                }
            }
            
            config_json = json.dumps(pipeline_config, indent=2)
            
            st.download_button(
                label="💾 Save Pipeline Config",
                data=config_json,
                file_name="pipeline_config.json",
                mime="application/json",
                key="download_pipeline_config"
            )
        else:
            st.info("Add operations to save pipeline")
    
    with col2:
        st.write("**Load Pipeline Configuration:**")
        uploaded_config = st.file_uploader(
            "Upload pipeline config file:",
            type=['json'],
            key="upload_pipeline_config"
        )
        
        if uploaded_config is not None:
            try:
                config_data = json.loads(uploaded_config.read())
                if st.button("🔄 Load Pipeline", key="load_pipeline"):
                    _load_pipeline_config(config_data)
                    st.success("Pipeline loaded successfully!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error loading pipeline: {str(e)}")
    
    # Load example pipelines
    st.write("**Load Example Pipeline:**")
    example_pipelines = _load_example_pipelines()
    
    if example_pipelines:
        selected_example = st.selectbox(
            "Choose an example:",
            ["None"] + [p["name"] for p in example_pipelines],
            key="select_example_pipeline"
        )
        
        if selected_example != "None":
            selected_pipeline = next(p for p in example_pipelines if p["name"] == selected_example)
            
            st.write(f"**Description:** {selected_pipeline['description']}")
            
            if st.button("🔄 Load Example", key="load_example"):
                _load_pipeline_config(selected_pipeline)
                st.success(f"Loaded example: {selected_example}")
                st.rerun()


def _convert_to_json(data: List[Dict[str, Any]]) -> str:
    """Convert data to JSON string."""
    return json.dumps(data, indent=2, ensure_ascii=False)


def _convert_to_csv(data: List[Dict[str, Any]]) -> str:
    """Convert data to CSV string."""
    if not data:
        return ""
    
    import csv
    import io
    
    # Get all field names
    fieldnames = set()
    for item in data:
        fieldnames.update(item.keys())
    fieldnames = sorted(list(fieldnames))
    
    # Create CSV string
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data)
    
    return output.getvalue()


def _convert_to_tsv(data: List[Dict[str, Any]]) -> str:
    """Convert data to TSV string."""
    if not data:
        return ""
    
    import csv
    import io
    
    # Get all field names
    fieldnames = set()
    for item in data:
        fieldnames.update(item.keys())
    fieldnames = sorted(list(fieldnames))
    
    # Create TSV string
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter='\t')
    writer.writeheader()
    writer.writerows(data)
    
    return output.getvalue()


def _generate_python_code(operations: List[Dict[str, Any]], uploaded_data: Optional[List[Dict[str, Any]]]) -> str:
    """Generate Python code from pipeline operations."""
    lines = [
        '#!/usr/bin/env python3',
        '"""',
        'Generated FuncPipe Pipeline',
        'This script was generated by FuncPipe Web UI',
        '"""',
        '',
        'from funcpipe import Pipeline, filters, transforms, readers, writers',
        '',
    ]
    
    # Add data loading if we have uploaded data
    if uploaded_data:
        lines.extend([
            '# Sample data (replace with your data source)',
            'data = ['
        ])
        
        # Add first few records as example
        for i, item in enumerate(uploaded_data[:3]):
            lines.append(f'    {repr(item)},')
        
        if len(uploaded_data) > 3:
            lines.append(f'    # ... and {len(uploaded_data) - 3} more records')
        
        lines.extend([
            ']',
            '',
            '# Or load from file:',
            '# data = readers.read_csv("your_file.csv")',
            '# data = readers.read_json("your_file.json")',
            '',
        ])
    else:
        lines.extend([
            '# Load your data',
            '# data = readers.read_csv("your_file.csv")',
            '# data = readers.read_json("your_file.json")',
            '',
        ])
    
    # Build pipeline
    lines.append('# Build pipeline')
    lines.append('pipeline = Pipeline()')
    
    for operation in operations:
        if operation["type"] == "filter":
            lines.append(_generate_filter_code(operation))
        elif operation["type"] == "transform":
            lines.append(_generate_transform_code(operation))
        elif operation["type"] == "sort":
            lines.append(_generate_sort_code(operation))
        elif operation["type"] == "limit":
            lines.append(_generate_limit_code(operation))
    
    lines.extend([
        '',
        '# Execute pipeline',
        'result = pipeline.run(data)',
        '',
        '# Display results',
        'print(f"Processed {len(result)} records")',
        'writers.print_sample(result, n=5)',
        '',
        '# Save results',
        '# writers.write_json(result, "output.json")',
        '# writers.write_csv(result, "output.csv")',
        '',
    ])
    
    return '\n'.join(lines)


def _generate_filter_code(operation: Dict[str, Any]) -> str:
    """Generate Python code for a filter operation."""
    config = operation["config"]
    filter_type = config["filter_type"]
    field = config["field"]
    
    if filter_type == "equals":
        return f'pipeline = pipeline.filter(filters.equals("{field}", {repr(config["value"])}))'
    elif filter_type == "greater_than":
        return f'pipeline = pipeline.filter(filters.greater_than("{field}", {config["value"]}))'
    elif filter_type == "greater_than_or_equal":
        return f'pipeline = pipeline.filter(filters.greater_than_or_equal("{field}", {config["value"]}))'
    elif filter_type == "less_than":
        return f'pipeline = pipeline.filter(filters.less_than("{field}", {config["value"]}))'
    elif filter_type == "less_than_or_equal":
        return f'pipeline = pipeline.filter(filters.less_than_or_equal("{field}", {config["value"]}))'
    elif filter_type == "contains":
        return f'pipeline = pipeline.filter(filters.contains("{field}", "{config["value"]}"))'
    elif filter_type == "starts_with":
        return f'pipeline = pipeline.filter(filters.starts_with("{field}", "{config["value"]}"))'
    elif filter_type == "ends_with":
        return f'pipeline = pipeline.filter(filters.ends_with("{field}", "{config["value"]}"))'
    elif filter_type == "is_null":
        return f'pipeline = pipeline.filter(filters.is_null("{field}"))'
    elif filter_type == "is_not_null":
        return f'pipeline = pipeline.filter(filters.is_not_null("{field}"))'
    elif filter_type == "between":
        return f'pipeline = pipeline.filter(filters.between("{field}", {config["min_value"]}, {config["max_value"]}))'
    elif filter_type == "in_list":
        values_repr = repr(config["values"])
        return f'pipeline = pipeline.filter(filters.in_list("{field}", {values_repr}))'
    else:
        return f'# Filter: {filter_type} on {field}'


def _generate_transform_code(operation: Dict[str, Any]) -> str:
    """Generate Python code for a transform operation."""
    config = operation["config"]
    transform_type = config["transform_type"]
    
    if transform_type == "capitalize_field":
        return f'pipeline = pipeline.map(transforms.capitalize_field("{config["field"]}"))'
    elif transform_type == "upper_field":
        return f'pipeline = pipeline.map(transforms.upper_field("{config["field"]}"))'
    elif transform_type == "lower_field":
        return f'pipeline = pipeline.map(transforms.lower_field("{config["field"]}"))'
    elif transform_type == "strip_field":
        return f'pipeline = pipeline.map(transforms.strip_field("{config["field"]}"))'
    elif transform_type == "add_field":
        return f'pipeline = pipeline.map(transforms.add_field("{config["field_name"]}", {repr(config["value"])}))'
    elif transform_type == "remove_field":
        return f'pipeline = pipeline.map(transforms.remove_field("{config["field"]}"))'
    elif transform_type == "rename_field":
        return f'pipeline = pipeline.map(transforms.rename_field("{config["old_field"]}", "{config["new_field"]}"))'
    elif transform_type == "multiply_field":
        return f'pipeline = pipeline.map(transforms.multiply_field("{config["field"]}", {config["value"]}))'
    elif transform_type == "add_to_field":
        return f'pipeline = pipeline.map(transforms.add_to_field("{config["field"]}", {config["value"]}))'
    elif transform_type == "round_field":
        return f'pipeline = pipeline.map(transforms.round_field("{config["field"]}", {config["decimals"]}))'
    elif transform_type == "compute_field":
        return f'pipeline = pipeline.map(transforms.compute_field("{config["field_name"]}", lambda item: {config["expression"]}))'
    else:
        return f'# Transform: {transform_type}'


def _generate_sort_code(operation: Dict[str, Any]) -> str:
    """Generate Python code for a sort operation."""
    config = operation["config"]
    field = config["field"]
    reverse = config["reverse"]
    
    return f'pipeline = pipeline.sort(lambda item: item["{field}"], reverse={reverse})'


def _generate_limit_code(operation: Dict[str, Any]) -> str:
    """Generate Python code for a limit operation."""
    config = operation["config"]
    operation_type = config["operation"]
    value = config["value"]
    
    if operation_type == "take":
        return f'pipeline = pipeline.take({value})'
    elif operation_type == "skip":
        return f'pipeline = pipeline.skip({value})'
    else:
        return f'# Limit: {operation_type} {value}'


def _load_pipeline_config(config_data: Dict[str, Any]) -> None:
    """Load pipeline configuration from JSON data."""
    from ..utils.session_state import clear_pipeline
    
    # Clear current pipeline
    clear_pipeline()
    
    # Load operations
    if "operations" in config_data:
        st.session_state.pipeline_operations = config_data["operations"]
    
    # Store metadata
    if "metadata" in config_data:
        st.session_state.pipeline_metadata = config_data["metadata"]


def _load_example_pipelines() -> List[Dict[str, Any]]:
    """Load example pipelines from JSON file."""
    try:
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        example_file = os.path.join(current_dir, "..", "example_pipelines.json")
        
        with open(example_file, 'r') as f:
            data = json.load(f)
            return data.get("example_pipelines", [])
    except Exception:
        return []
