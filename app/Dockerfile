FROM python:3.11-slim
WORKDIR /app
COPY app.py .
COPY requirements.txt .
RUN pip install -r requirements.txt
ENV VERSION=unknown
EXPOSE 8080
CMD ["python", "app.py"]
