# 🚀 GUÍA RÁPIDA DE INICIO

## Checklist de Despliegue

### ✅ Pre-requisitos (10 minutos)
- [ ] Cuenta de Google (Gmail)
- [ ] Cuenta de GitHub
- [ ] Cuenta de Render
- [ ] Cuenta de Brevo

### ✅ Configuración de Google (15 minutos)
1. [ ] Crear proyecto en Google Cloud Console
2. [ ] Habilitar Google Sheets API y Google Drive API
3. [ ] Crear cuenta de servicio
4. [ ] Descargar archivo JSON de credenciales
5. [ ] Crear Google Sheet
6. [ ] Copiar ID del Sheet (de la URL)
7. [ ] Compartir Sheet con email de la cuenta de servicio

### ✅ Configuración de Brevo (5 minutos)
1. [ ] Registrarse en Brevo
2. [ ] Generar API Key
3. [ ] Verificar email remitente

### ✅ GitHub (5 minutos)
1. [ ] Crear repositorio "sistema-calificaciones"
2. [ ] Subir todos los archivos del proyecto

### ✅ Render (10 minutos)
1. [ ] Crear Web Service
2. [ ] Conectar repositorio de GitHub
3. [ ] Configurar variables de entorno:
   - `GOOGLE_CREDENTIALS`
   - `SPREADSHEET_ID`
   - `BREVO_API_KEY`
   - `SENDER_EMAIL`
4. [ ] Desplegar

### ✅ Primer Uso (5 minutos)
1. [ ] Abrir URL de la aplicación
2. [ ] Ir a "Gestionar Nómina"
3. [ ] Agregar 2-3 estudiantes de prueba
4. [ ] Guardar nómina
5. [ ] Ir a "Registro de Calificaciones"
6. [ ] Seleccionar parámetros
7. [ ] Cargar calificaciones
8. [ ] Ingresar algunas notas de prueba
9. [ ] Guardar
10. [ ] Ir a "Resumen General"
11. [ ] Generar resumen

## ⚡ Comandos Rápidos (si usas Git local)

```bash
# Clonar o crear repositorio
git init
git add .
git commit -m "Sistema de calificaciones completo"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/sistema-calificaciones.git
git push -u origin main

# Actualizar después de cambios
git add .
git commit -m "Descripción del cambio"
git push
```

## 🔗 Enlaces Útiles

- Google Cloud Console: https://console.cloud.google.com/
- Google Sheets: https://sheets.google.com/
- Brevo: https://www.brevo.com/
- GitHub: https://github.com/
- Render: https://render.com/

## 📞 ¿Problemas?

1. **Aplicación no carga**: Revisa logs en Render
2. **Error con Google Sheets**: Verifica que el Sheet esté compartido con la cuenta de servicio
3. **Emails no se envían**: Verifica API Key de Brevo y email remitente

## 💡 Tips

- La app en plan gratuito de Render se "duerme" después de 15 min de inactividad
- El primer acceso después de dormir tarda ~30 segundos
- Brevo gratuito: 300 emails/día
- Google Sheets: 10 millones de celdas (suficiente para miles de estudiantes)

## 🎯 Flujo de Trabajo Recomendado

1. **Al inicio del periodo escolar**: Cargar toda la nómina
2. **Semanalmente**: Registrar calificaciones por criterio
3. **Mensualmente**: Generar resumen y enviar alertas
4. **Fin de periodo**: Exportar reportes finales

---

**¡Tiempo total estimado de configuración: ~45 minutos!**
