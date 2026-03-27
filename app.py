from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import gspread
from google.oauth2.service_account import Credentials
import os
import json
import bcrypt
from functools import wraps
import requests
import pandas as pd
import io
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuración de SECRET_KEY
if os.environ.get("RENDER"):
    app.secret_key = os.environ.get("SECRET_KEY")
    if not app.secret_key:
        logger.critical("❌ SECRET_KEY no configurada en producción")
        raise ValueError(
            "CRITICAL: SECRET_KEY debe estar configurada en Render.\n"
            "Ve a: Dashboard → Environment → Add Secret → SECRET_KEY"
        )
    logger.info("✅ SECRET_KEY cargada desde variable de entorno")
else:
    import secrets
    app.secret_key = secrets.token_hex(32)
    logger.warning("⚠️  Usando SECRET_KEY temporal para desarrollo local")

# Configuración de PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///local.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)

# Modelo de Usuario
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

# Inicializar base de datos y crear usuario inicial
def init_db():
    with app.app_context():
        db.create_all()
        
        # Crear usuario inicial si no existe
        usuario_existente = Usuario.query.filter_by(username=os.environ.get("APP_USUARIO", "eddy")).first()
        if not usuario_existente:
            nuevo_usuario = Usuario(username=os.environ.get("APP_USUARIO", "eddy"))
            
            # Usar contraseña de APP_PASSWORD o fallback
            password_inicial = os.environ.get("APP_PASSWORD", "admin123")
            nuevo_usuario.set_password(password_inicial)
            
            db.session.add(nuevo_usuario)
            db.session.commit()
            logger.info(f"✅ Usuario inicial creado: {nuevo_usuario.username}")
        else:
            logger.info(f"✅ Usuario ya existe: {usuario_existente.username}")

# Inicializar DB al inicio
try:
    init_db()
except Exception as e:
    logger.error(f"Error al inicializar base de datos: {e}")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
TRIMESTRES = ["Trimestre 1", "Trimestre 2", "Trimestre 3"]
CRITERIOS_COMPLETOS = ["Lecciones", "Tareas", "Act. Grupal", "Extra 1", "Extra 2", "Firmas"]
LISTA_CURSOS = [
    "1ero Bachillerato Ciencias A", "1ero Bachillerato Ciencias B", "1ero Bachillerato Técnico",
    "2do Bachillerato Ciencias A",  "2do Bachillerato Ciencias B",  "2do Bachillerato Técnico",
    "3ero Bachillerato Ciencias A", "3ero Bachillerato Ciencias B", "3ero Bachillerato Técnico"
]
LISTA_ASIGNATURAS = [
    "Matemáticas", "Emprendimiento y Gestión", "Herramientas Informáticas Empresariales",
    "Gestión Contable y Administración Financiera", "Gestión y Control Financiero",
    "Financiamiento e Inversión", "Legislación tributaria aplicada",
    "Planificación y Control Presupuestario", "Análisis Financiero"
]
MESES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
         "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
ANIOS = [str(a) for a in range(2026, 2031)]
DIAS = [str(d).zfill(2) for d in range(1, 32)]
MAX_COLUMNAS = 20
NOMBRE_SPREADSHEET = "BD-Notas"
HOJA_NOMINAS = "NOMINAS"
HOJA_RESUMEN = "RESUMEN_GENERAL"
PROMEDIO_MINIMO = 7.0

TELEFONO_CONFIG = {
    "regex_ecuador": r"^5939\d{8}$",
    "formato_visual": "5939XXXXXXXX",
    "mensaje_error": "El teléfono debe tener formato ecuatoriano: 5939XXXXXXXX (12 dígitos)"
}

def validar_telefono_ecuador(telefono):
    import re
    
    if not telefono or not isinstance(telefono, str):
        return {"valido": True, "valor": "", "error": None}
    
    telefono_limpio = telefono.strip()
    
    if telefono_limpio == "":
        return {"valido": True, "valor": "", "error": None}
    
    if not re.match(TELEFONO_CONFIG["regex_ecuador"], telefono_limpio):
        return {
            "valido": False,
            "valor": telefono_limpio,
            "error": TELEFONO_CONFIG["mensaje_error"]
        }
    
    return {"valido": True, "valor": telefono_limpio, "error": None}

