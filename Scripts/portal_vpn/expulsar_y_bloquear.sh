#!/bin/bash

CN="$1"
PUERTO_MANAGEMENT=7505
STATUS_LOG="/var/log/openvpn-status.log"
TIEMPO_BLOQUEO=60  # en segundos

if [[ -z "$CN" ]]; then
    echo "Uso: $0 <common_name>"
    exit 1
fi

# Obtener IP del cliente desde el log
IP_CLIENTE=$(awk -v user="$CN" -F, '$1 == user {print $2}' "$STATUS_LOG" | cut -d':' -f1)

if [[ -z "$IP_CLIENTE" ]]; then
    echo "No se encontró la IP del cliente $CN en $STATUS_LOG"
    exit 1
fi

echo "Cliente $CN conectado desde IP $IP_CLIENTE"

# Expulsar cliente usando la interfaz de gestión
echo "Expulsando cliente $CN..."
{
    echo "kill $CN"
    sleep 1
    echo "quit"
} | telnet 127.0.0.1 $PUERTO_MANAGEMENT > /dev/null 2>&1

# Bloquear IP
echo "Bloqueando IP $IP_CLIENTE durante $TIEMPO_BLOQUEO segundos..."
sudo iptables -I INPUT -s "$IP_CLIENTE" -j DROP

# Esperar y luego quitar la regla
sleep $TIEMPO_BLOQUEO
echo "Desbloqueando IP $IP_CLIENTE..."
sudo iptables -D INPUT -s "$IP_CLIENTE" -j DROP

echo "Proceso completado."
