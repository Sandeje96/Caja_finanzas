# 💬 Finanzas IA WhatsApp

> Asistente financiero personal conversacional. Registrá gastos, ingresos y comprobantes simplemente hablando por WhatsApp.

---

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Flask 3 + SQLAlchemy + Alembic |
| Base de datos | PostgreSQL 15 |
| IA | OpenAI GPT-4o-mini |
| Canal | WhatsApp Cloud API |
| Storage | Supabase Storage (bucket privado) |
| Frontend | React + Vite + TailwindCSS + Recharts |
| Deploy | Railway |

---

## Inicio Rápido (Docker)

```bash
# 1. Clonar el repositorio
git clone <repo-url>
cd finanzas-ia-whatsapp

# 2. Levantar backend + base de datos
docker compose up --build

# 3. Verificar que el backend está corriendo
curl http://localhost:5000/api/health
```

El primer inicio:
1. Construye la imagen Docker del backend
2. Espera a que PostgreSQL esté listo (healthcheck)
3. Ejecuta las migraciones (`flask db upgrade`)
4. Siembra las categorías iniciales (`flask seed-db`)
5. Inicia Flask en modo desarrollo con hot-reload

---

## Variables de Entorno

Copiá el archivo de ejemplo y completá tus credenciales reales:

```bash
cp backend/.env.example backend/.env
```

Las variables requeridas para producción están documentadas en `backend/.env.example`.

> Para desarrollo local con Docker, **no es necesario** crear `.env`.  
> Los valores de desarrollo están en `docker-compose.yml`.

---

## Estructura del Proyecto

```
finanzas-ia-whatsapp/
├── backend/                    # Flask API
│   ├── app/
│   │   ├── api/                # Endpoints HTTP (Blueprint por módulo)
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── repositories/       # Capa de acceso a datos
│   │   ├── services/           # Lógica de negocio
│   │   ├── prompts/            # Templates de prompts para OpenAI
│   │   └── utils/              # Validadores, decorators, helpers
│   ├── migrations/             # Alembic migrations
│   └── tests/
├── frontend/                   # React + Vite dashboard
└── docker-compose.yml
```

---

## Endpoints disponibles (MVP actual)

| Método | Ruta | Estado |
|--------|------|--------|
| `GET` | `/api/health` | ✅ Implementado |
| `GET` | `/api/webhook` | ✅ Verificación WhatsApp |
| `POST` | `/api/webhook` | 🔧 Sprint 2 |
| `POST` | `/api/auth/login` | 🔧 Sprint 6 |
| `GET` | `/api/transactions` | 🔧 Sprint 5 |
| `GET` | `/api/dashboard/summary` | 🔧 Sprint 5 |

---

## Comandos útiles

```bash
# Ejecutar solo la base de datos
docker compose up db

# Ver logs del backend
docker compose logs -f backend

# Correr las migraciones manualmente
docker compose exec backend flask db upgrade

# Sembrar categorías iniciales
docker compose exec backend flask seed-db

# Crear una nueva migración
docker compose exec backend flask db migrate -m "descripcion del cambio"

# Abrir psql en el contenedor
docker compose exec db psql -U finanzas_user -d finanzas_ia
```

---

## Roadmap

- **Sprint 1** ✅ Estructura + modelos + migraciones + /health
- **Sprint 2** 🔧 Canal WhatsApp + deduplicación + usuarios
- **Sprint 3** 🔧 Motor IA (OpenAI) + registro de gastos/ingresos
- **Sprint 4** 🔧 Comprobantes (Supabase Storage)
- **Sprint 5** 🔧 Consultas financieras
- **Sprint 6** 🔧 Autenticación JWT del dashboard
- **Sprint 7** 🔧 Dashboard React
- **Sprint 8** 🔧 Testing + deploy Railway

---

## Filosofía

> El dashboard es secundario. La experiencia conversacional es el producto.

Todo el diseño asume que el usuario usa WhatsApp el 90% del tiempo.  
Ver los documentos de arquitectura: `CLAUDE.md` y `PROJECT_CONTEXT.md`.
