"""
Local storage implementation that saves files to a local directory and data to a JSON file.
"""

import os
import json
from typing import Dict, Any

from .base import BaseStorage

class LocalStorage(BaseStorage):
    """Local storage client for saving files and structured data."""

    def __init__(self, upload_dir: str = "local_uploads", db_file: str = "local_db.json"):
        self.upload_dir = upload_dir
        self.db_file = db_file

        # Create upload directory if it doesn't exist
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)

        # Create db file if it doesn't exist
        if not os.path.exists(self.db_file):
            with open(self.db_file, 'w') as f:
                json.dump({}, f)

    def save_file(self, file_name: str, content: bytes) -> str:
        """
        Saves a file to the local filesystem.

        :param file_name: The name of the file to save.
        :param content: The file content in bytes.
        :return: The local path to the saved file.
        """
        file_path = os.path.join(self.upload_dir, file_name)
        with open(file_path, 'wb') as f:
            f.write(content)
        return file_path

    def save_job_data(self, job_id: str, data: Dict[str, Any]) -> None:
        """
        Saves structured job data to a local JSON file.

        :param job_id: The unique identifier for the job.
        :param data: The structured data to save.
        """
        with open(self.db_file, 'r+') as f:
            db_data = json.load(f)
            db_data[job_id] = data
            f.seek(0)
            json.dump(db_data, f, indent=4)
            f.truncate()

    def load_job_data(self, job_id: str) -> Dict[str, Any]:
        """
        Loads structured job data from a local JSON file.

        :param job_id: The unique identifier for the job.
        :return: The loaded data or an empty dict if not found.
        """
        try:
            with open(self.db_file, 'r') as f:
                db_data = json.load(f)
                return db_data.get(job_id, {})
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
