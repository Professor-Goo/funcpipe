"""
FuncPipe Web UI - Main Streamlit Application

Interactive web interface for building data processing pipelines visually.
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import funcpipe
sys.path.insert(0, str(Path(__file__).parent.parent))

from funcpipe_ui.utils.session_state import initialize_session_state
from funcpipe_ui.components.file_loader import render_file_uploader, render_example_data_selector
from funcpipe_ui.components.pipeline_builder import render_pipeline_builder, execute_pipeline
from funcpipe_ui.components.data_preview import render_data_preview
from funcpipe_ui.components.export_handler import render_export_handler


# Page configuration
st.set_page_config(
    page_title="FuncPipe Web UI",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #667eea;
    }
    
    .stButton > button {
        background-color: #667eea;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
    }
    
    .stButton > button:hover {
        background-color: #5a67d8;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main application function."""
    
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🔧 FuncPipe Web UI</h1>
        <p>Interactive Data Processing Pipeline Builder</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    render_sidebar()
    
    # Main content
    render_main_content()


def render_sidebar():
    """Render the sidebar with navigation and controls."""
    with st.sidebar:
        st.header("🚀 Quick Start")
        
        # Data loading options
        st.subheader("📁 Load Data")
        
        # Tab for data loading
        data_tab1, data_tab2 = st.tabs(["Upload", "Examples"])
        
        with data_tab1:
            render_file_uploader()
        
        with data_tab2:
            render_example_data_selector()
        
        # Pipeline controls
        st.subheader("🔧 Pipeline Controls")
        
        # Clear pipeline button
        if st.button("🗑️ Clear Pipeline", key="clear_pipeline"):
            from funcpipe_ui.utils.session_state import clear_pipeline
            clear_pipeline()
            st.rerun()
        
        # Run pipeline button
        from funcpipe_ui.utils.session_state import get_uploaded_data, get_pipeline_operations, set_pipeline_results
        
        uploaded_data = get_uploaded_data()
        operations = get_pipeline_operations()
        
        if uploaded_data and operations:
            if st.button("▶️ Run Pipeline", key="run_pipeline"):
                try:
                    with st.spinner("Processing pipeline..."):
                        result = execute_pipeline(uploaded_data)
                        set_pipeline_results(len(operations), result)
                    st.success(f"Pipeline executed! {len(result)} records processed.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Pipeline execution failed: {str(e)}")
        else:
            if not uploaded_data:
                st.info("Upload data to run pipeline")
            if not operations:
                st.info("Add operations to run pipeline")
        
        # Pipeline summary
        if operations:
            st.subheader("📋 Pipeline Summary")
            st.write(f"**Operations:** {len(operations)}")
            
            for i, op in enumerate(operations):
                st.write(f"{i+1}. {op.get('description', op.get('type', 'Unknown'))}")
        
        # Status
        st.subheader("📊 Status")
        uploaded_data = get_uploaded_data()
        if uploaded_data:
            st.success(f"✅ Data loaded: {len(uploaded_data)} records")
        else:
            st.info("📤 No data loaded")
        
        operations = get_pipeline_operations()
        if operations:
            st.success(f"✅ Pipeline: {len(operations)} operations")
        else:
            st.info("🔧 No operations added")


def render_main_content():
    """Render the main content area."""
    
    # Check if data is loaded
    from funcpipe_ui.utils.session_state import get_uploaded_data
    uploaded_data = get_uploaded_data()
    
    if not uploaded_data:
        render_welcome_screen()
        return
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔧 Pipeline Builder", "📊 Data Preview", "💾 Export", "📚 Help"])
    
    with tab1:
        render_pipeline_builder_tab()
    
    with tab2:
        render_data_preview_tab()
    
    with tab3:
        render_export_tab()
    
    with tab4:
        render_help_tab()


def render_welcome_screen():
    """Render welcome screen when no data is loaded."""
    st.markdown("""
    ## Welcome to FuncPipe Web UI! 🎉
    
    FuncPipe Web UI provides an intuitive, visual interface for building data processing pipelines.
    Get started by uploading your data or trying an example dataset.
    
    ### Features:
    - 🔧 **Visual Pipeline Builder**: Drag-and-drop interface for building pipelines
    - 📊 **Real-time Preview**: See results at each pipeline stage
    - 📈 **Data Analysis**: Built-in statistics and visualizations
    - 💾 **Export Options**: Download results or generate Python code
    - 🚀 **Easy to Use**: No coding required - just point and click!
    
    ### Getting Started:
    1. **Load Data**: Upload a CSV or JSON file, or try an example dataset
    2. **Build Pipeline**: Add filters, transforms, and other operations
    3. **Preview Results**: See how your data changes at each step
    4. **Export**: Download processed data or generate Python code
    
    ### Supported File Formats:
    - CSV files (.csv)
    - JSON files (.json)
    
    ### Example Use Cases:
    - Filter and clean customer data
    - Transform product catalogs
    - Analyze sales data
    - Prepare data for machine learning
    
    **Ready to get started?** Use the sidebar to upload your data or try an example!
    """)


