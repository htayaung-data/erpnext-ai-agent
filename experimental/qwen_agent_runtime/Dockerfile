FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app /app/app

ENV APP_HOST=0.0.0.0
ENV APP_PORT=8010

CMD ["sh", "-lc", "uvicorn app.main:app --host ${APP_HOST} --port ${APP_PORT}"]
