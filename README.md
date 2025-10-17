# FuncPipe

A functional data processing pipeline that transforms CSV/JSON data using composable functions.

## Features

- **Pure Functional**: Immutable data transformations using function composition
- **Flexible Input**: Process CSV and JSON files
- **Composable Pipeline**: Chain filters, maps, and reductions
- **Type-Safe**: Built with functional programming best practices
- **CLI & Library**: Use as command-line tool or import as Python library
- **Web UI**: Interactive browser-based pipeline builder (optional)

## Quick Start

```bash
# Filter and transform data
funcpipe data.csv --filter "age > 25" --map "capitalize_name" --output json

# Chain multiple operations  
funcpipe sales.json --filter "amount > 100" --map "add_tax:0.08" --reduce "sum:amount"

# Save processed data
funcpipe users.csv --filter "active == true" --map "format_email" --save cleaned_users.json
```

## Installation

### Core Library

```bash
pip install -e .
```

### Web UI (Optional)

To use the interactive web interface:

```bash
pip install -r requirements-ui.txt
```

## Library Usage

```python
from funcpipe import Pipeline, filters, transforms

# Build a processing pipeline
pipeline = Pipeline() \
    .filter(filters.greater_than('age', 25)) \
    .map(transforms.capitalize('name')) \
    .map(transforms.add_field('status', 'processed'))

# Process data
result = pipeline.run(data)
```

## Web UI

FuncPipe includes an optional interactive web interface for building pipelines visually.

### Launch the Web UI

```bash
streamlit run funcpipe_ui/app.py
```

### Web UI Features

- **📁 File Upload**: Upload CSV/JSON files or try example datasets
- **🔧 Visual Pipeline Builder**: Point-and-click interface for adding operations
- **📊 Real-time Preview**: See data changes at each pipeline stage
- **📈 Data Analysis**: Built-in statistics and visualizations
- **💾 Export Options**: Download results or generate Python code
- **🚀 No Coding Required**: Build complex pipelines through the UI

### Quick Start with Web UI

1. Launch the web interface: `streamlit run funcpipe_ui/app.py`
2. Upload your data file or try an example dataset
3. Add filters, transforms, and other operations using the visual builder
4. Preview results in real-time as you build your pipeline
5. Export processed data or generate Python code for reuse

The web UI is perfect for:
- Learning how FuncPipe works
- Building pipelines without writing code
- Exploring your data interactively
- Sharing pipeline configurations with team members

## Architecture

FuncPipe is built on functional programming principles:
- **Immutable Data**: All transformations create new data structures
- **Pure Functions**: No side effects, predictable outputs
- **Function Composition**: Chain operations using the `Pipeline` class
- **Higher-Order Functions**: Configurable transforms and filters

## Development

```bash
# Run tests
python -m pytest tests/

# Type check
mypy funcpipe/

# Format code
black funcpipe/

# Run web UI for development
streamlit run funcpipe_ui/app.py
```

## License

MIT License
