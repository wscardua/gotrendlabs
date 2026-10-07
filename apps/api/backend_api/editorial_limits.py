"""HTTP body limit applied before decoding editorial inputs."""

from starlette.responses import JSONResponse


class EditorialBodyLimit:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not scope.get("path", "").startswith(
            (
                "/oauth/",
                "/internal/agent-integrations",
                "/integrations/editorial",
                "/admin/agent-",
            )
        ):
            return await self.app(scope, receive, send)
        chunks = []
        size = 0
        while True:
            message = await receive()
            if message["type"] != "http.request":
                return
            size += len(message.get("body", b""))
            if size > 131072:
                return await JSONResponse(
                    {
                        "detail": {
                            "code": "validation_failed",
                            "message": "Request too large",
                        }
                    },
                    413,
                    headers={"Cache-Control": "private, no-store"},
                )(scope, receive, send)
            chunks.append(message.get("body", b""))
            if not message.get("more_body", False):
                break
        first = True

        async def bounded():
            nonlocal first
            if first:
                first = False
                return {
                    "type": "http.request",
                    "body": b"".join(chunks),
                    "more_body": False,
                }
            return await receive()

        await self.app(scope, bounded, send)