def validar_curso(curso):
    if not isinstance(curso, str):
        raise ValueError("El curso debe ser texto")
    
    curso_limpio = curso.strip()
    
    if not curso_limpio:
        raise ValueError("El curso no puede estar vacío")
    
    if curso_limpio not in LISTA_CURSOS:
        raise ValueError(f"El curso seleccionado no es válido")
    
    return curso_limpio

def validar_asignatura(asignatura):
    if not isinstance(asignatura, str):
        raise ValueError("La asignatura debe ser texto")
    
    asig_limpia = asignatura.strip()
    
    if not asig_limpia:
        raise ValueError("La asignatura no puede estar vacía")
    
    if asig_limpia not in LISTA_ASIGNATURAS:
        raise ValueError(f"La asignatura seleccionada no es válida")
    
    return asig_limpia

def validar_trimestre(trimestre):
    if not isinstance(trimestre, str):
        raise ValueError("El trimestre debe ser texto")
    
    tri_limpio = trimestre.strip()
    
    if tri_limpio not in TRIMESTRES:
        raise ValueError(f"El trimestre seleccionado no es válido")
    
    return tri_limpio

def validar_criterio(criterio):
    if not isinstance(criterio, str):
        raise ValueError("El criterio debe ser texto")
    
    crit_limpio = criterio.strip()
    
    if crit_limpio not in CRITERIOS_COMPLETOS:
        raise ValueError(f"El criterio seleccionado no es válido")
    
    return crit_limpio

def validar_nombre_estudiante(nombre):
    import re
    
    if not isinstance(nombre, str):
        raise ValueError("El nombre debe ser texto")
    
    nombre_limpio = nombre.strip()
    
    if len(nombre_limpio) < 3:
        raise ValueError("El nombre debe tener al menos 3 caracteres")
    
    if len(nombre_limpio) > 100:
        raise ValueError("El nombre es demasiado largo (máximo 100 caracteres)")
    
    if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s']+$", nombre_limpio):
        raise ValueError("El nombre contiene caracteres no permitidos")
    
    return nombre_limpio

def verificar_password(username, password):
    usuario = Usuario.query.filter_by(username=username).first()
    if usuario:
        return usuario.check_password(password)
    return False

def login_requerido(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("autenticado"):
            if request.is_json or request.method == "POST":
                return jsonify({"ok": False, "error": "No autorizado", "login": True}), 401
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("autenticado"):
        return redirect(url_for("index"))
    error = None
    if request.method == "POST":
        try:
            usuario  = request.form.get("usuario", "")
            password = request.form.get("password", "")
            
            if verificar_password(usuario, password):
                session["autenticado"] = True
                session["usuario"] = usuario
                logger.info(f"✅ Login exitoso: {usuario}")
                return redirect(url_for("index"))
            
            logger.warning(f"⚠️  Intento de login fallido: {usuario}")
            error = "Usuario o contraseña incorrectos"
        except Exception as e:
            logger.exception("Error en proceso de login")
            error = "Error al procesar el inicio de sesión"
    
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    usuario = session.get("usuario", "desconocido")
    session.clear()
    logger.info(f"🚪 Logout: {usuario}")
    return redirect(url_for("login"))

@app.route("/cambiar_password", methods=["POST"])
@login_requerido
def cambiar_password():
    try:
        data = request.json
        password_actual = data.get("password_actual", "")
        password_nueva = data.get("password_nueva", "")
        password_confirmar = data.get("password_confirmar", "")
        
        username = session.get('usuario')
        usuario = Usuario.query.filter_by(username=username).first()
        
        if not usuario or not usuario.check_password(password_actual):
            logger.warning(f"⚠️  Intento de cambio de contraseña con clave actual incorrecta: {username}")
            return jsonify({"ok": False, "error": "La contraseña actual es incorrecta"})
        
        if len(password_nueva) < 6:
            return jsonify({"ok": False, "error": "La nueva contraseña debe tener al menos 6 caracteres"})
        
        if password_nueva != password_confirmar:
            return jsonify({"ok": False, "error": "Las contraseñas nuevas no coinciden"})
        
        # Guardar nueva contraseña en BD
        usuario.set_password(password_nueva)
        usuario.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"🔑 Contraseña cambiada exitosamente para: {username}")
        
        return jsonify({"ok": True, "mensaje": "Contraseña cambiada exitosamente"})
        
    except KeyError as e:
        logger.warning(f"Datos incompletos en cambiar_password: {e}")
        return jsonify({"ok": False, "error": "Datos incompletos en la solicitud"}), 400
    except Exception as e:
        logger.exception("Error inesperado en cambiar_password")
        return jsonify({"ok": False, "error": "Ocurrió un error al cambiar la contraseña"}), 500

