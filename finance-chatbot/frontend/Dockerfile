FROM python:3.11-slim

WORKDIR /app

COPY frontend/requirements.txt frontend/requirements.txt
RUN pip install --no-cache-dir -r frontend/requirements.txt

COPY frontend/ frontend/

ENV BACKEND_URL=http://backend:5000/api/chat
EXPOSE 7860

CMD ["python", "frontend/gradio_app.py"]
