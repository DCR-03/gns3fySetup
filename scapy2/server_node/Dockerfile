FROM python:3.11-slim

WORKDIR /app

COPY server_node.py /app/server_node.py

RUN pip install --no-cache-dir scapy requests

EXPOSE 9000   # For control plane
EXPOSE 8080   # For HTTP server

CMD ["python", "server_node.py"]
