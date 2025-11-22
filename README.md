# FuncPipe

A functional data processing pipeline for transforming CSV and JSON data using composable functions.

## Features

- **Pure Functional**: Immutable data transformations using function composition
- **Flexible Input**: Process CSV and JSON files
- **Composable Pipeline**: Chain filters, maps, and reductions
- **Type-Safe**: Built with functional programming best practices
- **CLI & Library**: Use as command-line tool or import as Python library
- **Web UI**: Interactive browser-based pipeline builder (optional)

## Prerequisites

- Python >= 3.8
- pip (Python package installer)

## Installation

### For Users

Install the library and CLI tool:

```bash
# Clone the repository
git clone https://github.com/Professor-Goo/funcpipe.git
cd funcpipe

# Install the package
pip install .
```

### For Developers

Install in editable mode for development:

```bash
# Clone the repository
git clone https://github.com/Professor-Goo/funcpipe.git
cd funcpipe

# Install in editable mode with development dependencies
pip install -e .
pip install pytest pytest-cov black mypy flake8
```

### Web UI (Optional)

To use the interactive web interface, install additional dependencies:

```bash
pip install -r requirements-ui.txt
```

## Quick Start

### Command Line Interface

The `funcpipe` CLI provides several commands for data processing:

#### Inspect Data Files

```bash
# View file information and sample data
funcpipe inspect examples/employees.csv

# Show file statistics only
funcpipe inspect examples/employees.csv --info

# View first 10 records
funcpipe inspect examples/employees.csv --sample 10
```

#### Process Data

```bash
# Filter employees older than 25
funcpipe process examples/employees.csv --filter "age > 25"

# Filter and transform data
funcpipe process examples/employees.csv \
  --filter "age > 25" \
  --map "capitalize:name" \
  --output results.json

# Chain multiple operations
funcpipe process examples/employees.csv \
  --filter "department == Engineering" \
  --filter "salary > 50000" \
  --map "multiply:salary:1.1" \
  --map "round:salary:0" \
  --sort "salary:desc" \
  --output engineers_raise.csv

# Take first 5 records after sorting
funcpipe process examples/employees.csv \
  --sort "age:desc" \
  --take 5
```

#### Generate Reports

```bash
# Generate comprehensive analysis report
funcpipe report examples/employees.csv output_reports/
```

#### Merge Files

```bash
# Merge multiple CSV/JSON files
funcpipe merge file1.csv file2.csv file3.csv --output combined.json
```

#### Split Files

```bash
# Split file by department field
funcpipe split examples/employees.csv department --output-dir by_department/
```

### Filter Expressions

Supported filter operators:

- **Comparisons**: `>`, `>=`, `<`, `<=`, `==`, `!=`
  - Example: `"age > 25"`, `"salary >= 50000"`
- **String operations**: `contains`, `starts with`, `ends with`
  - Example: `"name contains Adams"`, `"email ends with .com"`
- **Null checks**: `is null`, `is not null`
  - Example: `"middle_name is null"`

### Map Expressions

Supported transformations (format: `operation:field` or `operation:field:params`):

- **String operations**: `capitalize:name`, `upper:email`, `lower:name`, `strip:name`
- **Numeric operations**: `multiply:salary:1.1`, `add:price:10`, `round:salary:2`
- **Type casting**: `cast:age:int`, `cast:price:float`
- **String replacement**: `replace:name:old:new`
- **Field operations**: `remove:field_name`

## Library Usage

### Basic Pipeline

```python
from funcpipe import Pipeline, filters, transforms

# Read data (or load from your source)
data = [
    {"name": "alice", "age": 30, "salary": 50000},
    {"name": "bob", "age": 25, "salary": 45000},
    {"name": "charlie", "age": 35, "salary": 60000}
]

# Build a processing pipeline
pipeline = (Pipeline()
    .filter(filters.greater_than('age', 25))
    .map(transforms.capitalize_field('name'))
    .map(transforms.multiply_field('salary', 1.05))
    .map(transforms.round_field('salary', 0))
    .sort(lambda emp: emp['salary'], reverse=True))

# Execute pipeline
result = pipeline.run(data)
print(result)
```

