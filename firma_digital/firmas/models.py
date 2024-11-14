# modelos.py en la app "firmas"
import hashlib
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Firma(models.Model):
   # usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    #documento = models.FileField(upload_to='documentos/')
    #fecha_firma = models.DateTimeField(auto_now_add=True)
    #firma_valida = models.BooleanField(default=False)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    documento = models.FileField(upload_to='documentos_firmados/')
    firma_valida = models.BooleanField(default=True)
    fecha_firma = models.DateTimeField(default=timezone.now)
    coordenada_x = models.IntegerField(blank=True, null=True)  # Coordenada X de la firma
    coordenada_y = models.IntegerField(blank=True, null=True)  # Coordenada Y de la firma
    hash_documento = models.CharField(max_length=64)  # Almacena el hash SHA-256 del documento

    def __str__(self):
        return f"Firma de {self.usuario} - {self.fecha_firma}"

    def verificar_firma(self, documento):
            """Verifica si el documento proporcionado coincide con el hash almacenado"""
            hash_sha256 = hashlib.sha256()
            
            # Generar el hash del documento proporcionado
            for chunk in documento.chunks():
                hash_sha256.update(chunk)
            
            # Comparar el hash generado con el hash almacenado
            return hash_sha256.hexdigest() == self.hash_documento

