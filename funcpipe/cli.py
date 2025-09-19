"""
Command-line interface for funcpipe.

Provides a functional data processing pipeline through CLI commands.
"""

import click
from typing import List, Dict, Any
from pathlib import Path
import sys

from . import Pipeline, filters, transforms, readers, writers


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """FuncPipe - Functional Data Processing Pipeline"""
    pass


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output file path')
@click.option('--format', '-f', type=click.Choice(['json', 'csv', 'tsv', 'table']), 
              help='Output format (auto-detected if not specified)')
@click.option('--sample', '-s', type=int, help='Show only first N records')
@click.option('--info', is_flag=True, help='Show file information only')
def inspect(input_file: str, output: str, format: str, sample: int, info: bool):
    """Inspect data file contents and structure."""
    try:
        if info:
            file_info = readers.get_file_info(input_file)
            click.echo(f"File: {file_info['filename']}")
            click.echo(f"Size: {file_info['size_bytes']} bytes")
            click.echo(f"Format: {file_info['format']}")
            
            if 'fields' in file_info:
                click.echo(f"Fields ({file_info['field_count']}): {', '.join(file_info['fields'])}")
            if 'record_count' in file_info:
                click.echo(f"Records: {file_info['record_count']}")
            if 'error' in file_info:
                click.echo(f"Error: {file_info['error']}", err=True)
            return
        
        # Read data
        data = readers.auto_read(input_file)
        
        # Apply sample limit if specified
        if sample:
            data = data[:sample]
        
        # Output results
        if output:
            if format:
                # Override auto-detection with specified format
                if format == 'json':
                    writers.write_json(data, output)
                elif format == 'csv':
                    writers.write_csv(data, output)
                elif format == 'tsv':
                    writers.write_tsv(data, output)
                elif format == 'table':
                    writers.write_pretty_table(data, output)
            else:
                writers.auto_write(data, output)
            click.echo(f"Data written to {output}")
        else:
            # Print to console
            writers.print_summary(data)
            click.echo()
            writers.print_sample(data, n=sample or 5)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--filter', 'filter_expr', multiple=True, 
              help='Filter expression (e.g., "age > 25")')
@click.option('--map', 'map_expr', multiple=True,
              help='Map expression (e.g., "capitalize:name")')
@click.option('--sort', 'sort_expr',
              help='Sort expression (e.g., "age" or "age:desc")')
@click.option('--take', type=int, help='Take first N records')
@click.option('--skip', type=int, help='Skip first N records')
@click.option('--output', '-o', help='Output file path')
@click.option('--format', '-f', type=click.Choice(['json', 'csv', 'tsv', 'table']),
              help='Output format')
def process(input_file: str, filter_expr: List[str], map_expr: List[str], 
           sort_expr: str, take: int, skip: int, output: str, format: str):
    """Process data through functional pipeline."""
    try:
        # Read input data
        data = readers.auto_read(input_file)
        
        # Build pipeline
        pipeline = Pipeline()
        
        # Add filters
        for expr in filter_expr:
            filter_func = _parse_filter_expression(expr)
            pipeline = pipeline.filter(filter_func)
        
        # Add maps
        for expr in map_expr:
            map_func = _parse_map_expression(expr)
            pipeline = pipeline.map(map_func)
        
        # Add sort
        if sort_expr:
            key_func, reverse = _parse_sort_expression(sort_expr)
            pipeline = pipeline.sort(key_func, reverse)
        
        # Add skip
        if skip:
            pipeline = pipeline.skip(skip)
        
        # Add take
        if take:
            pipeline = pipeline.take(take)
        
        # Execute pipeline
        result = pipeline.run(data)
        
        # Output results
        if output:
            if format:
                if format == 'json':
                    writers.write_json(result, output)
                elif format == 'csv':
                    writers.write_csv(result, output)
                elif format == 'tsv':
                    writers.write_tsv(result, output)
                elif format == 'table':
                    writers.write_pretty_table(result, output)
            else:
                writers.auto_write(result, output)
            click.echo(f"Processed {len(result)} records -> {output}")
        else:
            writers.print_sample(result, n=10)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_dir', type=click.Path())
def report(input_file: str, output_dir: str):
    """Generate comprehensive data analysis report."""
    try:
        # Read data
        data = readers.auto_read(input_file)
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate report files
        input_name = Path(input_file).stem
        
        # Summary report
        report_file = output_path / f"{input_name}_report.txt"
        writers.write_report(data, str(report_file))
        
        # Sample data in different formats
        sample_data = data[:100] if len(data) > 100 else data
        
        writers.write_json(sample_data, str(output_path / f"{input_name}_sample.json"))
        writers.write_csv(sample_data, str(output_path / f"{input_name}_sample.csv"))
        writers.write_pretty_table(sample_data, str(output_path / f"{input_name}_sample.txt"))
        
        click.echo(f"Report generated in {output_dir}/")
        click.echo(f"- {input_name}_report.txt (analysis)")
        click.echo(f"- {input_name}_sample.* (sample data)")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _parse_filter_expression(expr: str):
    """Parse filter expression into filter function."""
    # Simple parser for common filter patterns
    # Format: "field operator value"
    
    # Handle comparison operators
    for op in ['>=', '<=', '!=', '==', '>', '<']:
        if op in expr:
            field, value = expr.split(op, 1)
            field = field.strip()
            value = value.strip().strip('"\'')
            
            # Try to convert value to appropriate type
            try:
                if '.' in value:
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                pass  # Keep as string
            
            if op == '==':
                return filters.equals(field, value)
            elif op == '!=':
                return filters.not_filter(filters.equals(field, value))
            elif op == '>':
                return filters.greater_than(field, value)
            elif op == '>=':
                return filters.greater_than_or_equal(field, value)
            elif op == '<':
                return filters.less_than(field, value)
            elif op == '<=':
                return filters.less_than_or_equal(field, value)
    
    # Handle contains
    if ' contains ' in expr:
        field, value = expr.split(' contains ', 1)
        return filters.contains(field.strip(), value.strip().strip('"\''))
    
    # Handle starts with
    if ' starts with ' in expr:
        field, value = expr.split(' starts with ', 1)
        return filters.starts_with(field.strip(), value.strip().strip('"\''))
    
    # Handle ends with
    if ' ends with ' in expr:
        field, value = expr.split(' ends with ', 1)
        return filters.ends_with(field.strip(), value.strip().strip('"\''))
    
    # Handle null checks
    if expr.strip().endswith(' is null'):
        field = expr.replace(' is null', '').strip()
        return filters.is_null(field)
    
    if expr.strip().endswith(' is not null'):
        field = expr.replace(' is not null', '').strip()
        return filters.is_not_null(field)
    
    raise ValueError(f"Cannot parse filter expression: {expr}")


