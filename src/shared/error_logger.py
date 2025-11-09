# src/shared/error_logger.py
"""
Error logging utilities.

Provides structured error logging with context and timestamps.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class ErrorLogger:
    """Structured error logger."""

    def __init__(self, log_file: str = 'logs/errors.log'):
        """
        Initialize error logger.

        Args:
            log_file: Path to log file
        """
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )

        self.logger = logging.getLogger('ClaudeMonitor')

    def log_error(self, error: Exception, context: Dict[str, Any] = None) -> None:
        """
        Log error with context.

        Args:
            error: Exception object
            context: Additional context information
        """
        context_str = f' | Context: {context}' if context else ''
        self.logger.error(f'{type(error).__name__}: {error}{context_str}')

    def log_warning(self, message: str, context: Dict[str, Any] = None) -> None:
        """Log warning message."""
        context_str = f' | Context: {context}' if context else ''
        self.logger.warning(f'{message}{context_str}')

    def log_info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)
