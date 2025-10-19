import json
import logging
import sys
from datetime import datetime

from config.settings import settings


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }

        # 添加异常信息（如果存在）
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # 添加自定义字段（通过 logger.info("msg", extra={"user_id": 123})）
        for key, value in record.__dict__.items():
            if key not in logging.LogRecord(
                "", 0, "", 0, "", (), None
            ).__dict__ and not key.startswith("_"):
                log_entry[key] = value

        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(log_level: str):
    # 避免重复添加 handler（尤其在 Jupyter 或 reload 时）
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        handlers=[handler],
        force=True,  # Python 3.8+ 支持 force，确保覆盖已有配置
    )


# 使用
setup_logging(settings.log_level)
logger = logging.getLogger(__name__)
