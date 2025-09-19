# FuncPipe

A functional data processing pipeline that transforms CSV/JSON data using composable functions.

## Features

- **Pure Functional**: Immutable data transformations using function composition
- **Flexible Input**: Process CSV and JSON files
- **Composable Pipeline**: Chain filters, maps, and reductions
- **Type-Safe**: Built with functional programming best practices
- **CLI & Library**: Use as command-line tool or import as Python library

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

```bash
pip install -e .
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
```

## License

MIT License
