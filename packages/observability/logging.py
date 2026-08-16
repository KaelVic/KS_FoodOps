import logging
import json
import contextvars
from datetime import datetime, timezone
from uuid import uuid4

# Contextvars for structured logging
request_id_ctx_var = contextvars.ContextVar('request_id', default=None)
tenant_id_ctx_var = contextvars.ContextVar('tenant_id', default=None)

class JSONLogFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.name,
            "request_id": request_id_ctx_var.get(),
            "tenant_id": tenant_id_ctx_var.get(),
        }
        
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_record)

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Remove all existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        
    handler = logging.StreamHandler()
    handler.setFormatter(JSONLogFormatter())
    logger.addHandler(handler)
