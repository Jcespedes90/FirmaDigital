from django.contrib import admin

# Register your models here.

from .models import Firma

# Registrar el modelo en el administrador
admin.site.register(Firma)
