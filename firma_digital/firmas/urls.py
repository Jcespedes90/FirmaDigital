from django.urls import path
from . import views

urlpatterns = [
    path('firmar/', views.firmar_documento, name='firmar_documento'),  # Asegúrate de que esta ruta esté definida
    path('validar_firma/', views.validar_firma_documento, name='validar_firma_documento'),
]
