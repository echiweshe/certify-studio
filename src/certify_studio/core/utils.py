"""
Core utilities for Certify Studio
Common helper functions used across the platform
"""

import re
import unicodedata
from typing import Any, Dict, List, Optional, Union
import hashlib
import json
from datetime import datetime


def clean_text(text: str) -> str:
    """
    Clean and normalize text for processing.
    
    Args:
        text: Raw text to clean
        
    Returns:
        Cleaned and normalized text
    """
    if not text:
        return ""
    
    # Normalize unicode characters
    text = unicodedata.normalize('NFKD', text)
    
    # Remove control characters and non-printable characters
    text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C')
    
    # Replace multiple whitespaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Fix common encoding issues
    replacements = {
        '"': '"',
        '"': '"',
        ''': "'",
        ''': "'",
        '–': '-',
        '—': '-',
        '…': '...',
        '\xa0': ' ',  # Non-breaking space
        '\u200b': '',  # Zero-width space
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file system usage.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove control characters
    filename = ''.join(char for char in filename if ord(char) >= 32)
    
    # Limit length
    name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
    if len(name) > 200:
        name = name[:200]
    
    return f"{name}.{ext}" if ext else name


def generate_hash(content: Union[str, bytes], algorithm: str = 'sha256') -> str:
    """
    Generate hash of content.
    
    Args:
        content: Content to hash
        algorithm: Hash algorithm to use
        
    Returns:
        Hex digest of hash
    """
    if isinstance(content, str):
        content = content.encode('utf-8')
    
    hasher = hashlib.new(algorithm)
    hasher.update(content)
    return hasher.hexdigest()


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to append if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def extract_urls(text: str) -> List[str]:
    """
    Extract URLs from text.
    
    Args:
        text: Text to search
        
    Returns:
        List of URLs found
    """
    url_pattern = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )
    return url_pattern.findall(text)


def extract_emails(text: str) -> List[str]:
    """
    Extract email addresses from text.
    
    Args:
        text: Text to search
        
    Returns:
        List of email addresses found
    """
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    return email_pattern.findall(text)


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def parse_bool(value: Any) -> bool:
    """
    Parse various representations of boolean values.
    
    Args:
        value: Value to parse
        
    Returns:
        Boolean value
    """
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        value = value.lower().strip()
        return value in ('true', 'yes', '1', 'on', 'enabled')
    
    return bool(value)


def deep_merge(dict1: Dict, dict2: Dict) -> Dict:
    """
    Deep merge two dictionaries.
    
    Args:
        dict1: Base dictionary
        dict2: Dictionary to merge
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename.
    
    Args:
        filename: Filename or path
        
    Returns:
        File extension (lowercase, without dot)
    """
    parts = filename.rsplit('.', 1)
    if len(parts) > 1:
        return parts[1].lower()
    return ""


def format_bytes(bytes_size: int) -> str:
    """
    Format bytes to human-readable size.
    
    Args:
        bytes_size: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


def create_timestamp() -> str:
    """
    Create ISO format timestamp.
    
    Returns:
        ISO format timestamp string
    """
    return datetime.utcnow().isoformat() + 'Z'


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    Safely load JSON with default on error.
    
    Args:
        json_str: JSON string
        default: Default value if parsing fails
        
    Returns:
        Parsed JSON or default
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split list into chunks of specified size.
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def remove_duplicates(lst: List[Any], key_func: Optional[callable] = None) -> List[Any]:
    """
    Remove duplicates from list while preserving order.
    
    Args:
        lst: List with potential duplicates
        key_func: Optional function to extract comparison key
        
    Returns:
        List without duplicates
    """
    seen = set()
    result = []
    
    for item in lst:
        key = key_func(item) if key_func else item
        if key not in seen:
            seen.add(key)
            result.append(item)
    
    return result


def get_nested_value(data: Dict, path: str, default: Any = None) -> Any:
    """
    Get value from nested dictionary using dot notation.
    
    Args:
        data: Dictionary to search
        path: Dot-separated path (e.g., 'user.profile.name')
        default: Default value if path not found
        
    Returns:
        Value at path or default
    """
    keys = path.split('.')
    current = data
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current


def set_nested_value(data: Dict, path: str, value: Any) -> None:
    """
    Set value in nested dictionary using dot notation.
    
    Args:
        data: Dictionary to modify
        path: Dot-separated path
        value: Value to set
    """
    keys = path.split('.')
    current = data
    
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value


# Export all utility functions
__all__ = [
    'clean_text',
    'sanitize_filename',
    'generate_hash',
    'truncate_text',
    'extract_urls',
    'extract_emails',
    'format_duration',
    'parse_bool',
    'deep_merge',
    'get_file_extension',
    'format_bytes',
    'create_timestamp',
    'safe_json_loads',
    'chunk_list',
    'remove_duplicates',
    'get_nested_value',
    'set_nested_value',
]
