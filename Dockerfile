FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY schemas/ ./schemas/

ENV PYTHONPATH=/app/src

CMD ["python", "-m", "music_adapter.main"]