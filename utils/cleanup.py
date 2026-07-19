import os
from typing import Optional
from utils.logger import logger


def safe_delete(*paths: Optional[str]) -> None:
    """Deletes local temp/download files, never raises."""
    for path in paths:
        if not path:
            continue
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception as e:
            logger.warning(f"Cleanup failed for {path}: {e}")
