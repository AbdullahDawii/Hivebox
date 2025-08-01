
#Build the Docker image and run it locally.

FROM python:3.10-slim

WORKDIR /app

COPY . .

CMD ["python", "main.py"]
