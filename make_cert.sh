#!/bin/sh
# HTTPS certifikát na aktuálnu IP (pri zmene IP spusti znova)
cd "$(dirname "$0")"
mkdir -p data
IP=$(hostname -I | awk '{print $1}')
openssl req -x509 -newkey rsa:2048 -nodes -days 3650 \
  -keyout data/key.pem -out data/cert.pem -subj "/CN=$IP" \
  -addext "subjectAltName=IP:$IP,IP:127.0.0.1"
echo "Certifikát pre $IP: data/cert.pem"
