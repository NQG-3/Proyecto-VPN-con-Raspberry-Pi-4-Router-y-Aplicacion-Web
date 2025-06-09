#!/bin/bash

# Variables
CLIENT_NAME=$1
EASY_RSA_DIR="/home/vpn/openvpn-ca"
OUTPUT_DIR="/home/vpn/client-configs"
DEST_DIR="/home/vpn/portal_vpn/media/$CLIENT_NAME"
PASSWORD="NQG-1234"

cd "$EASY_RSA_DIR" || exit 1
source ./vars

echo "[*] Eliminando restos anteriores si existen..."
rm -f "pki/issued/$CLIENT_NAME.crt" "pki/private/$CLIENT_NAME.key" "pki/reqs/$CLIENT_NAME.req"

# Revocar si existe el certificado (solo para limpiar index.txt)
if ./easyrsa show-cert "$CLIENT_NAME" &> /dev/null; then
  echo yes | EASYRSA_PASSIN="pass:$PASSWORD" ./easyrsa revoke "$CLIENT_NAME"
  EASYRSA_PASSIN="pass:$PASSWORD" ./easyrsa gen-crl
fi

echo "[*] Generando nuevo par de claves y solicitud de firma..."
EASYRSA_BATCH=1 EASYRSA_REQ_CN="$CLIENT_NAME" ./easyrsa gen-req "$CLIENT_NAME" nopass

echo yes | EASYRSA_PASSIN="pass:$PASSWORD" ./easyrsa sign-req client "$CLIENT_NAME"

# Copiar archivos necesarios
mkdir -p "$OUTPUT_DIR"
cp "pki/private/$CLIENT_NAME.key" "$OUTPUT_DIR/"
cp "pki/issued/$CLIENT_NAME.crt" "$OUTPUT_DIR/"
cp "pki/ca.crt" "$OUTPUT_DIR/"
cp "/etc/openvpn/ta.key" "$OUTPUT_DIR/"

# Generar archivo .ovpn
cat <<EOT > "$OUTPUT_DIR/$CLIENT_NAME.ovpn"
client
dev tun
proto udp
;remote 10.144.254.61 1194
remote 192.168.1.100 1194
;resolv-retry infinite
explicit-exit-notify 1
nobind
persist-key
persist-tun
remote-cert-tls server
<ca>
$(cat "$OUTPUT_DIR/ca.crt")
</ca>
<cert>
$(sed -n '/-----BEGIN CERTIFICATE-----/,/-----END CERTIFICATE-----/p' "$OUTPUT_DIR/$CLIENT_NAME.crt")
</cert>
<key>
$(cat "$OUTPUT_DIR/$CLIENT_NAME.key")
</key>
<tls-auth>
$(cat "$OUTPUT_DIR/ta.key")
</tls-auth>
key-direction 1
data-ciphers AES-256-GCM:AES-128-GCM
auth SHA256
auth-nocache
auth-retry nointeract
EOT

# Copiar y comprimir para portal
mkdir -p "$DEST_DIR"
cp "$OUTPUT_DIR/$CLIENT_NAME.ovpn" "$DEST_DIR/"
cp "$OUTPUT_DIR/$CLIENT_NAME.key" "$DEST_DIR/"
cp "$OUTPUT_DIR/$CLIENT_NAME.crt" "$DEST_DIR/"
cp "$OUTPUT_DIR/ca.crt" "$DEST_DIR/"
cp "$OUTPUT_DIR/ta.key" "$DEST_DIR/"

cd "$DEST_DIR" || exit 1
zip -r "${CLIENT_NAME}_vpn_pack.zip" *.ovpn *.key *.crt ca.crt ta.key

echo "Certificados y paquete ZIP actualizados para $CLIENT_NAME"
