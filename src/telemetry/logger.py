import logging
import json
import os
from datetime import datetime
from typing import Any, Dict

# Xác định thư mục logs tại src/logs (relative to project root)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DEFAULT_LOG_DIR = os.path.join(_PROJECT_ROOT, "src", "logs")


class IndustryLogger:
    """
    Structured logger that simulates industry practices.
    Logs to both console and a file in JSON format.
    
    Log files được lưu tại src/logs/ với format: YYYY-MM-DD.log
    Mỗi dòng log là 1 JSON object chứa: timestamp, event, data
    """
    def __init__(self, name: str = "AI-Lab-Agent", log_dir: str = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Tránh duplicate handlers khi import nhiều lần
        if self.logger.handlers:
            return
        
        log_dir = log_dir or _DEFAULT_LOG_DIR
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # File Handler (JSON)
        log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        
        # Console Handler
        console_handler = logging.StreamHandler()
        
        # Format cho console (ngắn gọn hơn)
        console_formatter = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S")
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def log_event(self, event_type: str, data: Dict[str, Any]):
        """
        Logs an event with a timestamp and type.
        Data sẽ được serialize thành JSON.
        Pydantic models trong data sẽ được convert tự động.
        """
        # Serialize data — handle Pydantic models và non-serializable types
        safe_data = self._make_serializable(data)
        
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event_type,
            "data": safe_data
        }
        self.logger.info(json.dumps(payload, ensure_ascii=False))

    def info(self, msg: str):
        self.logger.info(msg)

    def error(self, msg: str, exc_info=True):
        self.logger.error(msg, exc_info=exc_info)

    def _make_serializable(self, obj: Any) -> Any:
        """Recursively convert data to JSON-serializable format."""
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [self._make_serializable(item) for item in obj]
        # Handle Pydantic models
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        # Handle enums
        if hasattr(obj, "value"):
            return obj.value
        # Fallback
        try:
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            return str(obj)


# Global logger instance
logger = IndustryLogger()