### Reading and Writing Files

```python
from funcpipe import Pipeline, filters, transforms, readers, writers

# Read CSV or JSON files
employees = readers.read_csv('examples/employees.csv')
products = readers.read_json('examples/products.json')

# Or auto-detect format
data = readers.auto_read('data.csv')

# Process data
pipeline = (Pipeline()
    .filter(filters.equals('active', True))
    .map(transforms.add_field('status', 'processed')))

result = pipeline.run(employees)

# Write results
writers.write_json(result, 'output.json')
writers.write_csv(result, 'output.csv')
writers.auto_write(result, 'output.tsv')  # Auto-detect from extension
```

### Available Filters

**Comparison Filters**:
- `filters.equals(field, value)` - Exact equality
- `filters.greater_than(field, value)` - Greater than
- `filters.greater_than_or_equal(field, value)` - Greater than or equal
- `filters.less_than(field, value)` - Less than
- `filters.less_than_or_equal(field, value)` - Less than or equal
- `filters.between(field, min_val, max_val)` - Range check

**String Filters**:
- `filters.contains(field, substring)` - Contains substring
- `filters.starts_with(field, prefix)` - Starts with prefix
- `filters.ends_with(field, suffix)` - Ends with suffix
- `filters.matches_regex(field, pattern)` - Regex pattern match

**Null Filters**:
- `filters.is_null(field)` - Field is None
- `filters.is_not_null(field)` - Field is not None

**List Filters**:
- `filters.in_list(field, values)` - Value in list
- `filters.not_in_list(field, values)` - Value not in list

**Combining Filters**:
- `filters.and_filter(*predicates)` - All conditions must be true
- `filters.or_filter(*predicates)` - Any condition must be true
- `filters.not_filter(predicate)` - Negate condition

### Available Transforms

**Field Operations**:
- `transforms.add_field(name, value)` - Add new field with static value
- `transforms.remove_field(name)` - Remove field
- `transforms.rename_field(old_name, new_name)` - Rename field
- `transforms.select_fields([names])` - Keep only specified fields
- `transforms.exclude_fields([names])` - Remove specified fields

**String Transforms**:
- `transforms.capitalize_field(field)` - Capitalize first letter
- `transforms.upper_field(field)` - Convert to uppercase
- `transforms.lower_field(field)` - Convert to lowercase
- `transforms.strip_field(field)` - Remove whitespace
- `transforms.replace_in_field(field, old, new)` - Replace substring

**Numeric Transforms**:
- `transforms.multiply_field(field, factor)` - Multiply by factor
- `transforms.add_to_field(field, value)` - Add value
- `transforms.round_field(field, decimals)` - Round to decimals

**Advanced Transforms**:
- `transforms.compute_field(name, func)` - Compute from other fields
- `transforms.cast_field(field, type)` - Cast to int/float/str
- `transforms.split_field(source, targets, separator)` - Split into multiple fields
- `transforms.extract_regex_field(source, target, pattern)` - Extract with regex
- `transforms.apply_function(field, func)` - Apply custom function

### Complex Example

```python
from funcpipe import Pipeline, filters, transforms, readers, writers

# Load employee data
employees = readers.read_csv('examples/employees.csv')

# Create a complex processing pipeline
pipeline = (Pipeline()
    # Filter active engineering employees
    .filter(filters.and_filter(
        filters.equals('active', True),
        filters.equals('department', 'Engineering'),
        filters.greater_than('age', 26)
    ))
    # Normalize names
    .map(transforms.strip_field('name'))
    .map(transforms.capitalize_field('name'))
    # Give 5% raise and round
    .map(transforms.multiply_field('salary', 1.05))
    .map(transforms.round_field('salary', 0))
    # Add bonus
    .map(transforms.add_field('bonus', 2000))
    # Compute total compensation
    .map(transforms.compute_field('total_comp',
         lambda emp: emp['salary'] + emp['bonus']))
    # Sort by total compensation
    .sort(lambda emp: emp['total_comp'], reverse=True))

# Execute and save
result = pipeline.run(employees)
writers.write_json(result, 'engineering_raises.json')
print(f"Processed {len(result)} employees")
```

