FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY analyzer.py .

EXPOSE 8000

CMD ["python", "analyzer.py"]
