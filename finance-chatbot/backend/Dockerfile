FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY llm/ llm/
COPY backend/ backend/

ENV PORT=5000
EXPOSE 5000

CMD ["python", "backend/app.py"]
