"""
Browser Cache for Enhanced AbletonBridge MCP Server.
"""

import json
import os
import time
from typing import Any, Dict, List, Optional

from MCP_Server.constants import CACHE_EXPIRY_SECONDS, MAX_CACHE_SIZE_MB


class BrowserCache:
    """Cache for browser operations."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the browser cache.
        
        Args:
            cache_dir: Cache directory path
        """
        if cache_dir is None:
            cache_dir = os.path.join(os.path.expanduser("~"), ".enhanced-abletonbridge", "cache")
        
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._load_cache()
    
    def _load_cache(self):
        """Load cache from disk."""
        cache_file = os.path.join(self.cache_dir, "browser_cache.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    self._cache = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load browser cache: {e}")
                self._cache = {}
    
    def _save_cache(self):
        """Save cache to disk."""
        cache_file = os.path.join(self.cache_dir, "browser_cache.json")
        try:
            with open(cache_file, 'w') as f:
                json.dump(self._cache, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save browser cache: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry['timestamp'] < CACHE_EXPIRY_SECONDS:
                return entry['value']
            else:
                # Entry expired
                del self._cache[key]
                self._save_cache()
        
        return None
    
    def set(self, key: str, value: Any):
        """
        Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        self._cache[key] = {
            'value': value,
            'timestamp': time.time()
        }
        
        # Check cache size
        self._check_cache_size()
        self._save_cache()
    
    def delete(self, key: str):
        """
        Delete a value from cache.
        
        Args:
            key: Cache key
        """
        if key in self._cache:
            del self._cache[key]
            self._save_cache()
    
    def clear(self):
        """Clear the cache."""
        self._cache = {}
        self._save_cache()
    
    def _check_cache_size(self):
        """Check cache size and remove old entries if needed."""
        # Estimate cache size
        cache_json = json.dumps(self._cache)
        cache_size_mb = len(cache_json.encode('utf-8')) / (1024 * 1024)
        
        if cache_size_mb > MAX_CACHE_SIZE_MB:
            # Remove oldest entries
            sorted_keys = sorted(
                self._cache.keys(),
                key=lambda k: self._cache[k]['timestamp']
            )
            
            # Remove oldest 25% of entries
            remove_count = len(sorted_keys) // 4
            for key in sorted_keys[:remove_count]:
                del self._cache[key]
    
    def get_or_set(self, key: str, value_func, *args, **kwargs) -> Any:
        """
        Get a value from cache or set it if not found.
        
        Args:
            key: Cache key
            value_func: Function to generate value if not cached
            *args: Arguments for value_func
            **kwargs: Keyword arguments for value_func
            
        Returns:
            Cached or newly generated value
        """
        value = self.get(key)
        if value is None:
            value = value_func(*args, **kwargs)
            self.set(key, value)
        return value
    
    def has(self, key: str) -> bool:
        """
        Check if a key exists in cache (and is not expired).
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists and is not expired
        """
        return self.get(key) is not None
    
    def keys(self) -> List[str]:
        """
        Get all valid (non-expired) cache keys.
        
        Returns:
            List of cache keys
        """
        valid_keys = []
        current_time = time.time()
        
        for key, entry in self._cache.items():
            if current_time - entry['timestamp'] < CACHE_EXPIRY_SECONDS:
                valid_keys.append(key)
        
        return valid_keys
    
    @property
    def size(self) -> int:
        """Get the number of entries in cache."""
        return len(self._cache)
