from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('admin_home/', views.admin_home, name='admin_home'),
    path('estado_usuarios/partial/', views.estado_usuarios_partial, name='estado_usuarios_partial'),
    path('historial/partial/', views.historial_partial, name='historial_partial'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('desactivar_usuario/<int:user_id>/', views.desactivar_usuario, name='desactivar_usuario'),

    path('crear_usuario/', views.crear_usuario, name='crear_usuario'),
    path('activar_usuario/<int:user_id>/', views.activar_usuario, name='activar_usuario'),
    path('desactivar_usuario/<int:user_id>/', views.desactivar_usuario, name='desactivar_usuario'),
    path('eliminar_usuario/<int:user_id>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('toggle_admin/<int:user_id>/', views.toggle_admin, name='toggle_admin'),
]
