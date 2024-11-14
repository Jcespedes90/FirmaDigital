import io
import datetime
from django.shortcuts import render
from django.http import HttpResponse
from django.utils import timezone
from django.contrib.auth import authenticate, login
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from .models import Firma
import hashlib
from django.shortcuts import render, HttpResponse


# Función para generar el hash del documento PDF
def generar_hash_documento(documento):
    """Generar un hash SHA-256 del archivo PDF"""
    hash_sha256 = hashlib.sha256()    
   
 
    for chunk in documento.chunks():
        hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

#vista para firmar el Documento
def firmar_documento(request):
    if request.method == 'POST':
        # Autenticar al usuario
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)  # Autenticar usuario
            documento_file = request.FILES['documento']  # Obtener archivo PDF
            apellido = user.last_name
            nombre = user.first_name
            nombreCompleto = nombre + " " + apellido 
             # Generar hash del documento antes de firmar
            hash_documento = generar_hash_documento(documento_file)
            # Obtener el nombre original del archivo
            nombre_documento = documento_file.name
            
            # Obtener coordenadas de la firma
            x = int(request.POST['posicion_x'])
            y = int(request.POST['posicion_y'])
            
            # Firmar el PDF con las coordenadas proporcionadas
            documento_firmado = agregar_firma_a_pdf(documento_file, nombreCompleto, x, y, nombre_documento)
           # hash_documento_Firmado = generar_hash_documento(documento_firmado+'application/pdf')
            # Guardar la firma en la base de datos
            firma = Firma(usuario=user, documento=nombre_documento, firma_valida=True, fecha_firma=timezone.now(),coordenada_x=x,
                coordenada_y=y,hash_documento=hash_documento)
            firma.save()
            
            # Preparar el archivo para la descarga
            response = HttpResponse(documento_firmado, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{nombre_documento}"'
            return response
        else:
            return HttpResponse("Error: Credenciales inválidas.")
    
    return render(request, 'firmas/firma_form.html')

#Agregar la firma al documento pdf
def agregar_firma_a_pdf(documento_file, usuario, x, y, nombre_documento, pagina_firma=None):
    packet = io.BytesIO()

    # Crear un canvas para la firma
    can = canvas.Canvas(packet, pagesize=letter)
    fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d")
    hora_actual = datetime.datetime.now().strftime("%H:%M:%S")
    can.setFont("Helvetica", 8)
    can.drawString(x, y, "Firmado digitalmente por:")
    can.drawString(x, y-10, usuario.upper())
    can.drawString(x, y-20, "(FIRMA)")
    can.setFont("Helvetica", 7)
    can.drawRightString(x+60, y-30, "Fecha: "+fecha_actual)
    can.drawRightString(x+50, y-40, hora_actual + " -06'00'")
    can.setFillAlpha(0)
    can.drawRightString(x+20, y-50, "(COFASA)")
    can.save()

    # Mover el puntero del stream al inicio
    packet.seek(0)

    # Leer el PDF original
    pdf_original = PdfReader(documento_file)
    pdf_firmado = PdfWriter()

    # Si no se especifica la página, se aplica la firma en la última página
    if pagina_firma is None:
        pagina_firma = len(pdf_original.pages)  # Página final

    # Recorrer todas las páginas y añadirlas al PDF firmado
    for i, pagina in enumerate(pdf_original.pages):
        if i == pagina_firma - 1:  # Página específica para la firma
            pagina_firma_pdf = PdfReader(packet).pages[0]
            pagina.merge_page(pagina_firma_pdf)  # Fusionar la firma
        pdf_firmado.add_page(pagina)  # Añadir la página al nuevo documento

    # Guardar el PDF firmado en un objeto BytesIO
    output_pdf = io.BytesIO()
    pdf_firmado.write(output_pdf)
    output_pdf.seek(0)

    return output_pdf
#Validar si el documento tiene firma y si existe registrada
def validar_firma_documento(request):
    if request.method == 'POST':
        documento_file = request.FILES['documento']  # Archivo PDF cargado para validar

        # Leer el archivo PDF
        pdf_reader = PdfReader(documento_file)
        
        # Buscar una posible marca de firma en el PDF
        documento_tiene_firma = False
        for pagina in pdf_reader.pages:
            texto = pagina.extract_text()
            if texto and "Firmado digitalmente por:" in texto:
                documento_tiene_firma = True
                break

        # Si el documento no tiene una firma visualmente marcada
        if not documento_tiene_firma:
            return HttpResponse("El documento no parece estar firmado.")

        # Generar el hash del documento cargado
        hash_sha256 = hashlib.sha256()
        documento_file.seek(0)  # Volver al inicio del archivo después de leerlo
        for chunk in documento_file.chunks():
            hash_sha256.update(chunk)
        hash_documento_cargado = hash_sha256.hexdigest()
        print("Hash documento cargado:", hash_documento_cargado)  # Imprimir el hash

        # Verificar si el hash coincide con alguno registrado en la base de datos
        firmas = Firma.objects.filter(hash_documento=hash_documento_cargado)
        print("Firmas encontradas:", firmas)  # Imprimir el queryset de firmas

        # Imprimir todos los hashes en la base de datos para depuración
       # all_firmas = Firma.objects.all()
       # for f in all_firmas:
        #    print(f"Hash BD: {f.hash_documento}, Usuario: {f.usuario.get_full_name()}")

        if firmas.exists():
            # Obtener los nombres de todos los usuarios que firmaron
            nombres_usuarios = [firma.usuario.get_full_name() for firma in firmas]
            return render(request, 'firmas/validar_firma_resultado.html', {'nombres_usuarios': nombres_usuarios})
        else:
            return HttpResponse("El documento está firmado, pero no se encontró un registro correspondiente en la base de datos.")

    # Si no es POST, mostrar el formulario de validación
    return render(request, 'firmas/validar_firma_form.html')
