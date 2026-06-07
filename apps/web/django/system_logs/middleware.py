import time

from apps.web.django.accounts.session import auth_user
from apps.web.django.system_logs.services import exception_payload, log_system_event, new_request_id, normalize_ip, request_headers


class SystemLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started_at = time.perf_counter()
        request_id = request.headers.get("x-request-id") or new_request_id()
        request.system_log_request_id = request_id
        session_user = auth_user(request) or {}
        user_id = session_user.get("id")
        if not user_id and getattr(request, "user", None) and request.user.is_authenticated:
            user_id = request.user.id
        ip_address = normalize_ip(request.META.get("HTTP_X_FORWARDED_FOR") or request.META.get("REMOTE_ADDR"))
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        try:
            response = self.get_response(request)
        except Exception as exc:
            duration_ms = int((time.perf_counter() - started_at) * 1000)
            exception_type, stack_trace = exception_payload(exc)
            log_system_event(
                level="ERROR",
                source="django",
                logger_name="django.request",
                event_type="request_exception",
                message=f"{request.method} {request.get_full_path()} raised {exception_type}",
                request_id=request_id,
                method=request.method,
                path=request.get_full_path(),
                status_code=500,
                duration_ms=duration_ms,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                exception_type=exception_type,
                stack_trace=stack_trace,
                context={"headers": request_headers(request.headers)},
            )
            raise
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        response["X-Request-ID"] = request_id
        status_code = getattr(response, "status_code", None)
        level = "ERROR" if status_code and status_code >= 500 else "WARNING" if status_code and status_code >= 400 else "INFO"
        log_system_event(
            level=level,
            source="django",
            logger_name="django.request",
            event_type="request",
            message=f"{request.method} {request.get_full_path()} -> {status_code}",
            request_id=request_id,
            method=request.method,
            path=request.get_full_path(),
            status_code=status_code,
            duration_ms=duration_ms,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            context={"headers": request_headers(request.headers)},
        )
        return response
