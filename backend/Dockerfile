# Tollgate API (Phase 7). Runtime image: the application, its locked dependencies, and the eval run SUMMARIES only.
#
# Eval runs (owner, 2026-11-14): the image carries each run's meta.json and summary.json (about 35 KB in all), which
# the dashboard's "Evaluation runs" section reads: it shows measured results. Recordings and results.jsonl are
# development artefacts and have no place in a runtime image; .dockerignore keeps them out of the build context.
# In local development, docker-compose.yml bind-mounts backend/eval/runs/ over this copy, so new runs show without a
# rebuild. If the summaries are missing, the section shows its empty state (probe db10).
FROM python:3.12.3-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.12.3 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY tollgate ./tollgate
# editable install: the dashboard finds the run files relative to the package (tollgate/domain/dashboard.py)
RUN uv sync --frozen --no-dev
COPY eval/runs/eval ./eval/runs/eval

EXPOSE 8000
CMD ["uv", "run", "--no-sync", "uvicorn", "tollgate.main:app", "--host", "0.0.0.0", "--port", "8000"]
