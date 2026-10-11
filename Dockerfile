FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1
ENV FORWARDED_ALLOW_IPS="*"
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --create-home appuser
USER appuser
EXPOSE 8000
CMD ["sh", "-c", "fastapi run main.py --port ${PORT:-8000}"]