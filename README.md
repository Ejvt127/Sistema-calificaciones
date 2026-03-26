# 📚 Sistema de Gestión de Calificaciones

Sistema web completo para gestión de calificaciones de bachillerato con integración a Google Sheets, envío de alertas por email y generación de reportes.

## 🎯 Características

- ✅ Registro de calificaciones por curso, asignatura, periodo y criterio
- ✅ Gestión de nómina de estudiantes
- ✅ Cálculo automático de promedios
- ✅ Envío de alertas por email a padres de familia
- ✅ Generación de archivos CSV para WhatsApp
- ✅ Integración con Google Sheets como base de datos
- ✅ Interfaz moderna y responsive

## 📋 Requisitos Previos

Antes de comenzar, necesitarás:

1. Una cuenta de Google (Gmail)
2. Una cuenta de GitHub
3. Una cuenta de Render (gratuita)
4. Una cuenta de Brevo/SendinBlue (gratuita) para envío de emails

## 🚀 Guía de Despliegue Paso a Paso

### PASO 1: Configurar Google Sheets API

1. **Ir a Google Cloud Console**
   - Accede a: https://console.cloud.google.com/
   - Inicia sesión con tu cuenta de Google

2. **Crear un nuevo proyecto**
   - Haz clic en "Seleccionar proyecto" (arriba)
   - Clic en "Nuevo proyecto"
   - Nombre: "Sistema-Calificaciones"
   - Clic en "Crear"

3. **Habilitar APIs necesarias**
   - Ve a "APIs y servicios" → "Biblioteca"
   - Busca y habilita:
     * Google Sheets API
     * Google Drive API

4. **Crear credenciales**
   - Ve a "APIs y servicios" → "Credenciales"
   - Clic en "Crear credenciales" → "Cuenta de servicio"
   - Nombre: "sistema-calificaciones-sa"
   - Clic en "Crear y continuar"
   - Rol: "Editor"
   - Clic en "Continuar" y "Listo"

5. **Descargar clave JSON**
   - Haz clic en la cuenta de servicio creada
   - Ve a la pestaña "Claves"
   - Clic en "Agregar clave" → "Crear nueva clave"
   - Tipo: JSON
   - Clic en "Crear" (se descargará un archivo JSON)
   - **¡GUARDA ESTE ARCHIVO! Lo necesitarás después**

6. **Crear Google Sheet**
   - Ve a: https://sheets.google.com/
   - Crea una nueva hoja de cálculo
   - Nómbrala: "Sistema-Calificaciones-DB"
   - Copia el ID de la hoja (está en la URL):
     ```
     https://docs.google.com/spreadsheets/d/[ESTE_ES_EL_ID]/edit
     ```
   - **Compartir la hoja:**
     * Clic en "Compartir" (arriba derecha)
     * Pega el email de la cuenta de servicio (está en el archivo JSON que descargaste, campo "client_email")
     * Permiso: "Editor"
     * Clic en "Enviar"

### PASO 2: Configurar Brevo (para envío de emails)

1. **Crear cuenta en Brevo**
   - Ve a: https://www.brevo.com/
   - Regístrate gratis (plan gratuito: 300 emails/día)

2. **Obtener API Key**
   - Inicia sesión en Brevo
   - Ve a tu perfil (arriba derecha) → "SMTP & API"
   - Pestaña "API Keys"
   - Clic en "Generate a new API key"
   - Nombre: "Sistema-Calificaciones"
   - Clic en "Generate"
   - **¡COPIA Y GUARDA ESTA CLAVE!**

3. **Configurar dominio de envío**
   - Ve a "Senders & IP"
   - Agrega tu email como remitente y verifica

### PASO 3: Subir código a GitHub

1. **Crear repositorio en GitHub**
   - Ve a: https://github.com/
   - Clic en "New repository" (verde)
   - Nombre: "sistema-calificaciones"
   - Descripción: "Sistema de gestión de calificaciones"
   - Público o Privado (tu elección)
   - Clic en "Create repository"

2. **Subir archivos**
   - Opción A (interfaz web):
     * En la página del repositorio, clic en "uploading an existing file"
     * Arrastra los archivos: `app.py`, `index.html`, `requirements.txt`, `README.md`
     * Clic en "Commit changes"
   
   - Opción B (Git desde terminal):
     ```bash
     git init
     git add .
     git commit -m "Initial commit"
     git branch -M main
     git remote add origin https://github.com/TU_USUARIO/sistema-calificaciones.git
     git push -u origin main
     ```

### PASO 4: Desplegar en Render

1. **Crear cuenta en Render**
   - Ve a: https://render.com/
   - Regístrate (puedes usar tu cuenta de GitHub)

2. **Crear nuevo Web Service**
   - Desde el dashboard, clic en "New +"
   - Selecciona "Web Service"
   - Conecta tu repositorio de GitHub
   - Selecciona el repositorio "sistema-calificaciones"

3. **Configurar el servicio**
   - Name: `sistema-calificaciones`
   - Region: Elige la más cercana (Oregon - US West)
   - Branch: `main`
   - Runtime: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Plan: **Free** (¡es gratis!)