@app.route("/")
@login_requerido
def index():
    try:
        return render_template("index.html",
            trimestres=TRIMESTRES, criterios=CRITERIOS_COMPLETOS,
            cursos=LISTA_CURSOS, asignaturas=LISTA_ASIGNATURAS,
            meses=MESES, anios=ANIOS, dias=DIAS,
            max_columnas=MAX_COLUMNAS,
            usuario=session.get("usuario", "")
        )
    except Exception as e:
        logger.exception("Error al cargar página principal")
        return "Error al cargar la aplicación. Por favor, contacta al administrador.", 500

def get_cliente_gspread():
    try:
        creds_json = os.environ.get("GOOGLE_CREDENTIALS")
        if creds_json:
            creds = Credentials.from_service_account_info(json.loads(creds_json), scopes=SCOPES)
        else:
            creds = Credentials.from_service_account_file("credenciales.json", scopes=SCOPES)
        return gspread.authorize(creds)
    except json.JSONDecodeError as e:
        logger.error(f"Error al parsear GOOGLE_CREDENTIALS: {e}")
        raise ValueError("Credenciales de Google mal formateadas")
    except FileNotFoundError:
        logger.error("Archivo credenciales.json no encontrado")
        raise FileNotFoundError("Credenciales de Google no encontradas")
    except Exception as e:
        logger.exception("Error al obtener cliente de Google Sheets")
        raise

def get_nombre_hoja(curso, asig, crit, tri):
    c = curso.replace("Bachillerato","B").replace(" Ciencias ","C").replace(" Técnico","T").replace(" ","")
    a = "".join([p[:3] for p in asig.split()][:3])
    t = tri[-1] if tri else "1"
    return f"{c}_{a}_{crit[:4]}_T{t}"[:100]

def get_o_crear_hoja(spreadsheet, nombre_hoja):
    try:
        return spreadsheet.worksheet(nombre_hoja)
    except gspread.exceptions.WorksheetNotFound:
        logger.info(f"📝 Creando nueva hoja: {nombre_hoja}")
        return spreadsheet.add_worksheet(title=nombre_hoja, rows=35, cols=28)

def calcular_promedio(lista_notas):
    nums = []
    for n in lista_notas:
        try:
            nums.append(float(str(n).strip()))
        except (ValueError, TypeError):
            pass
    return round(sum(nums) / len(nums), 2) if nums else 0.0

