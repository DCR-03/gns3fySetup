FROM python:3.11-slim

WORKDIR /app

COPY adversary.py /app/adversary.py

RUN pip install --no-cache-dir scapy requests

EXPOSE 9000

CMD ["python", "adversary.py"]
