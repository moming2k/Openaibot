# 第一个阶段
FROM python:3.11-bookworm AS builder

RUN apt update && \
    apt install -y build-essential && \
    pip install -U pip setuptools wheel && \
    pip install pdm && \
    apt install -y ffmpeg

COPY . /project/
WORKDIR /project
# Install all dependencies including optional ones (bot and api groups)
# Continue even if some packages fail (e.g., primp, duckduckgo-search on ARM64)
RUN pdm lock --update-reuse && \
    (pdm install --no-editable || echo "Some optional packages failed to install, continuing...")

# 第二个阶段
FROM python:3.11-slim-bookworm AS runtime

RUN apt update && \
    apt install -y npm && \
    npm install pm2 -g && \
    apt install -y ffmpeg && \
    pip install pdm

VOLUME ["/app/config_dir", "/app/logs"]

WORKDIR /app
COPY --from=builder /project/.venv /app/.venv

COPY pm2.json ./
COPY . /app

CMD [ "pm2-runtime", "pm2.json" ]
