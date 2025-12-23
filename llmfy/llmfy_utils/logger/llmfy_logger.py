import logging
import sys
from pathlib import Path


class LLMfyLogger:
    """
    Reusable colored logger with optional file logging.

    Example:
        logger = LLMfyLogger(__name__, use_log_file=True).get_logger()
        logger.info("Application started successfully")
    """

    LOG_DIR = Path("logs")
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[1;31m",  # Bold Red
        "RESET": "\033[0m",  # Reset
    }

    def __init__(
        self,
        name: str,
        use_log_file: bool = False,
        use_line_no: bool = False,
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False  # Prevent logs from going to root logger
        self.use_log_file = use_log_file
        self.use_line_no = use_line_no

        # Clear existing handlers to prevent duplicates when re-instantiated
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        self._configure_logger()

    def _configure_logger(self):
        # Console Handler (Colorized + aligned)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)

        class ColorFormatter(logging.Formatter):
            MAX_LEVEL_WIDTH = max(
                len(lvl) for lvl in LLMfyLogger.COLORS if lvl != "RESET"
            )

            def format(self, record):
                color = LLMfyLogger.COLORS.get(record.levelname, "")
                reset = LLMfyLogger.COLORS["RESET"]
                # Format levelname with colon and padding (e.g., INFO:     )
                padded_level = f"{record.levelname + ':':<{self.MAX_LEVEL_WIDTH + 1}}"
                record.levelname = f"{color}{padded_level}{reset}"
                record.msg = f"{color}{record.msg}{reset}"
                return super().format(record)

        if self.use_line_no:
            console_formatter = ColorFormatter(
                fmt="%(levelname)-8s %(name)s:%(lineno)d | %(asctime)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        else:
            console_formatter = ColorFormatter(
                fmt="%(levelname)-8s %(name)s | %(asctime)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # File Handlers (Optional)
        if self.use_log_file:
            self.LOG_DIR.mkdir(exist_ok=True)
            level_files = {
                "DEBUG": "debug.log",
                "INFO": "info.log",
                "WARNING": "warning.log",
                "ERROR": "error.log",
                "CRITICAL": "critical.log",
            }

            for level_name, filename in level_files.items():
                handler = logging.FileHandler(self.LOG_DIR / filename, encoding="utf-8")
                handler.setLevel(getattr(logging, level_name))
                if self.use_line_no:
                    file_formatter = logging.Formatter(
                        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S",
                    )
                else:
                    file_formatter = logging.Formatter(
                        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S",
                    )
                handler.setFormatter(file_formatter)
                self.logger.addHandler(handler)

    def get_logger(self) -> logging.Logger:
        """Return the configured logger instance."""
        return self.logger
