FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.0 /uv /uvx /bin/
ENV PYTHONUNBUFFERED=1
ENV FORWARDED_ALLOW_IPS="*"
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PATH="/app/.venv/bin:$PATH"
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY . .
RUN useradd --create-home appuser
USER appuser
EXPOSE 8000
CMD ["sh", "-c", "fastapi run main.py --port ${PORT:-8000}"]
