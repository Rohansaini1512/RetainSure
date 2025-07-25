import re
import string
import random
from urllib.parse import urlparse
from typing import Optional

def is_valid_url(url: str) -> bool:
    """
    Validate if a URL is properly formatted.
    
    Args:
        url: The URL to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    # Basic URL pattern validation
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if not url_pattern.match(url):
        return False
    
    # Additional validation using urlparse
    try:
        parsed = urlparse(url)
        return all([parsed.scheme, parsed.netloc])
    except Exception:
        return False

def generate_short_code(length: int = 6) -> str:
    """
    Generate a random short code.
    
    Args:
        length: Length of the short code (default: 6)
        
    Returns:
        Random alphanumeric string
    """
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def generate_unique_short_code(existing_codes_checker, max_attempts: int = 100) -> Optional[str]:
    """
    Generate a unique short code that doesn't exist in the store.
    
    Args:
        existing_codes_checker: Function that checks if a code exists
        max_attempts: Maximum number of attempts to generate unique code
        
    Returns:
        Unique short code or None if failed to generate
    """
    for _ in range(max_attempts):
        code = generate_short_code()
        if not existing_codes_checker(code):
            return code
    return None

def normalize_url(url: str) -> str:
    """
    Normalize URL by ensuring it has a proper scheme.
    
    Args:
        url: The URL to normalize
        
    Returns:
        Normalized URL with proper scheme
    """
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url