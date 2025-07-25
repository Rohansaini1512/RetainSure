from datetime import datetime, timezone
import threading
from typing import Dict, Optional

class URLMapping:
    """Represents a URL mapping with metadata."""
    
    def __init__(self, original_url: str, short_code: str):
        self.original_url = original_url
        self.short_code = short_code
        self.clicks = 0
        self.created_at = datetime.now(timezone.utc)
        self._lock = threading.Lock()
    
    def increment_clicks(self):
        """Thread-safe increment of click count."""
        with self._lock:
            self.clicks += 1
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'url': self.original_url,
            'short_code': self.short_code,
            'clicks': self.clicks,
            'created_at': self.created_at.isoformat()
        }

class URLStore:
    """Thread-safe in-memory store for URL mappings."""
    
    def __init__(self):
        self._mappings: Dict[str, URLMapping] = {}
        self._lock = threading.RLock()
    
    def add_mapping(self, original_url: str, short_code: str) -> URLMapping:
        """Add a new URL mapping."""
        with self._lock:
            mapping = URLMapping(original_url, short_code)
            self._mappings[short_code] = mapping
            return mapping
    
    def get_mapping(self, short_code: str) -> Optional[URLMapping]:
        """Get URL mapping by short code."""
        with self._lock:
            return self._mappings.get(short_code)
    
    def exists(self, short_code: str) -> bool:
        """Check if short code exists."""
        with self._lock:
            return short_code in self._mappings
    
    def get_all_mappings(self) -> Dict[str, URLMapping]:
        """Get all mappings (for testing purposes)."""
        with self._lock:
            return self._mappings.copy()

# Global store instance
url_store = URLStore()