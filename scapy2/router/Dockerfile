FROM python:3.11-slim

WORKDIR /app

COPY router.py /app/router.py

RUN apt-get update && apt-get install -y iproute2 iputils-ping tcpdump && \
    pip install --no-cache-dir scapy requests && \
    rm -rf /var/lib/apt/lists/*

# Enable IP forwarding inside container
RUN echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf

EXPOSE 9000

CMD ["python", "router.py"]
