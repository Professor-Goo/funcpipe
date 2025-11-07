"""
File loader component for FuncPipe Web UI.

Handles file upload, format detection, and initial data preview.
"""

import streamlit as st
import pandas as pd
import json
import io
from typing import List, Dict, Any, Optional
from .utils.session_state import set_uploaded_data, get_uploaded_data, get_field_names


def render_file_uploader() -> Optional[List[Dict[str, Any]]]:
    """
    Render file uploader widget and return uploaded data.
    
    Returns:
        List of dictionaries if file is uploaded, None otherwise
    """
    st.subheader("📁 Upload Data File")
    
    uploaded_file = st.file_uploader(
        "Choose a CSV or JSON file",
        type=['csv', 'json'],
        help="Upload a CSV or JSON file to start building your pipeline"
    )
    
    if uploaded_file is not None:
        try:
            # Read file based on extension
            if uploaded_file.name.endswith('.csv'):
                data = _read_csv_file(uploaded_file)
            elif uploaded_file.name.endswith('.json'):
                data = _read_json_file(uploaded_file)
            else:
                st.error("Unsupported file format. Please upload CSV or JSON.")
                return None
            
            # Store in session state
            set_uploaded_data(data)
            
            # Display file info and preview
            _display_file_info(uploaded_file, data)
            _display_data_preview(data)
            
            return data
            
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
            return None
    
    return None


def _read_csv_file(uploaded_file) -> List[Dict[str, Any]]:
    """Read CSV file and return list of dictionaries."""
    # Read as pandas DataFrame first
    df = pd.read_csv(uploaded_file)
    
    # Convert to list of dictionaries
    data = df.to_dict('records')
    
    # Convert numeric strings to numbers where possible
    for item in data:
        for key, value in item.items():
            if isinstance(value, str) and value.strip():
                # Try to convert to int first
                try:
                    if '.' not in value:
                        item[key] = int(value)
                    else:
                        item[key] = float(value)
                except ValueError:
                    pass  # Keep as string
    
    return data


def _read_json_file(uploaded_file) -> List[Dict[str, Any]]:
    """Read JSON file and return list of dictionaries."""
    # Read file content
    content = uploaded_file.read().decode('utf-8')
    
    # Parse JSON
    json_data = json.loads(content)
    
    # Ensure we return a list of dictionaries
    if isinstance(json_data, dict):
        return [json_data]
    elif isinstance(json_data, list):
        return json_data
    else:
        raise ValueError("JSON must contain object or array of objects")


def _display_file_info(uploaded_file, data: List[Dict[str, Any]]) -> None:
    """Display file information."""
    st.success(f"✅ File uploaded successfully: {uploaded_file.name}")
    
    # Create columns for file info
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Records", len(data))
    
    with col2:
        st.metric("Fields", len(data[0].keys()) if data else 0)
    
    with col3:
        file_size = len(uploaded_file.getvalue())
        st.metric("Size", f"{file_size:,} bytes")
    
    with col4:
        file_format = uploaded_file.name.split('.')[-1].upper()
        st.metric("Format", file_format)


def _display_data_preview(data: List[Dict[str, Any]], max_rows: int = 5) -> None:
    """Display data preview in a table."""
    if not data:
        return
    
    st.subheader("📊 Data Preview")
    
    # Show field names
    field_names = list(data[0].keys())
    st.write(f"**Fields:** {', '.join(field_names)}")
    
    # Create DataFrame for display
    df = pd.DataFrame(data)
    
    # Display first few rows
    st.dataframe(df.head(max_rows), use_container_width=True)
    
    # Show data types
    st.write("**Data Types:**")
    type_info = {}
    for item in data[:10]:  # Check first 10 items for type inference
        for key, value in item.items():
            if key not in type_info:
                type_info[key] = type(value).__name__
    
    for field, type_name in type_info.items():
        st.write(f"  - {field}: {type_name}")


def render_example_data_selector() -> Optional[List[Dict[str, Any]]]:
    """
    Render selector for example datasets.
    
    Returns:
        List of dictionaries if example is selected, None otherwise
    """
    st.subheader("📋 Load Example Data")
    
    examples = {
        "Employee Data": _get_employee_example(),
        "Product Data": _get_product_example(),
        "Sales Data": _get_sales_example()
    }
    
    selected_example = st.selectbox(
        "Choose an example dataset:",
        ["None"] + list(examples.keys())
    )
    
    if selected_example != "None":
        data = examples[selected_example]
        set_uploaded_data(data)
        
        st.success(f"✅ Loaded example: {selected_example}")
        _display_data_preview(data)
        
        return data
    
    return None


def _get_employee_example() -> List[Dict[str, Any]]:
    """Generate sample employee data."""
    return [
        {"name": "Alice Johnson", "age": 28, "department": "Engineering", "salary": 75000, "active": True},
        {"name": "Bob Smith", "age": 32, "department": "Marketing", "salary": 65000, "active": True},
        {"name": "Charlie Brown", "age": 25, "department": "Engineering", "salary": 70000, "active": False},
        {"name": "Diana Prince", "age": 30, "department": "Sales", "salary": 60000, "active": True},
        {"name": "Eve Adams", "age": 35, "department": "Engineering", "salary": 85000, "active": True},
        {"name": "Frank Miller", "age": 29, "department": "Marketing", "salary": 58000, "active": True},
        {"name": "Grace Lee", "age": 27, "department": "Sales", "salary": 62000, "active": False},
        {"name": "Henry Ford", "age": 31, "department": "Engineering", "salary": 78000, "active": True}
    ]


def _get_product_example() -> List[Dict[str, Any]]:
    """Generate sample product data."""
    return [
        {"name": "Laptop", "category": "Electronics", "price": 999.99, "quantity": 50, "in_stock": True},
        {"name": "Mouse", "category": "Electronics", "price": 29.99, "quantity": 200, "in_stock": True},
        {"name": "Desk Chair", "category": "Furniture", "price": 199.99, "quantity": 25, "in_stock": True},
        {"name": "Coffee Mug", "category": "Office Supplies", "price": 12.99, "quantity": 100, "in_stock": True},
        {"name": "Monitor", "category": "Electronics", "price": 299.99, "quantity": 0, "in_stock": False},
        {"name": "Keyboard", "category": "Electronics", "price": 79.99, "quantity": 75, "in_stock": True},
        {"name": "Notebook", "category": "Office Supplies", "price": 5.99, "quantity": 500, "in_stock": True},
        {"name": "Pen Set", "category": "Office Supplies", "price": 15.99, "quantity": 150, "in_stock": True}
    ]


def _get_sales_example() -> List[Dict[str, Any]]:
    """Generate sample sales data."""
    return [
        {"product": "Laptop", "customer": "Alice", "amount": 999.99, "date": "2024-01-15", "region": "North"},
        {"product": "Mouse", "customer": "Bob", "amount": 29.99, "date": "2024-01-16", "region": "South"},
        {"product": "Monitor", "customer": "Charlie", "amount": 299.99, "date": "2024-01-17", "region": "East"},
        {"product": "Keyboard", "customer": "Diana", "amount": 79.99, "date": "2024-01-18", "region": "West"},
        {"product": "Laptop", "customer": "Eve", "amount": 999.99, "date": "2024-01-19", "region": "North"},
        {"product": "Desk Chair", "customer": "Frank", "amount": 199.99, "date": "2024-01-20", "region": "South"},
        {"product": "Mouse", "customer": "Grace", "amount": 29.99, "date": "2024-01-21", "region": "East"},
        {"product": "Notebook", "customer": "Henry", "amount": 5.99, "date": "2024-01-22", "region": "West"}
    ]
