from loguru import logger
import sys
from pathlib import Path

LOG_DIR = Path.home() / ".cache" / "projector_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger.remove()  # clear default handler
logger.add(sys.stderr, level="INFO", backtrace=True, diagnose=True)
logger.add(
    LOG_DIR / "projector.log",
    rotation="10 MB",
    retention="7 days",
    compression="zip",
    level="DEBUG",
)

__all__ = ["logger"]
