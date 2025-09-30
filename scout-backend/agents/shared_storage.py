"""
Shared storage module for agent communication
"""
from typing import List
from threading import Lock

# Global storage for report file paths - shared between agents
report_filepaths_storage: List[str] = []

# Lock to ensure thread-safe access to the shared storage
storage_lock = Lock()