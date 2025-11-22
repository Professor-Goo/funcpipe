"""
Data preview component for FuncPipe Web UI.

Provides real-time visualization of data at each pipeline stage
with diff highlighting and statistics display.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any, Optional
from ..utils.session_state import get_uploaded_data, get_current_data
from .pipeline_builder import execute_pipeline


def render_data_preview() -> None:
    """Render the main data preview interface."""
    uploaded_data = get_uploaded_data()
    
    if not uploaded_data:
        st.info("📊 Upload data to see preview")
        return
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "🔍 Stage-by-Stage", "📊 Statistics", "🔬 Data Quality"])
    
    with tab1:
        _render_overview_tab(uploaded_data)
    
    with tab2:
        _render_stage_by_stage_tab(uploaded_data)
    
    with tab3:
        _render_statistics_tab(uploaded_data)
    
    with tab4:
        _render_data_quality_tab(uploaded_data)


def _render_overview_tab(data: List[Dict[str, Any]]) -> None:
    """Render overview tab with current pipeline results."""
    st.subheader("📈 Pipeline Results Overview")
    
    # Get current processed data
    current_data = get_current_data()
    
    if current_data is None:
        st.info("Run pipeline to see results")
        return
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Original Records", len(data))
    
    with col2:
        st.metric("Filtered Records", len(current_data))
    
    with col3:
        reduction_pct = ((len(data) - len(current_data)) / len(data) * 100) if data else 0
        st.metric("Reduction", f"{reduction_pct:.1f}%")
    
    with col4:
        if data and current_data:
            original_fields = len(data[0].keys()) if data else 0
            current_fields = len(current_data[0].keys()) if current_data else 0
            st.metric("Fields", f"{current_fields}/{original_fields}")
    
    # Display current data
    if current_data:
        st.subheader("Current Data Preview")
        df = pd.DataFrame(current_data)
        st.dataframe(df, use_container_width=True)
        
        # Quick visualization
        _render_quick_visualization(current_data)


def _render_stage_by_stage_tab(data: List[Dict[str, Any]]) -> None:
    """Render stage-by-stage analysis."""
    st.subheader("🔍 Stage-by-Stage Analysis")
    
    if not data:
        st.info("Upload data to see stage-by-stage analysis")
        return
    
    # Get pipeline operations
    from ..utils.session_state import get_pipeline_operations
    operations = get_pipeline_operations()
    
    if not operations:
        st.info("Add operations to see stage-by-stage analysis")
        return
    
    # Execute pipeline step by step
    current_data = data
    stages = [{"name": "Original Data", "data": current_data}]
    
    for i, operation in enumerate(operations):
        # Execute up to this point
        pipeline = _create_pipeline_up_to_stage(i)
        current_data = pipeline.run(data)
        
        stage_name = f"Step {i+1}: {operation.get('description', operation.get('type', 'Unknown'))}"
        stages.append({"name": stage_name, "data": current_data})
    
    # Display each stage
    for i, stage in enumerate(stages):
        with st.expander(f"{stage['name']} ({len(stage['data'])} records)", expanded=(i == len(stages)-1)):
            if stage['data']:
                df = pd.DataFrame(stage['data'])
                st.dataframe(df.head(10), use_container_width=True)
                
                # Show changes from previous stage
                if i > 0:
                    prev_data = stages[i-1]['data']
                    changes = _calculate_stage_changes(prev_data, stage['data'])
                    if changes:
                        st.write("**Changes from previous stage:**")
                        for change in changes:
                            st.write(f"  - {change}")
            else:
                st.warning("No data remaining at this stage")


def _render_statistics_tab(data: List[Dict[str, Any]]) -> None:
    """Render statistics tab with data analysis."""
    st.subheader("📊 Data Statistics")
    
    current_data = get_current_data()
    if current_data is None:
        st.info("Run pipeline to see statistics")
        return
    
    # Field statistics
    st.write("**Field Statistics:**")
    
    field_stats = _calculate_field_statistics(current_data)
    
    for field, stats in field_stats.items():
        with st.expander(f"📋 {field}", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Type:** {stats['type']}")
                st.write(f"**Non-null:** {stats['non_null']}/{stats['total']} ({stats['non_null_pct']:.1f}%)")
                
                if stats['type'] in ['int', 'float']:
                    st.write(f"**Min:** {stats.get('min', 'N/A')}")
                    st.write(f"**Max:** {stats.get('max', 'N/A')}")
                    st.write(f"**Mean:** {stats.get('mean', 'N/A')}")
                
                if stats['type'] == 'str':
                    st.write(f"**Unique values:** {stats.get('unique_count', 'N/A')}")
            
            with col2:
                # Show sample values
                st.write("**Sample values:**")
                sample_values = stats.get('sample_values', [])
                for value in sample_values[:5]:
                    st.write(f"  - {value}")
                
                if len(sample_values) > 5:
                    st.write(f"  - ... and {len(sample_values) - 5} more")
    
    # Visualizations
    _render_statistics_visualizations(current_data, field_stats)


def _render_data_quality_tab(data: List[Dict[str, Any]]) -> None:
    """Render data quality analysis."""
    st.subheader("🔬 Data Quality Analysis")
    
    current_data = get_current_data()
    if current_data is None:
        st.info("Run pipeline to see data quality analysis")
        return
    
    # Data completeness
    st.write("**Data Completeness:**")
    completeness = _calculate_data_completeness(current_data)
    
    # Create completeness chart
    fields = list(completeness.keys())
    completeness_values = [completeness[field]['completeness_pct'] for field in fields]
    
    fig = go.Figure(data=[
        go.Bar(
            x=fields,
            y=completeness_values,
            text=[f"{v:.1f}%" for v in completeness_values],
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title="Field Completeness",
        xaxis_title="Fields",
        yaxis_title="Completeness (%)",
        yaxis=dict(range=[0, 100])
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Missing data details
    st.write("**Missing Data Details:**")
    for field, info in completeness.items():
        if info['missing_count'] > 0:
            st.write(f"  - **{field}**: {info['missing_count']} missing ({info['missing_pct']:.1f}%)")
    
    # Duplicate analysis
    duplicates = _find_duplicates(current_data)
    if duplicates:
        st.write(f"**Duplicates:** {len(duplicates)} duplicate records found")
        
        if st.checkbox("Show duplicate records"):
            st.dataframe(pd.DataFrame(duplicates), use_container_width=True)
    else:
        st.write("**Duplicates:** No duplicate records found")


def _render_quick_visualization(data: List[Dict[str, Any]]) -> None:
    """Render quick visualizations based on data types."""
    if not data:
        return
    
    # Get numeric and categorical fields
    numeric_fields = []
    categorical_fields = []
    
    for key, value in data[0].items():
        if isinstance(value, (int, float)):
            numeric_fields.append(key)
        elif isinstance(value, str):
            categorical_fields.append(key)
    
    # Numeric field distributions
    if numeric_fields:
        st.write("**Numeric Field Distributions:**")
        selected_field = st.selectbox("Select field:", numeric_fields, key="viz_numeric_field")
        
        if selected_field:
            values = [item[selected_field] for item in data if item[selected_field] is not None]
            if values:
                fig = px.histogram(
                    x=values,
                    title=f"Distribution of {selected_field}",
                    nbins=20
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # Categorical field distributions
    if categorical_fields:
        st.write("**Categorical Field Distributions:**")
        selected_field = st.selectbox("Select field:", categorical_fields, key="viz_categorical_field")
        
        if selected_field:
            values = [str(item[selected_field]) for item in data if item[selected_field] is not None]
            if values:
                # Count occurrences
                value_counts = {}
                for value in values:
                    value_counts[value] = value_counts.get(value, 0) + 1
                
                # Create pie chart
                fig = px.pie(
                    values=list(value_counts.values()),
                    names=list(value_counts.keys()),
                    title=f"Distribution of {selected_field}"
                )
                st.plotly_chart(fig, use_container_width=True)


def _calculate_stage_changes(prev_data: List[Dict[str, Any]], current_data: List[Dict[str, Any]]) -> List[str]:
    """Calculate changes between two data stages."""
    changes = []
    
    # Record count change
    record_diff = len(current_data) - len(prev_data)
    if record_diff != 0:
        changes.append(f"Records: {len(prev_data)} → {len(current_data)} ({record_diff:+d})")
    
    # Field changes
    if prev_data and current_data:
        prev_fields = set(prev_data[0].keys())
        current_fields = set(current_data[0].keys())
        
        added_fields = current_fields - prev_fields
        removed_fields = prev_fields - current_fields
        
        if added_fields:
            changes.append(f"Added fields: {', '.join(added_fields)}")
        if removed_fields:
            changes.append(f"Removed fields: {', '.join(removed_fields)}")
    
    return changes


def _calculate_field_statistics(data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Calculate statistics for each field."""
    if not data:
        return {}
    
    field_stats = {}
    
    for field in data[0].keys():
        values = [item[field] for item in data]
        non_null_values = [v for v in values if v is not None and v != '']
        
        stats = {
            'type': type(non_null_values[0]).__name__ if non_null_values else 'unknown',
            'total': len(values),
            'non_null': len(non_null_values),
            'non_null_pct': (len(non_null_values) / len(values)) * 100 if values else 0,
            'sample_values': list(set(str(v) for v in non_null_values[:10]))
        }
        
        if non_null_values and isinstance(non_null_values[0], (int, float)):
            numeric_values = [v for v in non_null_values if isinstance(v, (int, float))]
            if numeric_values:
                stats.update({
                    'min': min(numeric_values),
                    'max': max(numeric_values),
                    'mean': sum(numeric_values) / len(numeric_values)
                })
        
        if non_null_values and isinstance(non_null_values[0], str):
            unique_values = set(str(v) for v in non_null_values)
            stats['unique_count'] = len(unique_values)
        
        field_stats[field] = stats
    
    return field_stats


