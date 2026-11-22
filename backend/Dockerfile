FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY sample_data ./sample_data
ENV DATA_DIR=/data
EXPOSE 8000
CMD ["python", "-m", "app.main"]
