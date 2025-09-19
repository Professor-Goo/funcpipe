"""
Data readers for various file formats.

Pure functional approach to reading data from files.
"""

from typing import Dict, List, Any, Optional
import json
import csv
from pathlib import Path


def read_json(filepath: str) -> List[Dict[str, Any]]:
    """
    Read JSON file and return list of dictionaries.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        List of dictionaries
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If invalid JSON
    """
    path = Path(filepath)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Ensure we return a list of dicts
    if isinstance(data, dict):
        return [data]
    elif isinstance(data, list):
        return data
    else:
        raise ValueError("JSON must contain object or array of objects")


def read_csv(filepath: str, delimiter: str = ',', 
             has_header: bool = True) -> List[Dict[str, Any]]:
    """
    Read CSV file and return list of dictionaries.
    
    Args:
        filepath: Path to CSV file
        delimiter: Field delimiter
        has_header: Whether first row contains headers
        
    Returns:
        List of dictionaries
        
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    path = Path(filepath)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    data = []
    
    with open(path, 'r', encoding='utf-8', newline='') as f:
        if has_header:
            reader = csv.DictReader(f, delimiter=delimiter)
            for row in reader:
                # Convert numeric strings to numbers where possible
                converted_row = {}
                for key, value in row.items():
                    converted_row[key] = _try_convert_numeric(value)
                data.append(converted_row)
        else:
            reader = csv.reader(f, delimiter=delimiter)
            headers = [f"column_{i}" for i in range(len(next(reader, [])))]
            f.seek(0)  # Reset to beginning
            
            for row in reader:
                converted_row = {}
                for i, value in enumerate(row):
                    if i < len(headers):
                        converted_row[headers[i]] = _try_convert_numeric(value)
                data.append(converted_row)
    
    return data


def read_tsv(filepath: str, has_header: bool = True) -> List[Dict[str, Any]]:
    """
    Read TSV (Tab-Separated Values) file.
    
    Args:
        filepath: Path to TSV file
        has_header: Whether first row contains headers
        
    Returns:
        List of dictionaries
    """
    return read_csv(filepath, delimiter='\t', has_header=has_header)


def read_text_lines(filepath: str, strip_empty: bool = True) -> List[Dict[str, Any]]:
    """
    Read text file as list of lines.
    
    Args:
        filepath: Path to text file
        strip_empty: Whether to remove empty lines
        
    Returns:
        List of dictionaries with 'line' field
    """
    path = Path(filepath)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    data = []
    for i, line in enumerate(lines):
        line = line.rstrip('\n\r')
        if strip_empty and not line.strip():
            continue
        data.append({
            'line_number': i + 1,
            'line': line
        })
    
    return data


def auto_read(filepath: str) -> List[Dict[str, Any]]:
    """
    Automatically detect file format and read data.
    
    Args:
        filepath: Path to data file
        
    Returns:
        List of dictionaries
        
    Raises:
        ValueError: If file format not supported
    """
    path = Path(filepath)
    suffix = path.suffix.lower()
    
    if suffix == '.json':
        return read_json(filepath)
    elif suffix == '.csv':
        return read_csv(filepath)
    elif suffix == '.tsv':
        return read_tsv(filepath)
    elif suffix == '.txt':
        return read_text_lines(filepath)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def _try_convert_numeric(value: str) -> Any:
    """
    Try to convert string value to numeric type.
    
    Args:
        value: String value to convert
        
    Returns:
        Converted value (int, float, or original string)
    """
    if not isinstance(value, str) or not value.strip():
        return value
    
    # Try integer conversion first
    try:
        return int(value)
    except ValueError:
        pass
    
    # Try float conversion
    try:
        return float(value)
    except ValueError:
        pass
    
    # Return original string if no conversion possible
    return value


def read_sample(filepath: str, n: int = 5) -> List[Dict[str, Any]]:
    """
    Read first n records from file for inspection.
    
    Args:
        filepath: Path to data file
        n: Number of records to read
        
    Returns:
        List of dictionaries (up to n items)
    """
    data = auto_read(filepath)
    return data[:n]


def get_file_info(filepath: str) -> Dict[str, Any]:
    """
    Get information about data file without reading all data.
    
    Args:
        filepath: Path to data file
        
    Returns:
        Dictionary with file information
    """
    path = Path(filepath)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    info = {
        'filename': path.name,
        'size_bytes': path.stat().st_size,
        'format': path.suffix.lower(),
    }
    
    # Try to get record count and field names
    try:
        sample = read_sample(filepath, 1)
        if sample:
            info['fields'] = list(sample[0].keys())
            info['field_count'] = len(sample[0])
        
        # For small files, get exact count
        if info['size_bytes'] < 1024 * 1024:  # 1MB
            full_data = auto_read(filepath)
            info['record_count'] = len(full_data)
        else:
            info['record_count'] = 'large_file'
            
    except Exception as e:
        info['error'] = str(e)
    
    return info
