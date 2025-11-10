"""
Claude Usage Monitor - Atomic File Writer

Provides atomic file write operations to prevent data corruption during writes.

Reference: EPIC-01-STOR-03 (JSON Data Schema)
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Union, Optional
from contextlib import contextmanager


@contextmanager
def atomic_write(
    filepath: Union[str, Path],
    mode: str = 'w',
    encoding: str = 'utf-8',
    overwrite: bool = True
):
    """
    Context manager for atomic file writes.

    Writes to a temporary file first, then atomically renames it to the target path.
    This prevents corruption if the write is interrupted.

    Args:
        filepath: Target file path
        mode: File open mode (default 'w')
        encoding: File encoding (default 'utf-8')
        overwrite: Whether to overwrite existing file (default True)

    Yields:
        File handle for writing

    Example:
        with atomic_write('data.json') as f:
            json.dump(data, f)

    Raises:
        FileExistsError: If file exists and overwrite=False
        OSError: If atomic rename fails
    """
    filepath = Path(filepath)

    # Check if file exists and overwrite is disabled
    if filepath.exists() and not overwrite:
        raise FileExistsError(f"File already exists: {filepath}")

    # Create parent directory if it doesn't exist
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Create temporary file in same directory (ensures same filesystem for atomic rename)
    temp_fd, temp_path = tempfile.mkstemp(
        dir=filepath.parent,
        prefix=f'.tmp_{filepath.name}_',
        text='b' not in mode
    )

    try:
        # Close the file descriptor and reopen with proper mode
        os.close(temp_fd)

        # Open temp file for writing
        with open(temp_path, mode, encoding=encoding) as f:
            yield f

        # Atomic rename (POSIX guarantees atomicity)
        # On Windows, need to remove target first
        if os.name == 'nt' and filepath.exists():
            os.remove(filepath)

        shutil.move(temp_path, filepath)

    except Exception:
        # Clean up temp file on error
        try:
            os.remove(temp_path)
        except OSError:
            pass
        raise


def atomic_write_json(filepath: Union[str, Path], data: dict, indent: int = 2) -> None:
    """
    Atomically write JSON data to file.

    Args:
        filepath: Target file path
        data: Dictionary to write as JSON
        indent: JSON indentation (default 2)

    Example:
        atomic_write_json('data.json', {'key': 'value'})
    """
    import json

    with atomic_write(filepath, mode='w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent)


def safe_read_json(filepath: Union[str, Path], default: Optional[dict] = None) -> dict:
    """
    Safely read JSON file with fallback to default.

    Args:
        filepath: File path to read
        default: Default value if file doesn't exist or is corrupted

    Returns:
        Parsed JSON data or default value
    """
    import json

    filepath = Path(filepath)

    if not filepath.exists():
        return default if default is not None else {}

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        # File corrupted or read error
        return default if default is not None else {}