def render_pipeline_builder_tab():
    """Render the pipeline builder tab."""
    st.header("🔧 Pipeline Builder")
    
    # Show current data info
    from funcpipe_ui.utils.session_state import get_uploaded_data, get_field_names
    uploaded_data = get_uploaded_data()
    field_names = get_field_names()
    
    if uploaded_data:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Records", len(uploaded_data))
        with col2:
            st.metric("Fields", len(field_names))
        with col3:
            st.metric("Data Type", "Ready for processing")
        
        st.write(f"**Available Fields:** {', '.join(field_names)}")
    
    # Pipeline builder
    render_pipeline_builder()


def render_data_preview_tab():
    """Render the data preview tab."""
    st.header("📊 Data Preview")
    render_data_preview()


def render_export_tab():
    """Render the export tab."""
    st.header("💾 Export Results")
    render_export_handler()


def render_help_tab():
    """Render the help tab."""
    st.header("📚 Help & Documentation")
    
    st.markdown("""
    ## How to Use FuncPipe Web UI
    
    ### 1. Loading Data
    - **Upload Files**: Use the sidebar to upload CSV or JSON files
    - **Example Data**: Try the built-in example datasets to get started
    - **File Requirements**: CSV files should have headers, JSON files should contain objects or arrays of objects
    
    ### 2. Building Pipelines
    
    #### Filters
    Filters remove records that don't meet certain criteria:
    - **Equals**: Keep records where field equals a specific value
    - **Greater Than/Less Than**: Numeric comparisons
    - **Contains**: String contains substring
    - **Is Null/Not Null**: Check for missing values
    - **Between**: Range checks for numeric fields
    - **In List**: Keep records with values in a specified list
    
    #### Transforms
    Transforms modify or add fields:
    - **Text Operations**: Capitalize, uppercase, lowercase, strip whitespace
    - **Field Operations**: Add, remove, or rename fields
    - **Numeric Operations**: Multiply, add, round values
    - **Custom Computation**: Create new fields using expressions
    
    #### Sort & Limit
    - **Sort**: Order records by any field (ascending or descending)
    - **Take**: Keep only the first N records
    - **Skip**: Skip the first N records
    
    ### 3. Data Preview
    - **Overview**: See summary statistics and current results
    - **Stage-by-Stage**: View data at each pipeline step
    - **Statistics**: Detailed field analysis and visualizations
    - **Data Quality**: Check for missing data and duplicates
    
    ### 4. Export Options
    - **Download Data**: Export results as JSON, CSV, or TSV
    - **Python Code**: Generate a complete Python script
    - **Save Pipeline**: Save pipeline configuration for later use
    
    ### Tips & Best Practices
    
    1. **Start Small**: Begin with simple operations and build complexity gradually
    2. **Preview Often**: Use the data preview to verify each step
    3. **Check Data Quality**: Use the data quality tab to identify issues
    4. **Save Your Work**: Export pipeline configurations for reuse
    5. **Test with Examples**: Try the example datasets to learn the interface
    
    ### Troubleshooting
    
    **Pipeline Execution Errors:**
    - Check that all required fields exist in your data
    - Verify that numeric operations are applied to numeric fields
    - Ensure filter values match the expected data types
    
    **File Upload Issues:**
    - Make sure your CSV file has headers
    - Check that JSON files contain valid JSON
    - Try the example datasets to verify the interface works
    
    **Performance:**
    - Large datasets may take longer to process
    - Use filters early in your pipeline to reduce data size
    - Consider sampling your data for testing
    
    ### Keyboard Shortcuts
    - **Ctrl+R**: Run pipeline (when focused on run button)
    - **Ctrl+S**: Save pipeline configuration
    - **Ctrl+C**: Copy Python code to clipboard
    
    ### Need More Help?
    - Check the [FuncPipe Documentation](https://github.com/Professor-Goo/funcpipe) for the core library
    - Try the example datasets to see common use cases
    - Use the stage-by-stage preview to understand how each operation works
    """)


if __name__ == "__main__":
    main()
