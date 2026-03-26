# 📡 Documentación de la API

## Base URL

```
Producción: https://tu-app.onrender.com
Local: http://localhost:5000
```

## Endpoints

### 1. Health Check

**GET** `/api/health`

Verifica el estado del servidor.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00"
}
```

---

### 2. Obtener Cursos

**GET** `/api/cursos`

Retorna la lista de cursos disponibles.

**Response:**
```json
[
  "1ero Bachillerato Ciencias A",
  "1ero Bachillerato Ciencias B",
  "1ero Bachillerato Técnico",
  ...
]
```

---

### 3. Obtener Asignaturas

**GET** `/api/asignaturas`

Retorna la lista de asignaturas disponibles.

**Response:**
```json
[
  "Matemáticas",
  "Contabilidad General",
  "Emprendimiento y Gestión",
  ...
]
```

---

### 4. Obtener Periodos

**GET** `/api/periodos`

Retorna la lista de periodos disponibles.

**Response:**
```json
[
  "Trimestre 1",
  "Trimestre 2",
  "Trimestre 3"
]
```

---

### 5. Obtener Criterios

**GET** `/api/criterios`

Retorna la lista de criterios de evaluación.

**Response:**
```json
[
  "Lecciones",
  "Tareas",
  "Actividad Grupal",
  "Extra 1",
  "Extra 2",
  "Firmas"
]
```

---

### 6. Obtener Nómina

**GET** `/api/nomina`

Retorna la lista de estudiantes registrados.

**Response:**
```json
[
  {
    "nombre": "Juan Pérez",
    "correo": "juan@ejemplo.com",
    "telefono": "0999999999"
  },
  ...
]
```

---

### 7. Guardar Nómina

**POST** `/api/nomina`

Guarda la nómina de estudiantes en Google Sheets.

**Request Body:**
```json
{
  "students": [
    {
      "nombre": "Juan Pérez",
      "correo": "juan@ejemplo.com",
      "telefono": "0999999999"
    },
    ...
  ]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Nómina guardada correctamente"
}
```

---

### 8. Obtener Calificaciones

**GET** `/api/calificaciones`

Retorna las calificaciones para un curso, asignatura, periodo y criterio específicos.

**Query Parameters:**
- `curso` (string, requerido)
- `asignatura` (string, requerido)
- `periodo` (string, requerido)
- `criterio` (string, requerido)

**Ejemplo:**
```
/api/calificaciones?curso=1ero%20Bachillerato%20Ciencias%20A&asignatura=Matemáticas&periodo=Trimestre%201&criterio=Lecciones
```

**Response:**
```json
{
  "students": [
    {
      "numero": "1",
      "nombre": "Juan Pérez",
      "notas": ["8.5", "9.0", "7.5", ...]
    },
    ...
  ],
  "dates": ["01/03/2024", "08/03/2024", ...]
}
```

---

### 9. Guardar Calificaciones

**POST** `/api/calificaciones`

Guarda las calificaciones en Google Sheets.

**Request Body:**
```json
{
  "curso": "1ero Bachillerato Ciencias A",
  "asignatura": "Matemáticas",
  "periodo": "Trimestre 1",
  "criterio": "Lecciones",
  "students": [
    {
      "numero": "1",
      "nombre": "Juan Pérez",
      "notas": ["8.5", "9.0", "7.5", ...]
    },
    ...
  ],
  "dates": ["01/03/2024", "08/03/2024", ...]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Calificaciones guardadas correctamente"
}
```

---

### 10. Generar Resumen

**POST** `/api/resumen`

Calcula el resumen de promedios por criterio y promedio final.

**Request Body:**
```json
{
  "curso": "1ero Bachillerato Ciencias A",
  "asignatura": "Matemáticas",
  "periodo": "Trimestre 1"
}
```

**Response:**
```json
[
  {
    "nombre": "Juan Pérez",
    "correo": "juan@ejemplo.com",
    "telefono": "0999999999",
    "promedios_criterios": {
      "Lecciones": 8.5,
      "Tareas": 7.8,
      "Actividad Grupal": 9.0,
      "Extra 1": 8.2,
      "Extra 2": 7.5,
      "Firmas": 9.0
    },
    "promedio_final": 8.33
  },
  ...
]
```

**Nota:** Para el criterio "Firmas", el sistema automáticamente convierte la escala. Si un estudiante tiene 20 firmas, se muestra como 10.0 en el promedio.

---

### 11. Enviar Alertas por Email

**POST** `/api/enviar-alertas`

Envía alertas por correo electrónico a padres de estudiantes con promedio < 7.

**Request Body:**
```json
{
  "estudiantes": [
    {
      "nombre": "María López",
      "correo": "padres.maria@ejemplo.com",
      "promedio_final": 6.5,
      "promedios_criterios": {
        "Lecciones": 7.0,
        "Tareas": 6.5,
        ...
      }
    },
    ...
  ],
  "curso": "1ero Bachillerato Ciencias A",
  "asignatura": "Matemáticas",
  "periodo": "Trimestre 1"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Se enviaron 5 correos correctamente.",
  "enviados": 5
}
```

---

### 12. Generar CSV para WhatsApp

**POST** `/api/generar-csv`

Genera un archivo CSV con datos para envío masivo por WhatsApp.

**Request Body:**
```json
{
  "estudiantes": [
    {
      "nombre": "María López",
      "telefono": "0999999999",
      "promedio_final": 6.5
    },
    ...
  ],
  "curso": "1ero Bachillerato Ciencias A",
  "asignatura": "Matemáticas",
  "periodo": "Trimestre 1"
}
```

**Response:**
Archivo CSV con las columnas:
- Nombre
- Teléfono
- Mensaje

---

## Códigos de Error

### 400 - Bad Request
Faltan parámetros requeridos o datos inválidos.

### 500 - Internal Server Error
Error del servidor (problemas con Google Sheets o Brevo).

---

## Ejemplo de Uso con JavaScript

```javascript
// Obtener cursos
const cursos = await fetch('https://tu-app.onrender.com/api/cursos')
  .then(r => r.json());