## Web UI

FuncPipe includes an optional interactive web interface for building pipelines visually.

### Launch the Web UI

```bash
streamlit run funcpipe_ui/app.py
```

Then open your browser to the URL shown (typically http://localhost:8501)

### Web UI Features

- **📁 File Upload**: Upload CSV/JSON files or try example datasets
- **🔧 Visual Pipeline Builder**: Point-and-click interface for adding operations
- **📊 Real-time Preview**: See data changes at each pipeline stage
- **📈 Data Analysis**: Built-in statistics and visualizations
- **💾 Export Options**: Download results or generate Python code
- **🚀 No Coding Required**: Build complex pipelines through the UI

### Web UI Quick Start

1. Launch the web interface: `streamlit run funcpipe_ui/app.py`
2. Upload your data file or select an example dataset (employees.csv or products.json)
3. Add filters, transforms, and other operations using the visual builder
4. Preview results in real-time as you build your pipeline
5. Export processed data or generate Python code for reuse

The web UI is perfect for:
- Learning how FuncPipe works
- Building pipelines without writing code
- Exploring your data interactively
- Prototyping transformations before coding them

## Examples

The repository includes example data files and a demo script:

```bash
# Run the demo script
python examples/demo.py

# Example data files
examples/employees.csv    # Sample employee data
examples/products.json    # Sample product catalog
```

## Architecture

FuncPipe is built on functional programming principles:

- **Immutable Data**: All transformations create new data structures, never modifying originals
- **Pure Functions**: No side effects, same input always produces same output
- **Function Composition**: Chain operations using the `Pipeline` class
- **Higher-Order Functions**: Configurable transforms and filters
- **Currying**: Pre-configure functions with parameters for reuse

## Development

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=funcpipe --cov-report=html

# Run specific test file
python -m pytest tests/test_pipeline.py
```

### Code Quality

```bash
# Format code
black funcpipe/

# Type checking
mypy funcpipe/

# Linting
flake8 funcpipe/
```

### Project Structure

```
funcpipe/
├── funcpipe/              # Core library
│   ├── __init__.py
│   ├── pipeline.py        # Pipeline implementation
│   ├── filters.py         # Filter functions
│   ├── transforms.py      # Transform functions
│   ├── readers.py         # Data readers (CSV/JSON)
│   ├── writers.py         # Data writers
│   └── cli.py             # Command-line interface
├── funcpipe_ui/           # Web UI (optional)
│   ├── app.py             # Streamlit application
│   └── components/        # UI components
├── examples/              # Example scripts and data
├── tests/                 # Test suite
└── README.md              # This file
```

## Dependencies

**Core Library**:
- click >= 8.0.0 (CLI framework)
- pandas >= 1.3.0 (Data processing)

**Web UI** (optional):
- streamlit >= 1.28.0 (Web framework)
- plotly >= 5.17.0 (Visualizations)

**Development** (optional):
- pytest >= 6.0 (Testing)
- black >= 21.0 (Code formatting)
- mypy >= 0.910 (Type checking)

## Troubleshooting

### Command not found: funcpipe

After installation, if `funcpipe` command is not found:
1. Ensure you installed the package: `pip install .`
2. Check that pip's bin directory is in your PATH
3. Try running with full path: `python -m funcpipe.cli`

### Import errors

If you get import errors:
1. Make sure you're in the correct virtual environment
2. Reinstall: `pip install --force-reinstall .`
3. For development, use: `pip install -e .`

### Web UI won't start

1. Ensure UI dependencies are installed: `pip install -r requirements-ui.txt`
2. Check that streamlit is in your PATH: `which streamlit`
3. Try: `python -m streamlit run funcpipe_ui/app.py`

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Run tests: `pytest tests/`
5. Format code: `black funcpipe/`
6. Submit a pull request

## License

MIT License - see LICENSE file for details

## Links

- **Repository**: https://github.com/Professor-Goo/funcpipe
- **Issues**: https://github.com/Professor-Goo/funcpipe/issues
- **Examples**: See `examples/demo.py` for comprehensive usage examples