def enviar_correo_alerta(correo_destino, nombre_estudiante, curso, asignatura, promedio):
    brevo_api_key = os.environ.get("BREVO_API_KEY", "")
    if not brevo_api_key:
        logger.error("BREVO_API_KEY no configurada")
        return False, "Servicio de correo no configurado"
    
    asunto = f"Alerta Academica - {nombre_estudiante}"
    cuerpo_html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
        <h2 style="color: #c0392b;">Alerta Academica</h2>
        <p>Estimado/a representante,</p>
        <p>Le informamos que el/la estudiante <strong>{nombre_estudiante}</strong> presenta un promedio
        <strong style="color: #c0392b;">por debajo del minimo requerido (7.00)</strong>.</p>
        <table style="width:100%; border-collapse: collapse; margin: 16px 0;">
            <tr style="background:#f5f5f5;">
                <td style="padding:8px; border:1px solid #ddd;"><strong>Estudiante</strong></td>
                <td style="padding:8px; border:1px solid #ddd;">{nombre_estudiante}</td>
            </tr>
            <tr>
                <td style="padding:8px; border:1px solid #ddd;"><strong>Curso</strong></td>
                <td style="padding:8px; border:1px solid #ddd;">{curso}</td>
            </tr>
            <tr style="background:#f5f5f5;">
                <td style="padding:8px; border:1px solid #ddd;"><strong>Asignatura</strong></td>
                <td style="padding:8px; border:1px solid #ddd;">{asignatura}</td>
            </tr>
            <tr>
                <td style="padding:8px; border:1px solid #ddd;"><strong>Promedio Actual</strong></td>
                <td style="padding:8px; border:1px solid #ddd; color:#c0392b;"><strong>{promedio}</strong></td>
            </tr>
        </table>
        <p>Le pedimos que se comunique con el docente o la institucion para coordinar un plan de mejora.</p>
        <p style="color: #888; font-size: 0.85em;">Este es un mensaje automatico del Sistema SYSEDDY.</p>
    </div>
    """
    try:
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={"api-key": brevo_api_key, "Content-Type": "application/json"},
            json={
                "sender": {"name": "SYSEDDY", "email": "ejvt593@gmail.com"},
                "to": [{"email": correo_destino}],
                "subject": asunto,
                "htmlContent": cuerpo_html
            },
            timeout=10
        )
        if response.status_code == 201:
            logger.info(f"✅ Correo enviado a {correo_destino} para {nombre_estudiante}")
            return True, "Correo enviado"
        else:
            logger.error(f"Error Brevo ({response.status_code}): {response.text}")
            return False, "Error al enviar el correo"
    except requests.exceptions.Timeout:
        logger.error(f"Timeout al enviar correo a {correo_destino}")
        return False, "Tiempo de espera agotado"
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de red al enviar correo: {e}")
        return False, "Error de conexión con el servicio de correo"
    except Exception as e:
        logger.exception(f"Error inesperado al enviar correo a {correo_destino}")
        return False, "Error inesperado al enviar correo"

@app.route("/cargar_estudiantes", methods=["POST"])
@login_requerido
def cargar_estudiantes():
    try:
        data = request.json
        curso = validar_curso(data.get("curso"))
        
        gc = get_cliente_gspread()
        sp = gc.open(NOMBRE_SPREADSHEET)
        
        nombres = []
        correos = {}
        telefonos = {}
        
        try:
            hoja = sp.worksheet(HOJA_NOMINAS)
            rows = hoja.get_all_values()
            
            for fila in rows[1:]:
                if len(fila) >= 2 and fila[0].strip() == curso.strip():
                    nombre   = fila[1].strip()
                    correo   = fila[2].strip() if len(fila) >= 3 else ""
                    telefono = fila[3].strip() if len(fila) >= 4 else ""
                    if nombre:
                        nombres.append(nombre)
                        correos[nombre]   = correo
                        telefonos[nombre] = telefono
            
            logger.info(f"📋 Cargados {len(nombres)} estudiantes de {curso} desde NOMINAS")
            
        except gspread.exceptions.WorksheetNotFound:
            logger.warning(f"Hoja NOMINAS no encontrada, buscando en hojas antiguas")
            for h in sp.worksheets():
                if h.title == HOJA_NOMINAS:
                    continue
                try:
                    datos = h.get_all_values()
                    if len(datos) > 1 and len(datos[0]) >= 3:
                        for fila in datos[1:]:
                            if len(fila) >= 3 and fila[0].strip() == curso.strip():
                                nombre = fila[2].strip()
                                if nombre and not nombre.startswith("Estudiante ") and nombre not in nombres:
                                    nombres.append(nombre)
                except:
                    pass
                if nombres:
                    break
        
        tiene_nomina = bool(nombres)
        
        if not nombres:
            logger.info(f"No hay nómina para {curso}, usando nombres por defecto")
            nombres = [f"Estudiante {i+1}" for i in range(30)]
        
        return jsonify({
            "ok": True,
            "nombres": nombres,
            "correos": correos,
            "telefonos": telefonos,
            "tiene_nomina": tiene_nomina
        })
        
    except ValueError as e:
        logger.warning(f"Validación fallida en cargar_estudiantes: {e}")
        return jsonify({"ok": False, "error": str(e)}), 400
    except gspread.exceptions.APIError as e:
        logger.error(f"Error API Google Sheets en cargar_estudiantes: {e}")
        return jsonify({
            "ok": False, 
            "error": "Google Sheets no está disponible temporalmente. Intenta en un momento."
        }), 503
    except Exception as e:
        logger.exception("Error inesperado en cargar_estudiantes")
        return jsonify({
            "ok": False, 
            "error": "Ocurrió un error al cargar los estudiantes. Intenta nuevamente."
        }), 500

@app.route("/cargar_notas", methods=["POST"])
@login_requerido
def cargar_notas():
    try:
        data = request.json
        curso = validar_curso(data.get("curso"))
        asig  = validar_asignatura(data.get("asignatura"))
        tri   = validar_trimestre(data.get("trimestre"))
        crit  = validar_criterio(data.get("criterio"))
        
        nombre_hoja = get_nombre_hoja(curso, asig, crit, tri)
        
        gc = get_cliente_gspread()
        sp = gc.open(NOMBRE_SPREADSHEET)
        
        resultado = {"ok": True, "encontrado": False, "notas_por_estudiante": {}, "fechas": []}
        
        try:
            hoja  = sp.worksheet(nombre_hoja)
            datos = hoja.get_all_values()
            
            if len(datos) > 1:
                resultado["fechas"] = datos[0][4:]
                resultado["encontrado"] = True
                
                for fila in datos[1:]:
                    while len(fila) < 4 + MAX_COLUMNAS:
                        fila.append("")
                    nombre = fila[2].strip()
                    if nombre:
                        resultado["notas_por_estudiante"][nombre] = fila[4:4 + MAX_COLUMNAS]
                
                logger.info(f"📖 Notas cargadas: {curso} | {asig} | {crit} | {tri}")
            else:
                logger.info(f"Hoja vacía: {nombre_hoja}")
                
        except gspread.exceptions.WorksheetNotFound:
            logger.info(f"No existe hoja para: {nombre_hoja}")
            pass
        
        return jsonify(resultado)
        
    except ValueError as e:
        logger.warning(f"Validación fallida en cargar_notas: {e}")
        return jsonify({"ok": False, "error": str(e)}), 400
    except gspread.exceptions.APIError as e:
        logger.error(f"Error API Google Sheets en cargar_notas: {e}")
        return jsonify({
            "ok": False,
            "error": "Google Sheets no está disponible temporalmente. Intenta en un momento."
        }), 503
    except Exception as e:
        logger.exception("Error inesperado en cargar_notas")
        return jsonify({
            "ok": False,
            "error": "Ocurrió un error al cargar las notas. Intenta nuevamente."
        }), 500

@app.route("/guardar", methods=["POST"])
@login_requerido
def guardar():
    try:
        data = request.json
        curso = validar_curso(data.get("curso"))
        asig  = validar_asignatura(data.get("asignatura"))
        tri   = validar_trimestre(data.get("trimestre"))
        crit  = validar_criterio(data.get("criterio"))
        
        fechas = data.get("fechas", [])
        estudiantes = data.get("estudiantes", [])
        
        if not isinstance(fechas, list):
            raise ValueError("Las fechas deben ser una lista")
        
        if not isinstance(estudiantes, list):
            raise ValueError("Los estudiantes deben ser una lista")
        
        nombre_hoja = get_nombre_hoja(curso, asig, crit, tri)
        
        gc   = get_cliente_gspread()
        sp   = gc.open(NOMBRE_SPREADSHEET)
        hoja = get_o_crear_hoja(sp, nombre_hoja)
        
        encabezados = ["CURSO", "TRIMESTRE", "Estudiante", "CRITERIO"] + fechas
        filas = [encabezados] + [[curso, tri, est["nombre"], crit] + est["notas"] for est in estudiantes]
        
        hoja.clear()
        hoja.update("A1", filas)
        
        logger.info(f"💾 Guardado exitoso: {curso} | {asig} | {crit} | {tri} ({len(estudiantes)} estudiantes)")
        
        return jsonify({
            "ok": True, 
            "mensaje": f"Guardado correctamente → {curso} | {crit} | {tri}"
        })
        
    except ValueError as e:
        logger.warning(f"Validación fallida en guardar: {e}")
        return jsonify({"ok": False, "error": str(e)}), 400
    except gspread.exceptions.APIError as e:
        logger.error(f"Error API Google Sheets en guardar: {e}")
        return jsonify({
            "ok": False,
            "error": "Google Sheets no está disponible. No se pudieron guardar los datos."
        }), 503
    except KeyError as e:
        logger.warning(f"Datos incompletos en guardar: {e}")
        return jsonify({
            "ok": False,
            "error": f"Faltan datos requeridos en la solicitud"
        }), 400
    except Exception as e:
        logger.exception("Error inesperado en guardar")
        return jsonify({
            "ok": False,
            "error": "Ocurrió un error al guardar. Intenta nuevamente."
        }), 500

@app.route("/resumen", methods=["POST"])
@login_requerido
def resumen():
    try:
        data = request.json
        curso   = validar_curso(data.get("curso"))
        asig    = validar_asignatura(data.get("asignatura"))
        tri     = validar_trimestre(data.get("trimestre"))
        nombres = data.get("nombres", [])
        
        if not isinstance(nombres, list):
            raise ValueError("Los nombres deben ser una lista")
        
        gc = get_cliente_gspread()
        sp = gc.open(NOMBRE_SPREADSHEET)
        
        tri_num = tri[-1]
        hojas_disponibles = {h.title for h in sp.worksheets()}
        
        datos_criterio = {}
        maximo_firmas  = 1.0
        
        for crit in CRITERIOS_COMPLETOS:
            nombre_hoja = get_nombre_hoja(curso, asig, crit, tri_num)
            datos_criterio[crit] = {}
            
            if nombre_hoja not in hojas_disponibles:
                continue
            
            hoja  = sp.worksheet(nombre_hoja)
            filas = hoja.get_all_values()
            
            if len(filas) <= 1:
                continue
            
            if crit == "Firmas":
                vals = []
                for fila in filas[1:]:
                    if len(fila) > 4 and fila[0].strip() == curso.strip():
                        try:
                            vals.append(float(fila[4]))
                        except:
                            pass
                maximo_firmas = max(vals) if vals else 1.0
                if maximo_firmas == 0:
                    maximo_firmas = 1.0
                
                for fila in filas[1:]:
                    if len(fila) >= 3 and fila[0].strip() == curso.strip():
                        nombre = fila[2].strip()
                        try:
                            nota_cruda = float(fila[4]) if len(fila) > 4 and fila[4].strip() else 0
                            datos_criterio[crit][nombre] = round((nota_cruda * 10) / maximo_firmas, 2)
                        except:
                            datos_criterio[crit][nombre] = 0.0
            else:
                for fila in filas[1:]:
                    if len(fila) >= 3 and fila[0].strip() == curso.strip():
                        datos_criterio[crit][fila[2].strip()] = calcular_promedio(fila[4:])
        
        resumen_data  = []
        filas_resumen = [["CURSO", "TRIMESTRE", "Asignatura", "Estudiante",
                          "Lecciones", "Tareas", "Act. Grupal", "Extra 1", "Extra 2", "Firmas", "Promedio Final"]]
        
        for nombre in nombres:
            proms = [datos_criterio[crit].get(nombre, 0.0) for crit in CRITERIOS_COMPLETOS]
            validos    = [p for p in proms if p > 0]
            prom_final = round(sum(validos) / len(validos), 2) if validos else 0.0
            
            resumen_data.append({"nombre": nombre, "proms": proms, "prom_final": prom_final})
            filas_resumen.append([curso, tri, asig, nombre] + [str(p) for p in proms] + [str(prom_final)])
        
        try:
            hoja_res = get_o_crear_hoja(sp, HOJA_RESUMEN)
            todos = hoja_res.get_all_values()
            otras = [f for f in todos[1:] if not (len(f) >= 3 and f[0].strip() == curso and f[1].strip() == tri and f[2].strip() == asig)]
            
            hoja_res.clear()
            hoja_res.update("A1", [filas_resumen[0]] + otras + filas_resumen[1:])
            
            logger.info(f"📊 Resumen generado: {curso} | {asig} | {tri} ({len(resumen_data)} estudiantes)")
        except Exception as e:
            logger.warning(f"No se pudo actualizar hoja RESUMEN_GENERAL: {e}")
        
        return jsonify({"ok": True, "data": resumen_data})
        
    except ValueError as e:
        logger.warning(f"Validación fallida en resumen: {e}")
        return jsonify({"ok": False, "error": str(e)}), 400
    except gspread.exceptions.APIError as e:
        logger.error(f"Error API Google Sheets en resumen: {e}")
        return jsonify({
            "ok": False,
            "error": "Google Sheets no está disponible temporalmente. Intenta en un momento."
        }), 503
    except Exception as e:
        logger.exception("Error inesperado en resumen")
        return jsonify({
            "ok": False,
            "error": "Ocurrió un error al generar el resumen. Intenta nuevamente."
        }), 500

@app.route("/enviar_alertas", methods=["POST"])
@login_requerido
def enviar_alertas():
    try:
        data = request.json
        curso       = validar_curso(data.get("curso"))
        asignatura  = validar_asignatura(data.get("asignatura"))
        estudiantes = data.get("estudiantes", [])
        
        if not isinstance(estudiantes, list):
            raise ValueError("Los estudiantes deben ser una lista")
        
        resultados = []
        enviados = 0
        errores = 0
        
        for est in estudiantes:
            nombre = est.get("nombre", "")
            prom   = est.get("prom_final", 0.0)
            correo = est.get("correo", "")
            
            if prom < PROMEDIO_MINIMO and prom > 0:
                if not correo:
                    resultados.append({
                        "nombre": nombre,
                        "estado": "sin_correo",
                        "mensaje": "No tiene correo de representante registrado"
                    })
                    errores += 1
                    continue
                
                ok, msg = enviar_correo_alerta(correo, nombre, curso, asignatura, prom)
                
                if ok:
                    enviados += 1
                    resultados.append({"nombre": nombre, "estado": "enviado", "correo": correo})
                else:
                    errores += 1
                    resultados.append({"nombre": nombre, "estado": "error", "mensaje": msg})
        
        logger.info(f"📧 Alertas enviadas: {enviados} exitosos, {errores} con errores")
        
        return jsonify({
            "ok": True,
            "enviados": enviados,
            "errores": errores,
            "detalle": resultados
        })
        
    except ValueError as e:
        logger.warning(f"Validación fallida en enviar_alertas: {e}")
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        logger.exception("Error inesperado en enviar_alertas")
        return jsonify({
            "ok": False,
            "error": "Ocurrió un error al enviar las alertas. Intenta nuevamente."
        }), 500

@app.route("/crear_nomina", methods=["POST"])
@login_requerido
def crear_nomina():
    try:
        data = request.json
        curso = validar_curso(data.get("curso"))
        nombres_raw = data.get("nombres", [])
        
        if not isinstance(nombres_raw, list):
            raise ValueError("Los nombres deben ser una lista")
        
        nombres_validados = []
        for item in nombres_raw:
            if isinstance(item, dict):
                nombre_input = item.get("nombre", "").strip()
                correo_input = item.get("correo", "").strip()
                telefono_input = item.get("telefono", "").strip()
                
                try:
                    nombre = validar_nombre_estudiante(nombre_input)
                except ValueError as e:
                    logger.warning(f"Nombre inválido rechazado: {nombre_input} - {e}")
                    return jsonify({"ok": False, "error": str(e)}), 400
                
                resultado_tel = validar_telefono_ecuador(telefono_input)
                if not resultado_tel["valido"]:
                    logger.warning(f"Teléfono inválido rechazado: {telefono_input}")
                    return jsonify({
                        "ok": False,
                        "error": f"Teléfono inválido para {nombre}: {resultado_tel['error']}"
                    }), 400
                
                nombres_validados.append({
                    "nombre": nombre,
                    "correo": correo_input,
                    "telefono": resultado_tel["valor"]
                })
            else:
                nombre = validar_nombre_estudiante(str(item).strip())
                nombres_validados.append({
                    "nombre": nombre,
                    "correo": "",
                    "telefono": ""
                })
        
        if not nombres_validados:
            raise ValueError("La nómina está vacía")
        
        gc = get_cliente_gspread()
        sp = gc.open(NOMBRE_SPREADSHEET)
        
        hoja_nominas = get_o_crear_hoja(sp, HOJA_NOMINAS)
        todos = hoja_nominas.get_all_values()
        otras_filas = [f for f in todos[1:] if len(f) >= 1 and f[0].strip() != curso.strip()]
        
        filas_curso = []
        for item in nombres_validados:
            filas_curso.append([curso, item["nombre"], item["correo"], item["telefono"]])
        
        hoja_nominas.clear()
        hoja_nominas.update("A1",
            [["CURSO", "Nombre", "Correo_Representante", "Telefono"]] + otras_filas + filas_curso)
        
        logger.info(f"📝 Nómina guardada: {curso} con {len(filas_curso)} estudiantes")
        
        return jsonify({
            "ok": True,
            "mensaje": f"Nómina de {curso} guardada con {len(filas_curso)} estudiantes."
        })
        
    except ValueError as e:
        logger.warning(f"Validación fallida en crear_nomina: {e}")
        return jsonify({"ok": False, "error": str(e)}), 400
    except gspread.exceptions.APIError as e:
        logger.error(f"Error API Google Sheets en crear_nomina: {e}")
        return jsonify({
            "ok": False,
            "error": "Google Sheets no está disponible. No se pudo guardar la nómina."
        }), 503
    except Exception as e:
        logger.exception("Error inesperado en crear_nomina")
        return jsonify({
            "ok": False,
            "error": "Ocurrió un error al guardar la nómina. Intenta nuevamente."
        }), 500

@app.route("/importar_nomina", methods=["POST"])
@login_requerido
def importar_nomina():
    try:
        if 'file' not in request.files:
            return jsonify({"ok": False, "error": "No se recibió ningún archivo"}), 400

        archivo = request.files['file']
        nombre_archivo = archivo.filename.lower()

        if nombre_archivo.endswith('.xlsx'):
            df = pd.read_excel(io.BytesIO(archivo.read()))
        elif nombre_archivo.endswith('.csv'):
            contenido = archivo.read()
            try:
                df = pd.read_csv(io.BytesIO(contenido), encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(io.BytesIO(contenido), encoding='latin-1')
        else:
            return jsonify({
                "ok": False,
                "error": "Formato no soportado. Use archivos .xlsx o .csv"
            }), 400

        df.columns = [str(c).strip().lower() for c in df.columns]

        col_nombre   = next((c for c in df.columns if 'nombre' in c), None)
        col_correo   = next((c for c in df.columns if 'correo' in c or 'email' in c or 'mail' in c), None)
        col_telefono = next((c for c in df.columns if 'tel' in c or 'phone' in c or 'movil' in c or 'celular' in c), None)

        if not col_nombre:
            return jsonify({
                "ok": False,
                "error": "No se encontró columna 'Nombre' en el archivo"
            }), 400

        estudiantes = []
        for idx, row in df.iterrows():
            nombre = str(row.get(col_nombre, '') or '').strip().title()
            if not nombre or nombre.lower() in ('nan', 'none', ''):
                continue
            
            correo   = str(row.get(col_correo,   '') or '').strip().lower() if col_correo   else ''
            telefono = str(row.get(col_telefono, '') or '').strip()         if col_telefono else ''
            
            telefono = ''.join(filter(str.isdigit, telefono))
            
            if correo   in ('nan', 'none'): correo   = ''
            if telefono in ('nan', 'none'): telefono = ''
            
            estudiantes.append({"nombre": nombre, "correo": correo, "telefono": telefono})

        if not estudiantes:
            return jsonify({
                "ok": False,
                "error": "El archivo no contiene filas válidas con nombres"
            }), 400
        
        logger.info(f"📂 Importados {len(estudiantes)} estudiantes desde archivo")

        return jsonify({
            "ok": True,
            "estudiantes": estudiantes,
            "total": len(estudiantes)
        })

    except pd.errors.EmptyDataError:
        logger.warning("Archivo vacío en importar_nomina")
        return jsonify({"ok": False, "error": "El archivo está vacío"}), 400
    except pd.errors.ParserError as e:
        logger.error(f"Error al parsear archivo: {e}")
        return jsonify({
            "ok": False,
            "error": "El archivo no tiene un formato válido"
        }), 400
    except Exception as e:
        logger.exception("Error inesperado en importar_nomina")
        return jsonify({
            "ok": False,
            "error": "Ocurrió un error al importar el archivo. Verifica el formato."
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🚀 Iniciando SYSEDDY en puerto {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
