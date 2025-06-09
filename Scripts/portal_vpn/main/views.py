import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from .forms import CustomUserCreationForm
from .models import VPNConnectionLog
from django.conf import settings
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.contrib import messages
import subprocess
import socket

def generar_certificado(nombre_usuario):
    script_path = "/home/vpn/portal_vpn/crear_cert_cliente.sh"
    try:
        subprocess.run([script_path, nombre_usuario], check=True)
        print(f"Certificado generado para {nombre_usuario}")
    except subprocess.CalledProcessError as e:
        print(f"Error generando certificado para {nombre_usuario}: {e}")

def expulsar_cliente(nombre_usuario):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', 7505))
        s.recv(4096)
        s.sendall(f"kill {nombre_usuario}\n".encode())
        s.recv(4096)
        s.sendall(b"quit\n")
        s.close()
    except Exception as e:
        print(f"Error expulsando al usuario {nombre_usuario}: {e}")

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_active:
                login(request, user)
                return redirect('home')
            else:
                form.add_error(None, 'Tu cuenta aún no ha sido activada por un administrador.')
    else:
        form = AuthenticationForm()
    return render(request, 'main/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # El usuario está inactivo hasta que el admin lo apruebe
            user.save()
            return render(request, 'main/registration_pending.html')
    else:
        form = CustomUserCreationForm()
    return render(request, 'main/register.html', {'form': form})

def leer_usuarios_conectados():
    ruta_status = '/var/log/openvpn-status.log'
    conectados = set()

    if os.path.exists(ruta_status):
        with open(ruta_status, 'r') as f:
            dentro_de_lista = False
            for linea in f:
                linea = linea.strip()
                if linea.startswith("Common Name"):
                    dentro_de_lista = True
                    continue
                if linea.startswith("ROUTING TABLE"):
                    break
                if dentro_de_lista and linea:
                    campos = linea.split(',')
                    if campos:
                        conectados.add(campos[0])  # Common Name
    return conectados

@login_required
def home_view(request):
    if request.user.is_superuser:
        return redirect('admin_home')
    else:
        user_folder = os.path.join('media', request.user.username)
        zip_file = f'{request.user.username}_vpn_pack.zip'
        zip_path = os.path.join(user_folder, zip_file)

        return render(request, 'main/home.html', {
            'zip_path': zip_path if os.path.exists(zip_path) else None
        })

@login_required
def admin_home(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('login')

    usuarios = User.objects.all()
    conectados = leer_usuarios_conectados()

    for u in usuarios:
        u.conectado = u.username in conectados

    logs = VPNConnectionLog.objects.order_by('-connected_at')[:10]

    return render(request, 'main/admin_home.html', {
        'usuarios': usuarios,
        'logs': logs,
        'conectados': conectados,
        'form': CustomUserCreationForm()
    })

@login_required
@require_POST
def crear_usuario(request):
    if not request.user.is_superuser:
        return redirect('home')

    form = CustomUserCreationForm(request.POST)
    if form.is_valid():
        user = form.save(commit=False)
        user.is_active = False
        user.save()
    return redirect('home')

@login_required
def activar_usuario(request, user_id):
    if not request.user.is_superuser:
        return redirect('home')

    usuario = get_object_or_404(User, id=user_id)
    usuario.is_active = True
    usuario.save()

    # Generar nuevos certificados y archivos del cliente
    generar_certificado(usuario.username)

    return redirect('home')

@login_required
def eliminar_usuario(request, user_id):
    if not request.user.is_superuser:
        return redirect('home')

    usuario = get_object_or_404(User, id=user_id)
    usuario.delete()
    return redirect('home')

@login_required
def toggle_admin(request, user_id):
    if not request.user.is_superuser:
        return redirect('home')

    usuario = get_object_or_404(User, id=user_id)
    if usuario.username == 'vpn':
        return redirect('home')

    usuario.is_staff = not usuario.is_staff
    usuario.is_superuser = usuario.is_staff
    usuario.save()
    return redirect('home')

@login_required
def historial_partial(request):
    logs = VPNConnectionLog.objects.exclude(username='UNDEF').order_by('-connected_at')
    paginator = Paginator(logs, 10)  # Mostrar 10 logs por página

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'main/historial_conexiones.html', {'page_obj': page_obj})

def revocar_certificado(nombre_usuario):
    script_path = "/home/vpn/portal_vpn/revocar_cert_cliente.sh"
    try:
        subprocess.run(['sudo', script_path, nombre_usuario], check=True)
        print(f"Certificado revocado para {nombre_usuario}")
    except subprocess.CalledProcessError as e:
        print(f"Error revocando certificado para {nombre_usuario}: {e}")

@login_required
def desactivar_usuario(request, user_id):
    if not request.user.is_superuser:
        return redirect('home')

    usuario = get_object_or_404(User, id=user_id)
    if usuario.username == 'vpn':
        return redirect('home')

    usuario.is_active = False
    usuario.save()

    # Revocar el certificado al desactivar
    expulsar_cliente(usuario.username)
    revocar_certificado(usuario.username)

    return redirect('home')

@login_required
def eliminar_usuario(request, user_id):
    if not request.user.is_superuser:
        return redirect('home')

    usuario = get_object_or_404(User, id=user_id)
    if usuario.username == 'vpn':
        return redirect('home')

    # Revocar antes de eliminar
    expulsar_cliente(usuario.username)
    revocar_certificado(usuario.username)
    usuario.delete()

    return redirect('home')

@login_required
def estado_usuarios_partial(request):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'No autorizado'}, status=403)

    usuarios = User.objects.all()
    conectados = leer_usuarios_conectados()

    for u in usuarios:
        u.conectado = u.username in conectados

    html = render_to_string('main/usuarios_estado.html', {'usuarios': usuarios})
    return JsonResponse({'html': html})
