FROM python:3.12-alpine

RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python3", "client.py"]

# Alpine Linux with Python 3.12 and necessary build tools with a simple client script that
# allows to test different functions of the gns3fy library and our own messaging protocols.