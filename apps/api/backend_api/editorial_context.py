from contextvars import ContextVar

# Set only by the HTTP boundary; no actor/scopes are taken from this context.
request_context = ContextVar("editorial_request_context", default={})
