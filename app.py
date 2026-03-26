from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import gspread
from google.oauth2.service_account import Credentials
import os
import json
from datetime import datetime
import csv
import io
from sib_api_v3_sdk import Configuration, ApiClient, TransactionalEmailsApi, SendSmtpEmail
from sib_api_v3_sdk.rest import ApiException

app = Flask(__name__)
CORS(app)

# Configuración de Google Sheets
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_sheets_client():
    """Inicializa el cliente de Google Sheets"""
    try:
        # Obtener credenciales desde variable de entorno
        creds_json = os.environ.get('GOOGLE_CREDENTIALS')
        if not creds_json:
            raise Exception("No se encontraron credenciales de Google")
        
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        return gspread.authorize(creds)
    except Exception as e:
        print(f"Error al conectar con Google Sheets: {e}")
        return None

def get_spreadsheet():
    """Obtiene la hoja de cálculo principal"""
    client = get_sheets_client()
    if not client:
        return None
    
    spreadsheet_id = os.environ.get('SPREADSHEET_ID')
    if not spreadsheet_id:
        raise Exception("No se encontró SPREADSHEET_ID")
    
    return client.open_by_key(spreadsheet_id)

# Configuración de Brevo (SendinBlue)
def get_brevo_api():
    """Inicializa la API de Brevo"""
    configuration = Configuration()
    configuration.api_key['api-key'] = os.environ.get('BREVO_API_KEY')
    return TransactionalEmailsApi(ApiClient(configuration))

