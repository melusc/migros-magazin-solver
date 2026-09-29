FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim@sha256:7cf77f594be8042dab6daa9fe326f90962252268b4f120a7f5dccce4d947e6c1 AS builder

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

RUN rm -r /usr/local/bin/uv /usr/local/bin/uvx /root/.cache

FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim@sha256:7cf77f594be8042dab6daa9fe326f90962252268b4f120a7f5dccce4d947e6c1 AS runner

COPY --from=builder / /

WORKDIR /app

ENV BIND=0.0.0.0:3000
EXPOSE 3000

CMD ["/app/.venv/bin/python", "-m", "gunicorn", "--config", "/app/gunicorn.conf.py"]
