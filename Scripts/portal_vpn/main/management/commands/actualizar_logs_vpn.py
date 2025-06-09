from django.core.management.base import BaseCommand
from main.models import VPNConnectionLog
from datetime import datetime, timedelta
from django.utils.timezone import make_aware, now
import os

class Command(BaseCommand):
    help = 'Actualiza los registros de conexiones y desconexiones desde el log de OpenVPN'

    def handle(self, *args, **options):
        log_file_path = '/var/log/openvpn-status.log'

        if not os.path.exists(log_file_path):
            self.stderr.write(f"Archivo no encontrado: {log_file_path}")
            return

        with open(log_file_path, 'r') as f:
            lines = f.readlines()

        conectados_actuales = set()
        processing_clients = False

        for line in lines:
            line = line.strip()

            if line.startswith("Common Name,Real Address"):
                processing_clients = True
                continue

            if processing_clients:
                if not line or line.startswith("ROUTING TABLE"):
                    break

                try:
                    parts = line.split(',')
                    if len(parts) >= 5:
                        username = parts[0]
                        ip_address = parts[1].split(':')[0]
                        connected_at_str = parts[4].strip()

                        connected_at = make_aware(datetime.strptime(connected_at_str, "%Y-%m-%d %H:%M:%S"))

                        if not VPNConnectionLog.objects.filter(
                            username=username,
                            ip_address=ip_address,
                            connected_at=connected_at
                        ).exists():
                            VPNConnectionLog.objects.create(
                                username=username,
                                ip_address=ip_address,
                                connected_at=connected_at
                            )

                        conectados_actuales.add((username, ip_address, connected_at))

                except Exception as e:
                    self.stderr.write(f"Error procesando línea: {line} ({e})")

        # Registrar desconexiones
        logs_activos = VPNConnectionLog.objects.filter(disconnected_at__isnull=True)

        for log in logs_activos:
            clave = (log.username, log.ip_address, log.connected_at)
            if clave not in conectados_actuales:
                ahora = now()
                if ahora > log.connected_at:
                    duracion = ahora - log.connected_at
                    duracion = timedelta(seconds=int(duracion.total_seconds()))  # sin decimales
                    log.disconnected_at = ahora
                    log.duration = duracion
                    log.save()
                    self.stdout.write(f"Desconexión registrada para {log.username}")

        self.stdout.write(self.style.SUCCESS("Logs actualizados correctamente."))