@app.route('/')
def home():
    return jsonify({
        "status": "ok",
        "message": "Sistema de Gestión de Calificaciones - API activa"
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint de salud"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/api/cursos', methods=['GET'])
def get_cursos():
    """Obtiene la lista de cursos disponibles"""
    cursos = [
        "1ero Bachillerato Ciencias A",
        "1ero Bachillerato Ciencias B",
        "1ero Bachillerato Técnico",
        "2do Bachillerato Ciencias A",
        "2do Bachillerato Ciencias B",
        "2do Bachillerato Técnico",
        "3ero Bachillerato Ciencias A",
        "3ero Bachillerato Ciencias B",
        "3ero Bachillerato Técnico"
    ]
    return jsonify(cursos)

@app.route('/api/asignaturas', methods=['GET'])
def get_asignaturas():
    """Obtiene la lista de asignaturas disponibles"""
    asignaturas = [
        "Matemáticas",
        "Contabilidad General",
        "Emprendimiento y Gestión",
        "Herramientas informáticas empresariales",
        "Gestión Contable y Administración Financiera",
        "Gestión y Control Financiero",
        "Financiamiento e Inversión",
        "Legislación Tributaria Aplicada",
        "Planificación y Control Presupuestario",
        "Análisis Financiero"
    ]
    return jsonify(asignaturas)

@app.route('/api/periodos', methods=['GET'])
def get_periodos():
    """Obtiene la lista de periodos disponibles"""
    periodos = ["Trimestre 1", "Trimestre 2", "Trimestre 3"]
    return jsonify(periodos)

@app.route('/api/criterios', methods=['GET'])
def get_criterios():
    """Obtiene la lista de criterios disponibles"""
    criterios = ["Lecciones", "Tareas", "Actividad Grupal", "Extra 1", "Extra 2", "Firmas"]
    return jsonify(criterios)

@app.route('/api/nomina', methods=['GET'])
def get_nomina():
    """Obtiene la nómina de estudiantes de Google Sheets"""
    try:
        spreadsheet = get_spreadsheet()
        if not spreadsheet:
            return jsonify({"error": "No se pudo conectar con Google Sheets"}), 500
        
        # Buscar o crear hoja de nómina
        try:
            worksheet = spreadsheet.worksheet("Nomina")
        except:
            worksheet = spreadsheet.add_worksheet(title="Nomina", rows="100", cols="20")
            worksheet.update('A1:C1', [['Nombre', 'Correo', 'Teléfono']])
        
        # Obtener todos los datos
        data = worksheet.get_all_values()
        
        if len(data) <= 1:
            return jsonify([])
        
        # Convertir a lista de diccionarios
        headers = data[0]
        students = []
        for row in data[1:]:
            if len(row) >= 3 and row[0]:  # Si hay al menos nombre
                students.append({
                    "nombre": row[0],
                    "correo": row[1] if len(row) > 1 else "",
                    "telefono": row[2] if len(row) > 2 else ""
                })
        
        return jsonify(students)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/nomina', methods=['POST'])
def save_nomina():
    """Guarda la nómina de estudiantes en Google Sheets"""
    try:
        data = request.json
        students = data.get('students', [])
        
        spreadsheet = get_spreadsheet()
        if not spreadsheet:
            return jsonify({"error": "No se pudo conectar con Google Sheets"}), 500
        
        # Buscar o crear hoja de nómina
        try:
            worksheet = spreadsheet.worksheet("Nomina")
        except:
            worksheet = spreadsheet.add_worksheet(title="Nomina", rows="100", cols="20")
        
        # Limpiar hoja
        worksheet.clear()
        
        # Escribir encabezados
        worksheet.update('A1:C1', [['Nombre', 'Correo', 'Teléfono']])
        
        # Escribir estudiantes
        if students:
            rows = [[s.get('nombre', ''), s.get('correo', ''), s.get('telefono', '')] for s in students]
            worksheet.update(f'A2:C{len(rows) + 1}', rows)
        
        return jsonify({"success": True, "message": "Nómina guardada correctamente"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/calificaciones', methods=['GET'])
def get_calificaciones():
    """Obtiene las calificaciones de Google Sheets"""
    try:
        curso = request.args.get('curso')
        asignatura = request.args.get('asignatura')
        periodo = request.args.get('periodo')
        criterio = request.args.get('criterio')
        
        if not all([curso, asignatura, periodo, criterio]):
            return jsonify({"error": "Faltan parámetros"}), 400
        
        spreadsheet = get_spreadsheet()
        if not spreadsheet:
            return jsonify({"error": "No se pudo conectar con Google Sheets"}), 500
        
        # Nombre de la hoja basado en los parámetros
        sheet_name = f"{curso}_{asignatura}_{periodo}_{criterio}".replace(" ", "_")
        
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except:
            # Si no existe, retornar estructura vacía
            return jsonify({
                "students": [],
                "dates": []
            })
        
        # Obtener todos los datos
        data = worksheet.get_all_values()
        
        if len(data) <= 1:
            return jsonify({
                "students": [],
                "dates": []
            })
        
        # Primera fila son las fechas
        dates = []
        for i in range(2, len(data[0])):  # Omitir columnas 0 (Número) y 1 (Estudiante)
            date_str = data[0][i] if len(data[0]) > i else ""
            dates.append(date_str)
        
        # Resto son estudiantes y notas
        students = []
        for row in data[1:]:
            if len(row) > 1 and row[1]:  # Si hay nombre de estudiante
                notas = []
                for i in range(2, min(len(row), 22)):  # Máximo 20 notas
                    nota = row[i] if len(row) > i else ""
                    notas.append(nota)
                
                students.append({
                    "numero": row[0] if len(row) > 0 else "",
                    "nombre": row[1],
                    "notas": notas
                })
        
        return jsonify({
            "students": students,
            "dates": dates
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/calificaciones', methods=['POST'])
def save_calificaciones():
    """Guarda las calificaciones en Google Sheets"""
    try:
        data = request.json
        curso = data.get('curso')
        asignatura = data.get('asignatura')
        periodo = data.get('periodo')
        criterio = data.get('criterio')
        students = data.get('students', [])
        dates = data.get('dates', [])
        
        if not all([curso, asignatura, periodo, criterio]):
            return jsonify({"error": "Faltan parámetros"}), 400
        
        spreadsheet = get_spreadsheet()
        if not spreadsheet:
            return jsonify({"error": "No se pudo conectar con Google Sheets"}), 500
        
        # Nombre de la hoja basado en los parámetros
        sheet_name = f"{curso}_{asignatura}_{periodo}_{criterio}".replace(" ", "_")
        
        # Buscar o crear hoja
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except:
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows="50", cols="22")
        
        # Limpiar hoja
        worksheet.clear()
        
        # Preparar encabezados
        headers = ['Número', 'Estudiante'] + dates[:20]
        worksheet.update('A1:V1', [headers])
        
        # Preparar y escribir datos de estudiantes
        if students:
            rows = []
            for i, student in enumerate(students, 1):
                row = [str(i), student.get('nombre', '')]
                notas = student.get('notas', [])
                row.extend(notas[:20])
                rows.append(row)
            
            worksheet.update(f'A2:V{len(rows) + 1}', rows)
        
        return jsonify({"success": True, "message": "Calificaciones guardadas correctamente"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/resumen', methods=['POST'])
def get_resumen():
    """Calcula el resumen de promedios por criterio y promedio final"""
    try:
        data = request.json
        curso = data.get('curso')
        asignatura = data.get('asignatura')
        periodo = data.get('periodo')
        
        if not all([curso, asignatura, periodo]):
            return jsonify({"error": "Faltan parámetros"}), 400
        
        spreadsheet = get_spreadsheet()
        if not spreadsheet:
            return jsonify({"error": "No se pudo conectar con Google Sheets"}), 500
        
        criterios = ["Lecciones", "Tareas", "Actividad Grupal", "Extra 1", "Extra 2", "Firmas"]
        
        # Obtener nómina de estudiantes
        nomina_worksheet = spreadsheet.worksheet("Nomina")
        nomina_data = nomina_worksheet.get_all_values()
        estudiantes_nomina = [row[0] for row in nomina_data[1:] if row[0]]
        
        # Diccionario para almacenar promedios por estudiante
        estudiantes_promedios = {}
        
        for nombre in estudiantes_nomina:
            estudiantes_promedios[nombre] = {
                "nombre": nombre,
                "promedios_criterios": {},
                "promedio_final": 0,
                "correo": "",
                "telefono": ""
            }
        
        # Obtener correos y teléfonos de la nómina
        for i, row in enumerate(nomina_data[1:]):
            if len(row) >= 3 and row[0]:
                nombre = row[0]
                if nombre in estudiantes_promedios:
                    estudiantes_promedios[nombre]['correo'] = row[1] if len(row) > 1 else ""
                    estudiantes_promedios[nombre]['telefono'] = row[2] if len(row) > 2 else ""
        
        # Obtener calificaciones de cada criterio
        for criterio in criterios:
            sheet_name = f"{curso}_{asignatura}_{periodo}_{criterio}".replace(" ", "_")
            
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
                data_sheet = worksheet.get_all_values()
                
                if len(data_sheet) > 1:
                    for row in data_sheet[1:]:
                        if len(row) > 1 and row[1]:
                            nombre = row[1]
                            if nombre in estudiantes_promedios:
                                # Obtener notas (columnas 2 en adelante)
                                notas = []
                                for i in range(2, len(row)):
                                    try:
                                        nota = float(row[i]) if row[i] else None
                                        if nota is not None:
                                            # Regla especial para Firmas
                                            if criterio == "Firmas":
                                                nota = (nota / 20) * 10
                                            notas.append(nota)
                                    except:
                                        pass
                                
                                # Calcular promedio del criterio
                                if notas:
                                    promedio = sum(notas) / len(notas)
                                    estudiantes_promedios[nombre]['promedios_criterios'][criterio] = round(promedio, 2)
            except:
                # Si no existe la hoja, continuar
                pass
        
        # Calcular promedio final
        for nombre, datos in estudiantes_promedios.items():
            promedios = list(datos['promedios_criterios'].values())
            if promedios:
                datos['promedio_final'] = round(sum(promedios) / len(promedios), 2)
        
        # Convertir a lista
        resultado = list(estudiantes_promedios.values())
        
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/enviar-alertas', methods=['POST'])
def enviar_alertas():
    """Envía alertas por correo a padres de estudiantes con promedio < 7"""
    try:
        data = request.json
        estudiantes = data.get('estudiantes', [])
        curso = data.get('curso', '')
        asignatura = data.get('asignatura', '')
        periodo = data.get('periodo', '')
        
        if not estudiantes:
            return jsonify({"success": True, "message": "No hay estudiantes con promedio menor a 7"})
        
        # Configurar Brevo
        api_instance = get_brevo_api()
        
        enviados = 0
        errores = []
        
        for estudiante in estudiantes:
            nombre = estudiante.get('nombre', '')
            correo = estudiante.get('correo', '')
            promedio = estudiante.get('promedio_final', 0)
            promedios_criterios = estudiante.get('promedios_criterios', {})
            
            if not correo or '@' not in correo:
                errores.append(f"{nombre}: correo inválido")
                continue
            
            # Construir detalle de promedios
            detalle_promedios = ""
            for criterio, promedio_crit in promedios_criterios.items():
                detalle_promedios += f"• {criterio}: {promedio_crit}/10\n"
            
            # Crear mensaje
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #d32f2f; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background-color: #f5f5f5; }}
                    .footer {{ padding: 15px; text-align: center; font-size: 12px; color: #666; }}
                    .alert {{ background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 15px 0; }}
                    .promedio {{ font-size: 24px; font-weight: bold; color: #d32f2f; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Alerta Académica</h1>
                    </div>
                    <div class="content">
                        <p>Estimados padres de familia,</p>
                        
                        <div class="alert">
                            <p><strong>Le informamos que su hijo/a {nombre} requiere apoyo académico.</strong></p>
                        </div>
                        
                        <p><strong>Detalles:</strong></p>
                        <ul>
                            <li><strong>Curso:</strong> {curso}</li>
                            <li><strong>Asignatura:</strong> {asignatura}</li>
                            <li><strong>Periodo:</strong> {periodo}</li>
                        </ul>
                        
                        <p><strong>Promedio final:</strong> <span class="promedio">{promedio}/10</span></p>
                        
                        <p><strong>Detalle por criterio:</strong></p>
                        <pre style="background: white; padding: 10px; border-radius: 5px;">{detalle_promedios}</pre>
                        
                        <p>Le recomendamos programar una reunión con el docente para establecer un plan de mejora académica.</p>
                        
                        <p>Atentamente,<br>
                        Departamento Académico</p>
                    </div>
                    <div class="footer">
                        <p>Este es un mensaje automático del sistema de gestión académica.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Enviar correo
            try:
                send_smtp_email = SendSmtpEmail(
                    to=[{"email": correo}],
                    html_content=html_content,
                    sender={"name": "Sistema Académico", "email": os.environ.get('SENDER_EMAIL', 'noreply@example.com')},
                    subject=f"Alerta Académica - {nombre} - {asignatura}"
                )
                
                api_instance.send_transac_email(send_smtp_email)
                enviados += 1
            except ApiException as e:
                errores.append(f"{nombre}: {str(e)}")
        
        mensaje = f"Se enviaron {enviados} correos correctamente."
        if errores:
            mensaje += f" Errores: {', '.join(errores)}"
        
        return jsonify({"success": True, "message": mensaje, "enviados": enviados})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generar-csv', methods=['POST'])
def generar_csv():
    """Genera un archivo CSV para envío de WhatsApp"""
    try:
        data = request.json
        estudiantes = data.get('estudiantes', [])
        curso = data.get('curso', '')
        asignatura = data.get('asignatura', '')
        periodo = data.get('periodo', '')
        
        if not estudiantes:
            return jsonify({"error": "No hay estudiantes con promedio menor a 7"}), 400
        
        # Crear CSV en memoria
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Encabezados
        writer.writerow(['Nombre', 'Teléfono', 'Mensaje'])
        
        # Escribir datos
        for estudiante in estudiantes:
            nombre = estudiante.get('nombre', '')
            telefono = estudiante.get('telefono', '')
            promedio = estudiante.get('promedio_final', 0)
            
            if not telefono:
                continue
            
            mensaje = (
                f"Estimados padres de {nombre}. "
                f"Le informamos que en {asignatura} ({periodo}) "
                f"su hijo/a obtuvo un promedio de {promedio}/10. "
                f"Se requiere refuerzo académico. "
                f"Por favor, contacte al docente para más información."
            )
            
            writer.writerow([nombre, telefono, mensaje])
        
        # Convertir a bytes
        output.seek(0)
        csv_data = output.getvalue()
        
        # Crear archivo en memoria
        mem_file = io.BytesIO()
        mem_file.write(csv_data.encode('utf-8-sig'))  # UTF-8 con BOM para Excel
        mem_file.seek(0)
        
        return send_file(
            mem_file,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'alertas_whatsapp_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
