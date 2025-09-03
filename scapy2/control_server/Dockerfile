FROM python:3.11-slim

WORKDIR /app

COPY control_server.py /app/control_server.py

RUN pip install --no-cache-dir scapy requests

EXPOSE 9000

CMD ["python", "control_server.py"]