def _parse_map_expression(expr: str):
    """Parse map expression into transform function."""
    # Format: "operation:field" or "operation:field:params"
    
    parts = expr.split(':')
    operation = parts[0].strip()
    
    if len(parts) < 2:
        raise ValueError(f"Map expression must specify field: {expr}")
    
    field = parts[1].strip()
    
    if operation == 'capitalize':
        return transforms.capitalize_field(field)
    elif operation == 'upper':
        return transforms.upper_field(field)
    elif operation == 'lower':
        return transforms.lower_field(field)
    elif operation == 'strip':
        return transforms.strip_field(field)
    elif operation == 'remove':
        return transforms.remove_field(field)
    elif operation == 'multiply' and len(parts) >= 3:
        factor = float(parts[2])
        return transforms.multiply_field(field, factor)
    elif operation == 'add' and len(parts) >= 3:
        value = float(parts[2])
        return transforms.add_to_field(field, value)
    elif operation == 'round' and len(parts) >= 3:
        decimals = int(parts[2])
        return transforms.round_field(field, decimals)
    elif operation == 'cast' and len(parts) >= 3:
        type_name = parts[2].lower()
        if type_name == 'int':
            return transforms.cast_field(field, int)
        elif type_name == 'float':
            return transforms.cast_field(field, float)
        elif type_name == 'str':
            return transforms.cast_field(field, str)
        else:
            raise ValueError(f"Unsupported cast type: {type_name}")
    elif operation == 'replace' and len(parts) >= 4:
        old_val = parts[2]
        new_val = parts[3]
        return transforms.replace_in_field(field, old_val, new_val)
    
    raise ValueError(f"Cannot parse map expression: {expr}")


def _parse_sort_expression(expr: str):
    """Parse sort expression into key function and reverse flag."""
    parts = expr.split(':')
    field = parts[0].strip()
    reverse = len(parts) > 1 and parts[1].strip().lower() in ['desc', 'descending']
    
    def key_func(item):
        return item.get(field)
    
    return key_func, reverse


@cli.command()
@click.argument('input_files', nargs=-1, type=click.Path(exists=True))
@click.option('--output', '-o', required=True, help='Output file path')
@click.option('--format', '-f', type=click.Choice(['json', 'csv', 'tsv']),
              help='Output format')
def merge(input_files: List[str], output: str, format: str):
    """Merge multiple data files into one."""
    try:
        all_data = []
        
        for file_path in input_files:
            data = readers.auto_read(file_path)
            all_data.extend(data)
            click.echo(f"Loaded {len(data)} records from {file_path}")
        
        # Write merged data
        if format:
            if format == 'json':
                writers.write_json(all_data, output)
            elif format == 'csv':
                writers.write_csv(all_data, output)
            elif format == 'tsv':
                writers.write_tsv(all_data, output)
        else:
            writers.auto_write(all_data, output)
        
        click.echo(f"Merged {len(all_data)} total records -> {output}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('field_name')
@click.option('--output-dir', '-o', required=True, help='Output directory')
@click.option('--format', '-f', type=click.Choice(['json', 'csv', 'tsv']),
              help='Output format')
def split(input_file: str, field_name: str, output_dir: str, format: str):
    """Split data file by unique values in a field."""
    try:
        data = readers.auto_read(input_file)
        
        # Group by field values
        groups = {}
        for item in data:
            value = item.get(field_name, 'unknown')
            if value not in groups:
                groups[value] = []
            groups[value].append(item)
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Write each group to separate file
        input_name = Path(input_file).stem
        ext = '.json' if not format else f'.{format}'
        
        for value, group_data in groups.items():
            # Sanitize filename
            safe_value = str(value).replace('/', '_').replace('\\', '_')
            filename = f"{input_name}_{field_name}_{safe_value}{ext}"
            filepath = output_path / filename
            
            if format == 'json' or (not format and ext == '.json'):
                writers.write_json(group_data, str(filepath))
            elif format == 'csv' or (not format and ext == '.csv'):
                writers.write_csv(group_data, str(filepath))
            elif format == 'tsv' or (not format and ext == '.tsv'):
                writers.write_tsv(group_data, str(filepath))
            
            click.echo(f"{value}: {len(group_data)} records -> {filename}")
        
        click.echo(f"Split into {len(groups)} files in {output_dir}/")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def main():
    """Main entry point for CLI."""
    cli()


if __name__ == '__main__':
    main()
