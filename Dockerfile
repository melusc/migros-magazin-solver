FROM python:3.15-slim-bookworm@sha256:575f8bc12ec26542e0678bc6b60e385218248019d433157ec327264a78c3a853 AS builder

COPY --from=ghcr.io/astral-sh/uv:latest@sha256:32a7bb39b496babbd997b0a39a4d66c126bdaf5661b302bf6f06abda8deca6ff /uv /uvx /bin/

ENV UV_LINK_MODE=copy
ENV UV_PYTHON_CACHE_DIR=/root/.cache/uv/python

WORKDIR /app

COPY COPYING pyproject.toml uv.* .python-version .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --compile-bytecode --no-dev

COPY scrapers scrapers
COPY templates templates
COPY *.py .

RUN uv run --no-sync -m scrapers.german_words

RUN rm -r /bin/uv /bin/uvx /root/.cache

FROM scratch

COPY --from=builder / /

WORKDIR /app

ENV BIND=0.0.0.0:3000
EXPOSE 3000

CMD ["/app/.venv/bin/python", "-m", "gunicorn", "--config", "/app/gunicorn.conf.py"]
