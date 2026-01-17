FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl perl wget ca-certificates \
    && wget -qO- "https://yihui.org/tinytex/install-bin-unix.sh" | sh \
    && /root/.TinyTeX/bin/x86_64-linux/tlmgr install \
    multicol wrapfig caption booktabs tcolorbox lipsum microtype environ pgf etoolbox || true \
    && /root/.TinyTeX/bin/x86_64-linux/tlmgr path add \
    && apt-get purge -y curl wget \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /root/.TinyTeX/texmf-dist/doc/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
ENV PATH="${PATH}:/root/.TinyTeX/bin/x86_64-linux" \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app/src"

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache

COPY src/ ./src/
RUN mkdir -p /app/src/output

CMD ["uv", "run", "python", "src/models/inference.py", "full", "image"]