import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from .forms import CustomUserCreationForm

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
            user.is_active = False  # El usuario está inactivo hasta que el admin lo active
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
        usuarios = User.objects.all()
        conectados = leer_usuarios_conectados()

        for u in usuarios:
            u.conectado = u.username in conectados

        form = CustomUserCreationForm()

        return render(request, 'main/admin_home.html', {
            'usuarios': usuarios,
            'conectados': conectados,
            'form': form,
        })
    else:
        user_folder = os.path.join('media', request.user.username)
        zip_file = f'{request.user.username}_vpn_pack.zip'
        zip_path = os.path.join(user_folder, zip_file)

        return render(request, 'main/home.html', {
            'zip_path': zip_path if os.path.exists(zip_path) else None
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
    usuario.is_staff = not usuario.is_staff
    usuario.is_superuser = usuario.is_staff  # Opcional: admin total si is_staff true
    usuario.save()
    return redirect('home')
