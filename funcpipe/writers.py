"""
Data writers for various output formats.

Pure functional approach to writing processed data.
"""

from typing import Dict, List, Any, Optional
import json
import csv
from pathlib import Path


def write_json(data: List[Dict[str, Any]], filepath: str, indent: int = 2) -> None:
    """
    Write data to JSON file.
    
    Args:
        data: List of dictionaries to write
        filepath: Output file path
        indent: JSON indentation level
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def write_csv(data: List[Dict[str, Any]], filepath: str, 
              delimiter: str = ',') -> None:
    """
    Write data to CSV file.
    
    Args:
        data: List of dictionaries to write
        filepath: Output file path
        delimiter: Field delimiter
    """
    if not data:
        return
    
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Get all unique field names from all records
    fieldnames = set()
    for item in data:
        fieldnames.update(item.keys())
    fieldnames = sorted(list(fieldnames))
    
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(data)


def write_tsv(data: List[Dict[str, Any]], filepath: str) -> None:
    """
    Write data to TSV file.
    
    Args:
        data: List of dictionaries to write
        filepath: Output file path
    """
    write_csv(data, filepath, delimiter='\t')


def write_text_lines(data: List[Dict[str, Any]], filepath: str, 
                    line_field: str = 'line') -> None:
    """
    Write data to text file (one line per record).
    
    Args:
        data: List of dictionaries to write
        filepath: Output file path
        line_field: Field containing line content
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        for item in data:
            line = str(item.get(line_field, ''))
            f.write(line + '\n')


def write_pretty_table(data: List[Dict[str, Any]], filepath: str,
                      max_width: int = 20) -> None:
    """
    Write data as formatted table to text file.
    
    Args:
        data: List of dictionaries to write
        filepath: Output file path
        max_width: Maximum column width
    """
    if not data:
        return
    
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Get all field names
    fieldnames = set()
    for item in data:
        fieldnames.update(item.keys())
    fieldnames = sorted(list(fieldnames))
    
    # Calculate column widths
    widths = {}
    for field in fieldnames:
        widths[field] = min(max_width, max(
            len(field),
            max(len(str(item.get(field, ''))) for item in data)
        ))
    
    with open(path, 'w', encoding='utf-8') as f:
        # Write header
        header_row = ' | '.join(field.ljust(widths[field]) for field in fieldnames)
        f.write(header_row + '\n')
        
        # Write separator
        separator = '-+-'.join('-' * widths[field] for field in fieldnames)
        f.write(separator + '\n')
        
        # Write data rows
        for item in data:
            row = ' | '.join(
                str(item.get(field, '')).ljust(widths[field])[:widths[field]]
                for field in fieldnames
            )
            f.write(row + '\n')


def auto_write(data: List[Dict[str, Any]], filepath: str) -> None:
    """
    Automatically detect output format from file extension and write data.
    
    Args:
        data: List of dictionaries to write
        filepath: Output file path
        
    Raises:
        ValueError: If file format not supported
    """
    path = Path(filepath)
    suffix = path.suffix.lower()
    
    if suffix == '.json':
        write_json(data, filepath)
    elif suffix == '.csv':
        write_csv(data, filepath)
    elif suffix == '.tsv':
        write_tsv(data, filepath)
    elif suffix == '.txt':
        write_text_lines(data, filepath)
    else:
        raise ValueError(f"Unsupported output format: {suffix}")


def print_sample(data: List[Dict[str, Any]], n: int = 5) -> None:
    """
    Print first n records to console for inspection.
    
    Args:
        data: List of dictionaries to display
        n: Number of records to print
    """
    if not data:
        print("No data to display")
        return
    
    print(f"Showing {min(n, len(data))} of {len(data)} records:")
    print("-" * 50)
    
    for i, item in enumerate(data[:n]):
        print(f"Record {i + 1}:")
        for key, value in item.items():
            print(f"  {key}: {value}")
        print()


def print_summary(data: List[Dict[str, Any]]) -> None:
    """
    Print summary statistics about the data.
    
    Args:
        data: List of dictionaries to analyze
    """
    if not data:
        print("No data to summarize")
        return
    
    # Get all field names and types
    field_info = {}
    for item in data:
        for key, value in item.items():
            if key not in field_info:
                field_info[key] = {
                    'count': 0,
                    'null_count': 0,
                    'types': set()
                }
            
            field_info[key]['count'] += 1
            if value is None or value == '':
                field_info[key]['null_count'] += 1
            field_info[key]['types'].add(type(value).__name__)
    
    print(f"Dataset Summary:")
    print(f"Records: {len(data)}")
    print(f"Fields: {len(field_info)}")
    print("-" * 50)
    
    for field, info in sorted(field_info.items()):
        null_pct = (info['null_count'] / len(data)) * 100
        types_str = ', '.join(sorted(info['types']))
        print(f"{field}:")
        print(f"  Types: {types_str}")
        print(f"  Nulls: {info['null_count']} ({null_pct:.1f}%)")
        print()


def write_report(data: List[Dict[str, Any]], filepath: str, 
                include_sample: bool = True, sample_size: int = 10) -> None:
    """
    Write comprehensive data report to text file.
    
    Args:
        data: List of dictionaries to report on
        filepath: Output file path
        include_sample: Whether to include sample records
        sample_size: Number of sample records to include
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        # Write header
        f.write("Data Processing Report\n")
        f.write("=" * 50 + "\n\n")
        
        # Write summary
        f.write(f"Total Records: {len(data)}\n")
        
        if not data:
            f.write("No data to report.\n")
            return
        
        # Field analysis
        field_info = {}
        for item in data:
            for key, value in item.items():
                if key not in field_info:
                    field_info[key] = {
                        'count': 0,
                        'null_count': 0,
                        'types': set(),
                        'sample_values': []
                    }
                
                field_info[key]['count'] += 1
                if value is None or value == '':
                    field_info[key]['null_count'] += 1
                field_info[key]['types'].add(type(value).__name__)
                
                # Collect sample values
                if len(field_info[key]['sample_values']) < 3:
                    field_info[key]['sample_values'].append(str(value)[:50])
        
        f.write(f"Total Fields: {len(field_info)}\n\n")
        
        # Write field details
        f.write("Field Details:\n")
        f.write("-" * 30 + "\n")
        
        for field, info in sorted(field_info.items()):
            null_pct = (info['null_count'] / len(data)) * 100
            types_str = ', '.join(sorted(info['types']))
            samples_str = ', '.join(info['sample_values'])
            
            f.write(f"{field}:\n")
            f.write(f"  Types: {types_str}\n")
            f.write(f"  Nulls: {info['null_count']} ({null_pct:.1f}%)\n")
            f.write(f"  Samples: {samples_str}\n\n")
        
        # Write sample data
        if include_sample:
            f.write("Sample Records:\n")
            f.write("-" * 30 + "\n")
            
            for i, item in enumerate(data[:sample_size]):
                f.write(f"Record {i + 1}:\n")
                for key, value in item.items():
                    f.write(f"  {key}: {value}\n")
                f.write("\n")
