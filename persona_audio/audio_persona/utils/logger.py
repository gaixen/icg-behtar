"""Logging configuration and utilities"""
import logging
from datetime import datetime


class Logger:
    """Handles logging configuration and operations"""

    @staticmethod
    def setup(session_id: str) -> logging.Logger:
        """
        Setup logging with file handler

        Args:
            session_id: Identifier for the logging session

        Returns:
            Configured logger instance
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(f"session_{timestamp}.log")],
        )
        return logging.getLogger(session_id)
