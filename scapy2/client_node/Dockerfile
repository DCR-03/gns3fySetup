FROM python:3.11-slim

WORKDIR /app

COPY client_node.py /app/client_node.py

RUN pip install --no-cache-dir scapy requests

EXPOSE 9000  # For control plane

CMD ["python", "client_node.py"]