// Guardar calificaciones
const resultado = await fetch('https://tu-app.onrender.com/api/calificaciones', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    curso: '1ero Bachillerato Ciencias A',
    asignatura: 'Matemáticas',
    periodo: 'Trimestre 1',
    criterio: 'Lecciones',
    students: [...],
    dates: [...]
  })
}).then(r => r.json());

// Descargar CSV
const response = await fetch('https://tu-app.onrender.com/api/generar-csv', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ estudiantes: [...], curso: '...', ... })
});
const blob = await response.blob();
const url = window.URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = 'alertas.csv';
a.click();
```

---

## Notas Técnicas

### Almacenamiento en Google Sheets

El sistema crea automáticamente hojas en el Google Sheet con el siguiente formato de nombre:

```
{curso}_{asignatura}_{periodo}_{criterio}
```

Por ejemplo:
```
1ero_Bachillerato_Ciencias_A_Matemáticas_Trimestre_1_Lecciones
```

### Formato de Emails

Los emails enviados son HTML con formato profesional, incluyendo:
- Nombre del estudiante
- Curso, asignatura y periodo
- Promedio final destacado
- Detalle de promedios por criterio
- Mensaje formal para los padres

### Límites y Restricciones

- **Google Sheets**: 10 millones de celdas por hoja
- **Brevo (plan gratuito)**: 300 emails por día
- **Render (plan gratuito)**: La app se duerme después de 15 min de inactividad

---

## Seguridad

- Todas las credenciales se almacenan como variables de entorno
- No se exponen credenciales en el código
- Comunicación sobre HTTPS en producción
- CORS configurado para permitir el frontend

---

## Contacto y Soporte

Para reportar problemas o sugerencias, crear un issue en el repositorio de GitHub.