4. **Configurar Variables de Entorno**
   - En "Environment Variables", agrega las siguientes variables:
   
   ```
   GOOGLE_CREDENTIALS
   ```
   Valor: El contenido completo del archivo JSON de credenciales de Google (todo el JSON como una sola línea o tal cual)
   
   ```
   SPREADSHEET_ID
   ```
   Valor: El ID de tu Google Sheet (que copiaste antes)
   
   ```
   BREVO_API_KEY
   ```
   Valor: Tu API Key de Brevo (que copiaste antes)
   
   ```
   SENDER_EMAIL
   ```
   Valor: El email que configuraste como remitente en Brevo (ej: tucorreo@gmail.com)

5. **Desplegar**
   - Clic en "Create Web Service"
   - Espera 3-5 minutos mientras Render despliega tu aplicación
   - ¡Listo! Tu aplicación estará en: `https://sistema-calificaciones-XXXX.onrender.com`

### PASO 5: Acceder al Sistema

1. **Abrir la aplicación**
   - Usa la URL que Render te proporcionó
   - Ejemplo: `https://sistema-calificaciones-xxxx.onrender.com`

2. **Primer uso**
   - Ve a "Gestionar Nómina"
   - Agrega estudiantes
   - Guarda la nómina
   - Ve a "Registro de Calificaciones"
   - Selecciona curso, asignatura, periodo y criterio
   - Carga las calificaciones
   - Ingresa las notas
   - Guarda

3. **Generar reportes**
   - Ve a "Resumen General"
   - Selecciona parámetros
   - Genera resumen
   - Envía alertas o descarga CSV

## 🔧 Solución de Problemas

### Error: "No se pudo conectar con Google Sheets"
- Verifica que las credenciales JSON estén correctamente configuradas en Render
- Asegúrate de que la hoja de Google esté compartida con la cuenta de servicio

### Error: "Error al enviar emails"
- Verifica tu API Key de Brevo
- Asegúrate de que el email remitente esté verificado
- Revisa que no hayas excedido el límite del plan gratuito (300 emails/día)

### La aplicación no carga
- Revisa los logs en Render (Dashboard → tu servicio → Logs)
- Verifica que todas las variables de entorno estén configuradas
- Asegúrate de que el build haya completado exitosamente

### Error: "Module not found"
- Verifica que `requirements.txt` esté en la raíz del repositorio
- Asegúrate de que el Build Command sea correcto: `pip install -r requirements.txt`

## 📱 Uso del Sistema

### Registro de Calificaciones
1. Selecciona Curso, Asignatura, Periodo y Criterio
2. Clic en "Cargar Calificaciones"
3. Ingresa las fechas en los encabezados (DD/MM/AAAA)
4. Ingresa las notas (escala 0-10)
5. Clic en "Guardar Calificaciones"

### Gestión de Nómina
1. Clic en "Agregar Estudiante" para cada nuevo estudiante
2. Ingresa: Nombre, Correo, Teléfono
3. Clic en "Guardar Nómina"
4. También puedes "Cargar Nómina" para ver estudiantes existentes

### Resumen y Alertas
1. Selecciona Curso, Asignatura y Periodo
2. Clic en "Generar Resumen"
3. Revisa promedios por criterio y promedio final
4. Para estudiantes con promedio < 7:
   - "Enviar Alertas Email": Envía correos automáticos a padres
   - "Descargar CSV WhatsApp": Genera archivo para envío masivo

## 🔒 Seguridad

- Las credenciales se almacenan como variables de entorno (nunca en el código)
- La comunicación es sobre HTTPS
- Los datos se almacenan en Google Sheets con acceso controlado

## 📞 Soporte

Si tienes problemas:
1. Revisa esta guía completa
2. Verifica los logs en Render
3. Asegúrate de seguir cada paso exactamente

## 🎓 Estructura del Proyecto

```
sistema-calificaciones/
│
├── app.py              # Backend Flask (API)
├── index.html          # Frontend completo
├── requirements.txt    # Dependencias Python
└── README.md          # Esta guía
```

## 🌟 Características Técnicas

- **Backend**: Python + Flask
- **Frontend**: HTML5 + CSS3 + JavaScript vanilla
- **Base de Datos**: Google Sheets
- **Emails**: Brevo API
- **Hosting**: Render
- **Versionado**: Git + GitHub

## 📝 Notas Importantes

1. **Plan Gratuito de Render**: La aplicación puede "dormir" después de 15 minutos de inactividad. El primer acceso después de dormir puede tardar 30-60 segundos.

2. **Límites de Brevo Gratuito**: 300 emails por día. Si necesitas más, considera el plan de pago.

3. **Google Sheets**: Límite de 10 millones de celdas por hoja. Suficiente para miles de estudiantes.

4. **Respaldos**: Google Sheets mantiene historial de cambios automáticamente.

## 🎉 ¡Listo!

Tu sistema está funcionando. Accede desde cualquier navegador y dispositivo.

**URL de tu sistema**: `https://tu-app.onrender.com`

---

Creado con ❤️ para educadores