def _render_statistics_visualizations(data: List[Dict[str, Any]], field_stats: Dict[str, Dict[str, Any]]) -> None:
    """Render visualizations for field statistics."""
    if not data or not field_stats:
        return

    st.write("**Field Visualizations:**")

    # Separate numeric and categorical fields
    numeric_fields = [field for field, stats in field_stats.items() if stats['type'] in ['int', 'float']]
    categorical_fields = [field for field, stats in field_stats.items() if stats['type'] == 'str']

    # Numeric field visualizations
    if numeric_fields:
        selected_numeric = st.selectbox("Select numeric field to visualize:", numeric_fields, key="stats_numeric_field")

        if selected_numeric:
            values = [item[selected_numeric] for item in data if item.get(selected_numeric) is not None]
            if values:
                fig = px.histogram(
                    x=values,
                    title=f"Distribution of {selected_numeric}",
                    nbins=30,
                    labels={'x': selected_numeric, 'y': 'Count'}
                )
                st.plotly_chart(fig, use_container_width=True)

    # Categorical field visualizations
    if categorical_fields:
        selected_categorical = st.selectbox("Select categorical field to visualize:", categorical_fields, key="stats_categorical_field")

        if selected_categorical:
            values = [str(item[selected_categorical]) for item in data if item.get(selected_categorical) is not None and item[selected_categorical] != '']
            if values:
                # Count unique values
                value_counts = {}
                for value in values:
                    value_counts[value] = value_counts.get(value, 0) + 1

                # Sort by count and take top 10
                sorted_counts = sorted(value_counts.items(), key=lambda x: x[1], reverse=True)[:10]

                if sorted_counts:
                    fig = go.Figure(data=[
                        go.Bar(
                            x=[item[0] for item in sorted_counts],
                            y=[item[1] for item in sorted_counts],
                            text=[item[1] for item in sorted_counts],
                            textposition='auto',
                        )
                    ])

                    fig.update_layout(
                        title=f"Top Values for {selected_categorical}",
                        xaxis_title=selected_categorical,
                        yaxis_title="Count"
                    )

                    st.plotly_chart(fig, use_container_width=True)


