# Caja Finanzas — Despliegue a Producción 🚀

Este repositorio contiene un sistema financiero integrado por un Backend (Flask) que sirve de webhook para WhatsApp y expone una API, y un Frontend (React/Vite) que funciona como un Dashboard web para el usuario.

## 1. Backend (Despliegue en Railway)

El backend está preparado para funcionar en plataformas como Railway, Heroku o Render, mediante Nixpacks o Docker.

### Variables de Entorno Requeridas en Producción

Para que el servidor en producción arranque exitosamente (`ProductionConfig`), debes configurar las siguientes variables:

* `FLASK_ENV`: `production`
* `SECRET_KEY`: Una cadena segura aleatoria (ej. generada con `openssl rand -hex 32`).
* `JWT_SECRET_KEY`: Otra cadena segura para firmar los tokens del Dashboard.
* `DATABASE_URL`: URL de conexión a PostgreSQL (provista por Railway, ej. `postgresql://user:pass@host:port/db`).
* `FRONTEND_URL`: La URL pública donde se desplegará el frontend (ej. `https://mi-dashboard.vercel.app`). Sirve para configurar el **CORS**.
* `OPENAI_API_KEY`: Tu clave de OpenAI.
* `SUPABASE_URL`: La URL de tu proyecto en Supabase.
* `SUPABASE_KEY`: Tu clave de API de Supabase (Service Role Key preferentemente, o Anon Key si las políticas lo permiten).
* `SUPABASE_BUCKET_RECEIPTS`: Nombre de tu bucket (por defecto `receipts`).
* `WHATSAPP_TOKEN`: El token permanente de la API de Cloud de WhatsApp.
* `WHATSAPP_VERIFY_TOKEN`: El token de verificación para el webhook (tú lo defines en Meta).
* `WHATSAPP_PHONE_NUMBER_ID`: El ID del número de teléfono en Meta.

### Comandos de Despliegue

Railway leerá automáticamente el archivo `Procfile` y ejecutará:
```bash
flask db upgrade && flask seed-db && gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 run:app
```
Esto asegurará que las migraciones de base de datos se ejecuten y se cree la base de datos de ser necesario antes de iniciar el servidor de producción `gunicorn`.

> **Nota para Docker**: Si Railway detecta y prefiere usar el `Dockerfile`, el script `entrypoint.sh` se ejecutará. El script fue modificado para usar `gunicorn` si `FLASK_ENV=production`.

---

## 2. Frontend (Despliegue en Vercel)

El Frontend está desarrollado con React, Vite y TailwindCSS. Se recomienda desplegarlo como un proyecto independiente en Vercel o Netlify.

### Variables de Entorno Requeridas
* `VITE_API_URL`: La URL pública de tu backend en Railway apuntando a `/api` (ej. `https://mi-backend-railway.app/api`).

### Configuración en Vercel
1. Conecta el repositorio de GitHub a Vercel.
2. Selecciona la carpeta `frontend/` como *Root Directory* (o configúralo en los comandos).
3. **Framework Preset**: Vite.
4. **Build Command**: `npm run build`
5. **Output Directory**: `dist`
6. Añade la variable `VITE_API_URL` en las *Environment Variables*.

---

## 3. Configuración en Meta for Developers

Una vez desplegado el Backend, debes ir al portal de Meta y configurar el Webhook:
1. **Callback URL**: `https://<tu-backend-railway>.app/api/webhook`
2. **Verify Token**: El mismo que colocaste en la variable `WHATSAPP_VERIFY_TOKEN`.
3. Suscríbete al evento `messages`.

## ¡Todo Listo!
Con estas configuraciones, tu asistente y tu dashboard estarán funcionando perfectamente en producción.
