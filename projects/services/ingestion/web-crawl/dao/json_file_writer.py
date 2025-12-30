"""
JSON File Writer - Saves crawl data to JSON files in projects/data/.

Provides dual storage alongside PostgreSQL for easy data access.
"""
import os
import json
from datetime import datetime
from typing import Optional


class JsonFileWriter:
    """Writes crawl data to JSON files for backup and easy access."""
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize JSON file writer.
        
        Args:
            base_path: Base path for JSON storage. 
                      Defaults to projects/data/ingestion/web-crawl/
        """
        if base_path is None:
            # Navigate from dao -> web-crawl -> ingestion -> services -> projects
            current_dir = os.path.dirname(os.path.abspath(__file__))
            projects_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
            base_path = os.path.join(projects_dir, "data", "ingestion", "web-crawl")
        
        self.base_path = base_path
        self.history_dir = os.path.join(base_path, "crawl_history")
        self.result_dir = os.path.join(base_path, "crawl_result")
        
        # Ensure directories exist
        os.makedirs(self.history_dir, exist_ok=True)
        os.makedirs(self.result_dir, exist_ok=True)
    
    def save_history(self, request_id: str, data: dict) -> str:
        """
        Save crawl history to JSON file.
        
        Args:
            request_id: Unique request ID
            data: History data dictionary
            
        Returns:
            Path to saved file
        """
        filepath = os.path.join(self.history_dir, f"{request_id}.json")
        self._save_json(filepath, data)
        return filepath
    
    def save_result(self, request_id: str, data: dict) -> str:
        """
        Save crawl result to JSON file.
        
        Args:
            request_id: Unique request ID
            data: Result data dictionary
            
        Returns:
            Path to saved file
        """
        filepath = os.path.join(self.result_dir, f"{request_id}.json")
        self._save_json(filepath, data)
        return filepath
    
    def get_history(self, request_id: str) -> Optional[dict]:
        """Load crawl history from JSON file."""
        filepath = os.path.join(self.history_dir, f"{request_id}.json")
        return self._load_json(filepath)
    
    def get_result(self, request_id: str) -> Optional[dict]:
        """Load crawl result from JSON file."""
        filepath = os.path.join(self.result_dir, f"{request_id}.json")
        return self._load_json(filepath)
    
    def _save_json(self, filepath: str, data: dict):
        """Save data to JSON file with proper encoding."""
        # Convert datetime objects to ISO format strings
        serializable_data = self._make_serializable(data)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(serializable_data, f, indent=2, ensure_ascii=False)
    
    def _load_json(self, filepath: str) -> Optional[dict]:
        """Load data from JSON file if it exists."""
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _make_serializable(self, obj):
        """Convert non-serializable objects to serializable format."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        else:
            return obj
