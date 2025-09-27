"module"

from typing import Dict, Any
import json
import os


def read_json_db(file_path: str) -> Dict[str, Any]:
    """Read a JSON file and return its contents as a dictionary.

    Args:
        file_path: path to the JSON file to read.

    Returns:
        Dictionary containing the parsed JSON data.

    Raises:
        FileNotFoundError: if the JSON file cannot be found.
        json.JSONDecodeError: if the file contains invalid JSON.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"JSON file not found at: {file_path}")

    with open(file_path, "r", encoding="utf-8") as fh:
        return json.load(fh)


__all__ = ["read_json_db"]
