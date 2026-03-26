# Sistema Eddy - Registro de Calificaciones Web

## Archivos del proyecto
```
sistema-notas-web/
├── app.py              ← Backend Flask (lógica del servidor)
├── requirements.txt    ← Librerías Python necesarias
├── Procfile            ← Configuración para Render.com
├── credenciales.json   ← TU ARCHIVO JSON (NO subir a GitHub)
└── templates/
    └── index.html      ← Frontend (interfaz web)
```

## PASOS PARA PONERLO A FUNCIONAR

### 1. Instalar dependencias (en tu computadora)
```bash
pip install -r requirements.txt
```

### 2. Agregar tus credenciales
- Renombra tu archivo JSON descargado de Google Cloud a: `credenciales.json`
- Colócalo en la misma carpeta que `app.py`

### 3. Probar localmente
```bash
python app.py
```
Abre tu navegador en: http://localhost:5000

### 4. Subir a GitHub
- Crea un repositorio en github.com
- IMPORTANTE: Agrega un archivo `.gitignore` con:
  ```
  credenciales.json
  __pycache__/
  *.pyc
  ```
- Sube todos los archivos EXCEPTO `credenciales.json`

### 5. Desplegar en Render.com (GRATIS)
1. Ve a https://render.com y crea cuenta
2. Clic en "New Web Service"
3. Conecta tu repositorio de GitHub
4. Configuración:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
5. En "Environment Variables" agrega:
   - Key: `GOOGLE_CREDENTIALS`
   - Value: pega TODO el contenido de tu archivo `credenciales.json`
6. Clic en "Deploy"

## IMPORTANTE - Seguridad
- NUNCA subas `credenciales.json` a GitHub
- Usa siempre la variable de entorno en producción
