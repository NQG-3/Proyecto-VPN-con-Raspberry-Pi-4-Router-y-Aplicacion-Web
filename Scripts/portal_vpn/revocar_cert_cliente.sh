#!/bin/bash

CLIENT_NAME=$1
EASY_RSA_DIR="/home/vpn/openvpn-ca"
PASSWORD="NQG-1234"

cd "$EASY_RSA_DIR" || exit 1

# Revocar el certificado con passphrase y confirmación automática
echo yes | EASYRSA_PASSIN="pass:$PASSWORD" ./easyrsa revoke "$CLIENT_NAME"

# Generar la CRL (también necesita la passphrase)
EASYRSA_PASSIN="pass:$PASSWORD" ./easyrsa gen-crl

# Copiar la CRL al directorio OpenVPN y asignar permisos correctos
sudo cp pki/crl.pem /etc/openvpn/crl.pem
sudo chown nobody:nogroup /etc/openvpn/crl.pem

# Reiniciar OpenVPN para que la nueva CRL se aplique
sudo systemctl restart openvpn@server
