
from django.contrib import admin
from django.urls import path, include  # Asegúrate de importar 'include'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('firmas/', include('firmas.urls')),  # Conecta las URLs de la app "firmas"
]