def _calculate_data_completeness(data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Calculate data completeness for each field."""
    if not data:
        return {}

    completeness = {}
    total_records = len(data)
    
    for field in data[0].keys():
        missing_count = sum(1 for item in data if item[field] is None or item[field] == '')
        
        completeness[field] = {
            'missing_count': missing_count,
            'missing_pct': (missing_count / total_records) * 100 if total_records > 0 else 0,
            'completeness_pct': ((total_records - missing_count) / total_records) * 100 if total_records > 0 else 0
        }
    
    return completeness


def _find_duplicates(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find duplicate records in the data."""
    seen = set()
    duplicates = []
    
    for item in data:
        # Create a hashable representation of the item
        item_tuple = tuple(sorted(item.items()))
        if item_tuple in seen:
            duplicates.append(item)
        else:
            seen.add(item_tuple)
    
    return duplicates


def _create_pipeline_up_to_stage(stage_index: int):
    """Create pipeline that executes up to the specified stage."""
    from funcpipe import Pipeline, filters, transforms
    from ..utils.session_state import get_pipeline_operations
    
    pipeline = Pipeline()
    operations = get_pipeline_operations()
    
    for i in range(min(stage_index + 1, len(operations))):
        operation = operations[i]
        
        if operation["type"] == "filter":
            from .pipeline_builder import _create_filter_function
            filter_func = _create_filter_function(operation["config"])
            pipeline = pipeline.filter(filter_func)
            
        elif operation["type"] == "transform":
            from .pipeline_builder import _create_transform_function
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
    
    return pipeline
