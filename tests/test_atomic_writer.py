"""
Tests for Claude Usage Monitor atomic file writer.

This module tests the atomic write operations.
"""

import pytest
import json
import tempfile
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.shared.atomic_writer import (
    atomic_write,
    atomic_write_json,
    safe_read_json
)


class TestAtomicWrite:
    """Test atomic write context manager."""

    def test_atomic_write_creates_file(self, tmp_path):
        """Test that atomic write creates a file."""
        test_file = tmp_path / "test.txt"

        with atomic_write(test_file, mode='w') as f:
            f.write("Hello, world!")

        assert test_file.exists()
        with open(test_file, 'r') as f:
            content = f.read()
        assert content == "Hello, world!"

    def test_atomic_write_overwrites(self, tmp_path):
        """Test that atomic write can overwrite existing file."""
        test_file = tmp_path / "test.txt"

        # Create initial file
        with open(test_file, 'w') as f:
            f.write("Original content")

        # Overwrite
        with atomic_write(test_file, mode='w', overwrite=True) as f:
            f.write("New content")

        with open(test_file, 'r') as f:
            content = f.read()
        assert content == "New content"

    def test_atomic_write_no_overwrite_raises(self, tmp_path):
        """Test that atomic write raises if file exists and overwrite=False."""
        test_file = tmp_path / "test.txt"

        # Create initial file
        with open(test_file, 'w') as f:
            f.write("Original content")

        # Attempt to write without overwrite
        with pytest.raises(FileExistsError):
            with atomic_write(test_file, mode='w', overwrite=False) as f:
                f.write("New content")

    def test_atomic_write_creates_parent_directory(self, tmp_path):
        """Test that atomic write creates parent directories."""
        test_file = tmp_path / "subdir" / "test.txt"

        with atomic_write(test_file, mode='w') as f:
            f.write("Content")

        assert test_file.exists()

    def test_atomic_write_cleans_up_on_error(self, tmp_path):
        """Test that atomic write cleans up temp file on error."""
        test_file = tmp_path / "test.txt"

        # Get initial file count
        initial_files = list(tmp_path.glob('*'))

        try:
            with atomic_write(test_file, mode='w') as f:
                f.write("Content")
                raise ValueError("Simulated error")
        except ValueError:
            pass

        # Target file should not exist
        assert not test_file.exists()

        # No temp files should remain
        final_files = list(tmp_path.glob('*'))
        assert len(final_files) == len(initial_files)


class TestAtomicWriteJSON:
    """Test atomic JSON write function."""

    def test_atomic_write_json_creates_file(self, tmp_path):
        """Test that atomic JSON write creates a valid JSON file."""
        test_file = tmp_path / "test.json"
        data = {'key': 'value', 'number': 42}

        atomic_write_json(test_file, data)

        assert test_file.exists()
        with open(test_file, 'r') as f:
            loaded = json.load(f)
        assert loaded == data

    def test_atomic_write_json_formats_nicely(self, tmp_path):
        """Test that atomic JSON write formats with indentation."""
        test_file = tmp_path / "test.json"
        data = {'key': 'value'}

        atomic_write_json(test_file, data, indent=2)

        with open(test_file, 'r') as f:
            content = f.read()
        assert '\n' in content  # Should be formatted
        assert '  ' in content  # Should have indentation


class TestSafeReadJSON:
    """Test safe JSON read function."""

    def test_safe_read_json_reads_valid_file(self, tmp_path):
        """Test that safe read reads a valid JSON file."""
        test_file = tmp_path / "test.json"
        data = {'key': 'value', 'number': 42}

        with open(test_file, 'w') as f:
            json.dump(data, f)

        loaded = safe_read_json(test_file)
        assert loaded == data

    def test_safe_read_json_missing_file_returns_default(self, tmp_path):
        """Test that safe read returns default for missing file."""
        test_file = tmp_path / "nonexistent.json"

        loaded = safe_read_json(test_file)
        assert loaded == {}

        loaded = safe_read_json(test_file, default={'default': 'value'})
        assert loaded == {'default': 'value'}

    def test_safe_read_json_corrupted_returns_default(self, tmp_path):
        """Test that safe read returns default for corrupted JSON."""
        test_file = tmp_path / "corrupted.json"

        with open(test_file, 'w') as f:
            f.write("{ invalid json }")

        loaded = safe_read_json(test_file)
        assert loaded == {}

        loaded = safe_read_json(test_file, default={'fallback': 'data'})
        assert loaded == {'fallback': 'data'}


class TestAtomicWriteIntegration:
    """Test atomic write integration scenarios."""

    def test_atomic_write_prevents_corruption(self, tmp_path):
        """Test that atomic write prevents partial writes."""
        test_file = tmp_path / "test.json"
        initial_data = {'version': 1}

        # Write initial data
        atomic_write_json(test_file, initial_data)

        # Attempt to write new data but fail
        try:
            with atomic_write(test_file, mode='w') as f:
                json.dump({'version': 2}, f)
                raise RuntimeError("Simulated failure")
        except RuntimeError:
            pass

        # Original data should still be readable
        loaded = safe_read_json(test_file)
        assert loaded == initial_data

    def test_concurrent_write_safety(self, tmp_path):
        """Test that atomic writes don't interfere with each other."""
        test_file = tmp_path / "test.json"

        # Multiple writes in sequence
        for i in range(5):
            atomic_write_json(test_file, {'version': i})

        # Final data should be version 4
        loaded = safe_read_json(test_file)
        assert loaded == {'version': 4}
