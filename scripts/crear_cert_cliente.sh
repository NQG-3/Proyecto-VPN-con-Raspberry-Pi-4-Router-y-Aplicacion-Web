#!/bin/bash

# Variables
CLIENT_NAME=$1
EASY_RSA_DIR="/home/vpn/openvpn-ca"
OUTPUT_DIR="/home/vpn/client-configs"
PASSWORD="NQG-1234"

# Navega al directorio Easy-RSA
cd $EASY_RSA_DIR

# Fuente Easy-RSA
source ./vars

# Genera el certificado y la clave para el cliente sin passphrase
EASYRSA_BATCH=1 EASYRSA_REQ_CN="$CLIENT_NAME" ./easyrsa gen-req $CLIENT_NAME nopass

# Firma el certificado automáticamente con yes y passphrase
echo yes | EASYRSA_PASSIN="pass:$PASSWORD" ./easyrsa sign-req client $CLIENT_NAME

# Verifica si la firma fue exitosa
if [ $? -ne 0 ]; then
  echo "Error al firmar el certificado para $CLIENT_NAME"
  exit 1
fi

# Mueve los certificados generados a la carpeta de salida
cp pki/private/$CLIENT_NAME.key $OUTPUT_DIR/$CLIENT_NAME.key
cp pki/issued/$CLIENT_NAME.crt $OUTPUT_DIR/$CLIENT_NAME.crt
cp pki/ca.crt $OUTPUT_DIR/ca.crt

# Copia ta.key si tienes permisos
if cp /etc/openvpn/ta.key $OUTPUT_DIR/ta.key; then
  echo "Archivo ta.key copiado correctamente"
else
  echo "Error: no se pudo copiar el archivo ta.key. ¿Tienes permisos?"
fi

# Crea el archivo .ovpn
cat <<EOT > $OUTPUT_DIR/$CLIENT_NAME.ovpn
client
dev tun
proto udp
remote 192.168.1.100 1194
resolv-retry infinite
nobind
persist-key
persist-tun
remote-cert-tls server
<ca>
$(cat $OUTPUT_DIR/ca.crt)
</ca>
<cert>
$(cat $OUTPUT_DIR/$CLIENT_NAME.crt)
</cert>
<key>
$(cat $OUTPUT_DIR/$CLIENT_NAME.key)
</key>
<tls-auth>
$(cat $OUTPUT_DIR/ta.key)
</tls-auth>
key-direction 1
cipher AES-256-CBC
auth SHA256
auth-nocache
EOT

# Ruta del directorio destino en media/
DEST_DIR="/home/vpn/portal_vpn/media/$CLIENT_NAME"

# Crea el directorio del usuario si no existe
mkdir -p "$DEST_DIR"

# Copia los archivos al directorio del usuario
cp /home/vpn/client-configs/$CLIENT_NAME.* "$DEST_DIR/"

# Mensaje de éxito
echo "Certificado y archivo .ovpn para el cliente $CLIENT_NAME creados en $DEST_DIR"
