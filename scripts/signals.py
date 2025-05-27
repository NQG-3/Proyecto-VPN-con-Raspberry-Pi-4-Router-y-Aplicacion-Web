import os
import shutil
import zipfile
import subprocess
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def crear_certificado_y_guardar_credenciales(sender, instance, created, **kwargs):
    # Ejecutar solo si el usuario fue activado (no creado) y aún no tiene certificado
    if not created and instance.is_active:
        username = instance.username

        user_media_path = os.path.join(settings.MEDIA_ROOT, username)
        zip_path = os.path.join(user_media_path, f'{username}_vpn_pack.zip')

        # Si ya existe el .zip, no volver a generar nada
        if os.path.exists(zip_path):
            return

        # Ejecutar script para crear certificado
        script_path = os.path.join(settings.BASE_DIR, 'crear_cert_cliente.sh')
        try:
            subprocess.run([script_path, username, 'NQG-1234'], check=True)
        except subprocess.CalledProcessError:
            print(f"Error al ejecutar el script para {username}")
            return

        # Crear carpeta si no existe
        os.makedirs(user_media_path, exist_ok=True)

        # Ruta base de los certificados generados
        client_config_dir = os.path.expanduser('~/client-configs')
        archivos_a_incluir = []

        # Copiar .ovpn, .key, .crt del usuario sin renombrar
        for ext in ['.ovpn', '.key', '.crt']:
            filename = f'{username}{ext}'
            source = os.path.join(client_config_dir, filename)
            if os.path.exists(source):
                dest = os.path.join(user_media_path, filename)
                shutil.copy(source, dest)
                archivos_a_incluir.append(dest)

        # Copiar ca.crt
        ca_source = os.path.expanduser('~/client-configs/ca.crt')
        if os.path.exists(ca_source):
            ca_dest = os.path.join(user_media_path, 'ca.crt')
            shutil.copy(ca_source, ca_dest)
            archivos_a_incluir.append(ca_dest)

        # Copiar ta.key
        ta_source = os.path.expanduser('~/client-configs/ta.key')
        if os.path.exists(ta_source):
            ta_dest = os.path.join(user_media_path, 'ta.key')
            shutil.copy(ta_source, ta_dest)
            archivos_a_incluir.append(ta_dest)

        # Crear archivo .zip
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file_path in archivos_a_incluir:
                zipf.write(file_path, arcname=os.path.basename(file_path))
