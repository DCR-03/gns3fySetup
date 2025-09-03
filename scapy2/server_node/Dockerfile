FROM python:3.11-slim

WORKDIR /app

COPY server_node.py /app/server_node.py

RUN pip install --no-cache-dir scapy requests

EXPOSE 8080

CMD ["python", "server_node.py"]
