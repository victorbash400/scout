"""
Base class for storage clients
"""
from abc import ABC, abstractmethod

class BaseStorage(ABC):
    """Abstract base class for storage operations."""

    @abstractmethod
    def save_file(self, file_path: str, content: bytes) -> str:
        """
        Saves a file to the storage backend.
        
        :param file_path: The path where the file should be saved.
        :param content: The file content in bytes.
        :return: The path or URI to the saved file.
        """
        pass

    @abstractmethod
    def save_job_data(self, job_id: str, data: dict) -> None:
        """
        Saves structured job data.
        
        :param job_id: The unique identifier for the job.
        :param data: The structured data (e.g., research brief) to save.
        """
        pass

    @abstractmethod
    def load_job_data(self, job_id: str) -> dict:
        """
        Loads structured job data.
        
        :param job_id: The unique identifier for the job.
        :return: The loaded data.
        """
        pass
