import logging

from system_logs.services import exception_payload, log_system_event, sanitize_context


class DatabaseLogHandler(logging.Handler):
    def emit(self, record):
        try:
            exception_type = ""
            stack_trace = ""
            if record.exc_info:
                exc = record.exc_info[1]
                exception_type, stack_trace = exception_payload(exc)
            extra = {}
            for key, value in record.__dict__.items():
                if key in {
                    "name",
                    "msg",
                    "args",
                    "levelname",
                    "levelno",
                    "pathname",
                    "filename",
                    "module",
                    "exc_info",
                    "exc_text",
                    "stack_info",
                    "lineno",
                    "funcName",
                    "created",
                    "msecs",
                    "relativeCreated",
                    "thread",
                    "threadName",
                    "processName",
                    "process",
                }:
                    continue
                extra[key] = value
            log_system_event(
                level=record.levelname,
                source="python",
                logger_name=record.name,
                event_type="logging",
                message=self.format(record),
                request_id=str(getattr(record, "request_id", "") or ""),
                exception_type=exception_type,
                stack_trace=stack_trace,
                context={
                    "module": record.module,
                    "path": record.pathname,
                    "line": record.lineno,
                    "function": record.funcName,
                    "extra": sanitize_context(extra),
                },
            )
        except Exception:
            self.handleError(record)
