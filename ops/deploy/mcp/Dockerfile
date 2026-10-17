FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY apps/mcp/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt && useradd --system --uid 10001 mcp
COPY apps/mcp /app/apps/mcp
# Schemas contain Pydantic only; no DB/client runtime is copied to this image.
COPY apps/api/backend_api/editorial_schemas.py apps/api/backend_api/resolution_schedule_contract.py /app/apps/api/backend_api/
RUN python -c "from apps.mcp.server import app; from apps.api.backend_api.editorial_schemas import Draft; Draft.model_json_schema()"
RUN mkdir -p /spool && chown mcp /spool
USER mcp
EXPOSE 8002
CMD ["uvicorn", "apps.mcp.server:app", "--host", "0.0.0.0", "--port", "8002", "--no-access-log", "--log-level", "warning"]
