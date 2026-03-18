import logging
from typing import Dict, List, Any, Union, Optional
import traceback

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Utility class for handling common errors in the application"""
    
    @staticmethod
    def handle_api_response(response, default_value=None):
        """
        Safely handle API responses with proper error handling
        
        Args:
            response: The API response object
            default_value: Value to return if response processing fails
            
        Returns:
            Processed response data or default_value on error
        """
        try:
            # Check for HTTP errors
            if hasattr(response, 'status_code') and response.status_code != 200:
                logger.error(f"API error: {response.status_code} - {response.text if hasattr(response, 'text') else 'No response text'}")
                return default_value
                
            # Try to parse JSON
            if hasattr(response, 'json'):
                data = response.json()
                return data
            return response
        except Exception as e:
            logger.error(f"Error handling API response: {str(e)}")
            return default_value
    
    @staticmethod
    def safe_get(data: Dict, key_path: str, default=None) -> Any:
        """
        Safely access nested dictionary keys without raising KeyError
        
        Args:
            data: Dictionary to access
            key_path: Path to the key, using dot notation (e.g., "user.profile.name")
            default: Default value if key doesn't exist
            
        Returns:
            Value at key_path or default if not found
        """
        if not data:
            return default
            
        keys = key_path.split('.')
        result = data
        
        try:
            for key in keys:
                if isinstance(result, dict):
                    result = result.get(key, default)
                else:
                    return default
            return result
        except Exception:
            return default
    
    @staticmethod
    def format_exception() -> str:
        """
        Format the current exception into a readable string with traceback
        
        Returns:
            Formatted exception string
        """
        return traceback.format_exc()