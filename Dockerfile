FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    JARVIS_DB_PATH=/data/jarvis.db

COPY pyproject.toml README.md ./
COPY jarvis ./jarvis
RUN pip install --no-cache-dir '.[telegram]'

VOLUME /data
ENTRYPOINT ["jarvis"]
CMD []
