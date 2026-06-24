# Revisión Arquitectónica — Finanzas IA WhatsApp

> **Estado**: Pendiente de aprobación. No se ha escrito código todavía.

---

## 1. Análisis de los Documentos Fuente

Ambos documentos (CLAUDE.md y PROJECT_CONTEXT.md) son **coherentes en visión y filosofía**, pero presentan **ausencias arquitectónicas** que deben resolverse antes de escribir código. A continuación el análisis completo.

---

## 2. Inconsistencias Detectadas

| # | Problema | Ubicación | Impacto |
|---|----------|-----------|---------|
| 1 | La tabla `users` no tiene campo `is_active` ni `status` | CLAUDE.md modelo de datos | Sin forma de bloquear usuarios sin hard-delete |
| 2 | La tabla `categories` no tiene `user_id` | CLAUDE.md | Las categorías son globales, sin soporte para categorías personalizadas por usuario |
| 3 | La tabla `transactions` no tiene `message_id` | CLAUDE.md | Imposible trazar una transacción a la conversación que la originó |
| 4 | La tabla `attachments` no tiene `uploaded_by` ni `status` | CLAUDE.md | Sin control de estado de subida (pending/uploaded/failed) |
| 5 | No existe tabla `users_sessions` o similar para JWT | Ambos | Se menciona JWT pero no se define cómo se persisten los tokens del dashboard |
| 6 | La arquitectura en PROJECT_CONTEXT muestra el flujo en orden incorrecto | PROJECT_CONTEXT línea 50-74 | React → Flask → ... → WhatsApp Cloud API (debería ser bidireccional, no un stack secuencial) |
| 7 | No se menciona estrategia de reintentos para mensajes WhatsApp fallidos | Ambos | Si la API de WhatsApp falla, el mensaje se pierde silenciosamente |
| 8 | No se define qué pasa cuando la IA no puede clasificar la intención | Ambos | Sin fallback claro → experiencia de usuario rota |
| 9 | No se menciona idempotencia del webhook | Ambos | WhatsApp puede reenviar el mismo evento; sin deduplicación → transacciones duplicadas |
| 10 | La tabla `conversations` no tiene campo `is_active` | CLAUDE.md | Sin forma de saber cuál conversación está "abierta" actualmente |

---

## 3. Riesgos Identificados

### 🔴 Riesgos Críticos (bloquean MVP)

**R1 — Deduplicación de Webhooks**
WhatsApp Cloud API garantiza entrega *at-least-once*. Sin un campo `whatsapp_message_id` único en la tabla `messages`, el mismo gasto puede registrarse múltiples veces si WhatsApp reintenta el webhook.

**R2 — Contexto conversacional para la IA**
El documento dice "guardar todos los mensajes", pero no define cuántos mensajes se envían al contexto de OpenAI. Sin una estrategia de ventana de contexto, los costos de tokens crecen indefinidamente conforme el historial aumenta.

**R3 — Procesamiento síncrono del webhook**
El flujo propuesto (recibir → procesar IA → responder) es síncrono. OpenAI puede tardar 5-15 segundos. WhatsApp Cloud API requiere respuesta HTTP 200 en < 5 segundos. Si se procesa todo en el webhook, habrá timeouts.

### 🟡 Riesgos Moderados

**R4 — Manejo de archivos adjuntos grandes**
WhatsApp limita imágenes a 5MB y PDFs a 100MB. La descarga del archivo desde WhatsApp → subida a Supabase Storage debe ser asíncrona; si falla, el comprobante se pierde.

**R5 — Escalabilidad de categorías**
Las categorías son globales (sin `user_id`). En Fase 4 (multiusuario/empresas), cada cliente necesitará sus propias categorías. Agregar `user_id` después requiere una migración disruptiva.

**R6 — Autenticación sin refresh tokens**
Solo se menciona JWT. Sin refresh tokens, el usuario del dashboard deberá re-autenticarse frecuentemente o se usan tokens de larga duración (riesgo de seguridad).

---

## 4. Estructura de Carpetas Definitiva

```
finanzas-ia-whatsapp/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── extensions.py          # SQLAlchemy, Migrate, etc.
│   │   │
│   │   ├── api/                   # Capa HTTP — solo validar, delegar, responder
│   │   │   ├── __init__.py
│   │   │   ├── webhook.py         # GET+POST /webhook (WhatsApp)
│   │   │   ├── auth.py            # POST /auth/login, /auth/refresh
│   │   │   ├── transactions.py    # CRUD de transacciones (dashboard)
│   │   │   ├── categories.py      # CRUD categorías
│   │   │   ├── attachments.py     # Subida / visualización comprobantes
│   │   │   ├── conversations.py   # Historial conversacional (dashboard)
│   │   │   └── dashboard.py       # Endpoints de métricas y resúmenes
│   │   │
│   │   ├── services/              # Lógica de negocio
│   │   │   ├── __init__.py
│   │   │   ├── webhook_processor.py     # Orquesta el flujo completo
│   │   │   ├── conversation_service.py  # Gestión de conversaciones y contexto
│   │   │   ├── ai_service.py            # OpenAI: clasificación + extracción
│   │   │   ├── transaction_service.py   # CRUD + validaciones de negocio
│   │   │   ├── financial_summary_service.py  # Cálculos, balances, estadísticas
│   │   │   ├── attachment_service.py    # Descarga WhatsApp → sube a Storage
│   │   │   ├── whatsapp_service.py      # Envío de mensajes a WhatsApp API
│   │   │   ├── storage_service.py       # Abstracción Supabase/S3
│   │   │   └── auth_service.py          # JWT: login, refresh, verificación
│   │   │
│   │   ├── repositories/          # Acceso a datos — solo queries
│   │   │   ├── __init__.py
│   │   │   ├── base_repository.py
│   │   │   ├── user_repository.py
│   │   │   ├── conversation_repository.py
│   │   │   ├── message_repository.py
│   │   │   ├── transaction_repository.py
│   │   │   ├── category_repository.py
│   │   │   └── attachment_repository.py
│   │   │
│   │   ├── models/                # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── user.py
│   │   │   ├── conversation.py
│   │   │   ├── message.py
│   │   │   ├── category.py
│   │   │   ├── transaction.py
│   │   │   └── attachment.py
│   │   │
│   │   ├── prompts/               # Prompt templates (texto plano)
│   │   │   ├── system_prompt.txt
│   │   │   ├── intent_classifier.txt
│   │   │   ├── entity_extractor.txt
│   │   │   └── query_assistant.txt
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── validators.py
│   │       ├── decorators.py      # jwt_required, rate_limit, etc.
│   │       └── helpers.py
│   │
│   ├── migrations/                # Alembic
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   ├── .env.example
│   ├── requirements.txt
│   ├── Procfile                   # Para Railway
│   └── run.py
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/                # Botones, inputs, modales, badges
│   │   │   ├── charts/            # Wrappers de Recharts
│   │   │   └── layout/            # Sidebar, Header, Footer
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Transactions.tsx
│   │   │   ├── Attachments.tsx
│   │   │   ├── Statistics.tsx
│   │   │   └── Settings.tsx
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   ├── useTransactions.ts
│   │   │   └── useSummary.ts
│   │   ├── services/              # Llamadas a la API Flask
│   │   │   ├── api.ts             # Axios instance con interceptors
│   │   │   ├── authService.ts
│   │   │   └── transactionService.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   └── layouts/
│   │       └── DashboardLayout.tsx
│   ├── index.html
│   ├── vite.config.ts
│   └── tailwind.config.ts
│
├── .gitignore
└── README.md
```

---

## 5. Esquema PostgreSQL Completo

### Principios aplicados
- Todas las tablas tienen `id UUID PRIMARY KEY`, `created_at`, `updated_at`, `deleted_at`
- Soft delete con `deleted_at IS NULL` en todas las queries
- Índices en columnas frecuentes de filtro
- `whatsapp_message_id` para deduplicación

```sql
-- ─────────────────────────────────────────────
-- USERS
-- ─────────────────────────────────────────────
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone           VARCHAR(20) UNIQUE NOT NULL,   -- E.164: +5491112345678
    name            VARCHAR(100),
    email           VARCHAR(150) UNIQUE,            -- Para login en dashboard
    password_hash   VARCHAR(255),                   -- Nullable: solo si usa dashboard
    timezone        VARCHAR(50) DEFAULT 'America/Argentina/Buenos_Aires',
    currency        VARCHAR(10) DEFAULT 'ARS',
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

CREATE INDEX idx_users_phone     ON users(phone) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_email     ON users(email) WHERE deleted_at IS NULL;

-- ─────────────────────────────────────────────
-- CONVERSATIONS
-- ─────────────────────────────────────────────
CREATE TABLE conversations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id),
    is_active       BOOLEAN DEFAULT TRUE,           -- La sesión actual del usuario
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

CREATE INDEX idx_conversations_user_id  ON conversations(user_id) WHERE deleted_at IS NULL;

-- ─────────────────────────────────────────────
-- MESSAGES
-- ─────────────────────────────────────────────
CREATE TABLE messages (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id      UUID NOT NULL REFERENCES conversations(id),
    whatsapp_message_id  VARCHAR(100) UNIQUE,        -- Para deduplicación
    role                 VARCHAR(10) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content              TEXT NOT NULL,
    message_type         VARCHAR(20) DEFAULT 'text'
                         CHECK (message_type IN ('text', 'image', 'document', 'audio', 'video')),
    raw_payload          JSONB,                      -- Payload completo de WhatsApp (auditoría)
    created_at           TIMESTAMPTZ DEFAULT NOW(),
    updated_at           TIMESTAMPTZ DEFAULT NOW(),
    deleted_at           TIMESTAMPTZ
);

CREATE INDEX idx_messages_conversation_id        ON messages(conversation_id);
CREATE INDEX idx_messages_whatsapp_message_id    ON messages(whatsapp_message_id);
CREATE INDEX idx_messages_created_at             ON messages(created_at DESC);

-- ─────────────────────────────────────────────
-- CATEGORIES
-- ─────────────────────────────────────────────
CREATE TABLE categories (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES users(id),          -- NULL = categoría global del sistema
    name        VARCHAR(100) NOT NULL,
    type        VARCHAR(10) CHECK (type IN ('expense', 'income', 'both')) DEFAULT 'both',
    icon        VARCHAR(50),
    color       VARCHAR(7),                          -- Hex color: #FFFFFF
    is_system   BOOLEAN DEFAULT FALSE,               -- TRUE = categoría del sistema, no editable
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    deleted_at  TIMESTAMPTZ
);

CREATE INDEX idx_categories_user_id  ON categories(user_id) WHERE deleted_at IS NULL;

-- ─────────────────────────────────────────────
-- TRANSACTIONS
-- ─────────────────────────────────────────────
CREATE TABLE transactions (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID NOT NULL REFERENCES users(id),
    category_id      UUID REFERENCES categories(id),
    message_id       UUID REFERENCES messages(id),   -- Origen conversacional
    type             VARCHAR(20) NOT NULL
                     CHECK (type IN ('expense', 'income', 'transfer', 'adjustment')),
    amount           NUMERIC(15, 2) NOT NULL CHECK (amount > 0),
    description      TEXT,
    notes            TEXT,
    transaction_date DATE NOT NULL DEFAULT CURRENT_DATE,
    source           VARCHAR(20) DEFAULT 'whatsapp'
                     CHECK (source IN ('whatsapp', 'dashboard', 'import')),
    ai_confidence    NUMERIC(4, 3),                  -- 0.000 a 1.000: confianza de la IA
    is_confirmed     BOOLEAN DEFAULT TRUE,            -- Para futuras transacciones pendientes
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    updated_at       TIMESTAMPTZ DEFAULT NOW(),
    deleted_at       TIMESTAMPTZ
);

CREATE INDEX idx_transactions_user_id         ON transactions(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_transactions_date            ON transactions(user_id, transaction_date DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_transactions_type            ON transactions(user_id, type) WHERE deleted_at IS NULL;
CREATE INDEX idx_transactions_category_id     ON transactions(category_id) WHERE deleted_at IS NULL;

-- ─────────────────────────────────────────────
-- ATTACHMENTS
-- ─────────────────────────────────────────────
CREATE TABLE attachments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id  UUID REFERENCES transactions(id),  -- Nullable: puede subirse sin transacción
    user_id         UUID NOT NULL REFERENCES users(id),
    storage_path    VARCHAR(500) NOT NULL,
    public_url      TEXT,
    file_name       VARCHAR(255),
    mime_type       VARCHAR(100),
    file_size       INTEGER,                            -- Bytes
    status          VARCHAR(20) DEFAULT 'uploaded'
                    CHECK (status IN ('pending', 'uploaded', 'failed', 'processing')),
    whatsapp_media_id VARCHAR(100),                     -- ID de media de WhatsApp
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

CREATE INDEX idx_attachments_transaction_id  ON attachments(transaction_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_attachments_user_id         ON attachments(user_id) WHERE deleted_at IS NULL;

-- ─────────────────────────────────────────────
-- AI LOGS (control de costos y auditoría)
-- ─────────────────────────────────────────────
CREATE TABLE ai_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    message_id      UUID REFERENCES messages(id),
    intent          VARCHAR(50),                    -- Intención detectada
    prompt_tokens   INTEGER,
    completion_tokens INTEGER,
    total_tokens    INTEGER,
    model           VARCHAR(50),
    cost_usd        NUMERIC(10, 6),                 -- Costo estimado en USD
    latency_ms      INTEGER,
    success         BOOLEAN DEFAULT TRUE,
    error_message   TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ai_logs_user_id    ON ai_logs(user_id);
CREATE INDEX idx_ai_logs_created_at ON ai_logs(created_at DESC);
```

---

## 6. Arquitectura de Servicios

```
┌─────────────────────────────────────────────────────────┐
│                     WHATSAPP CLOUD API                   │
└────────────────────────────┬────────────────────────────┘
                             │ Webhook HTTP POST
                             ▼
┌─────────────────────────────────────────────────────────┐
│                    FLASK WEBHOOK ENDPOINT                │
│  • Valida firma HMAC                                     │
│  • Responde 200 inmediatamente                           │
│  • Encola el procesamiento (Task Queue)                  │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│                  WEBHOOK PROCESSOR SERVICE               │
│  1. Deduplica por whatsapp_message_id                    │
│  2. Identifica / registra al usuario por phone           │
│  3. Obtiene o crea conversación activa                   │
│  4. Persiste el mensaje entrante                         │
│  5. Prepara contexto (últimos N mensajes)                │
│  6. Llama a AI Service                                   │
│  7. Ejecuta acción según intención detectada             │
│  8. Persiste respuesta                                   │
│  9. Envía respuesta por WhatsApp                         │
└──────┬──────────────┬───────────────┬───────────────────┘
       │              │               │
       ▼              ▼               ▼
  AI Service    Transaction      Attachment
                  Service          Service
       │              │               │
       ▼              ▼               ▼
  OpenAI API    PostgreSQL       Storage (S3)
```

### Por qué Task Queue en MVP

El documento prioriza simplicidad. Para el MVP se usará **threading simple** (Python `threading.Thread`) para no bloquear el webhook. Si la carga crece, se migra a Celery + Redis sin cambiar la lógica de negocio.

---

## 7. Flujo WhatsApp → IA → PostgreSQL → Respuesta

```
Usuario WhatsApp: "gasté 18000 en supermercado"
         │
         ▼
[1] Webhook recibe el evento
    → Valida firma HMAC (X-Hub-Signature-256)
    → Responde HTTP 200 de inmediato
    → Lanza thread de procesamiento
         │
         ▼
[2] Deduplicación
    → Busca whatsapp_message_id en messages
    → Si ya existe: descarta silenciosamente
         │
         ▼
[3] Identificación de usuario
    → Busca por phone en users
    → Si no existe: crea usuario nuevo, envía mensaje de bienvenida
         │
         ▼
[4] Contexto conversacional
    → Obtiene conversación activa del usuario
    → Recupera los últimos 10 mensajes (ventana deslizante)
    → Construye la lista [{"role": "user/assistant", "content": "..."}]
         │
         ▼
[5] AI Service — Paso 1: Clasificación de intención
    → Envía: system_prompt + historial + mensaje actual
    → Modelo: gpt-4o-mini (económico, rápido)
    → Recibe JSON estructurado:
      {
        "intent": "REGISTER_EXPENSE",
        "amount": 18000,
        "category": "Supermercado",
        "description": "supermercado",
        "date": "2026-06-24",
        "confidence": 0.97
      }
         │
         ▼
[6] Business Logic según intención
    ┌─ REGISTER_EXPENSE / REGISTER_INCOME ─────────────────┐
    │  → TransactionService.create()                        │
    │  → Busca categoría por nombre (fuzzy match)           │
    │  → Persiste en transactions                           │
    │  → Genera texto de confirmación                       │
    └───────────────────────────────────────────────────────┘
    ┌─ QUERY ───────────────────────────────────────────────┐
    │  → FinancialSummaryService.query()                    │
    │  → Ejecuta SQL directo (no IA para sumas)             │
    │  → AI genera respuesta en lenguaje natural con datos  │
    └───────────────────────────────────────────────────────┘
    ┌─ ATTACH_RECEIPT ──────────────────────────────────────┐
    │  → AttachmentService.process()                        │
    │  → Descarga media de WhatsApp                         │
    │  → Sube a Supabase Storage                            │
    │  → Asocia al último movimiento compatible (< 24h)     │
    └───────────────────────────────────────────────────────┘
    ┌─ UNKNOWN ─────────────────────────────────────────────┐
    │  → Responde pidiendo aclaración                       │
    │  → No registra movimiento                             │
    └───────────────────────────────────────────────────────┘
         │
         ▼
[7] Persistencia de respuesta
    → Guarda mensaje del asistente en messages
    → Registra en ai_logs (tokens, costo, latencia)
         │
         ▼
[8] WhatsApp Service
    → Llama a POST /messages de WhatsApp Cloud API
    → Si falla: reintenta 2 veces con backoff exponencial
    → Si falla definitivamente: loguea el error (mensaje perdido)
```

---

## 8. Manejo de Archivos Adjuntos y Comprobantes

### Flujo Detallado

```
[A] Usuario envía imagen/PDF en WhatsApp
         │
         ▼
[B] Webhook recibe mensaje de tipo "image" o "document"
    raw_payload contiene: { "id": "whatsapp_media_id", "mime_type": "...", "sha256": "..." }
         │
         ▼
[C] AttachmentService.process_incoming_media()
    1. Descarga el archivo usando el whatsapp_media_id
       GET https://graph.facebook.com/v18.0/{media_id}
       (Obtiene URL temporal firmada)
    2. Valida mime_type (jpg, jpeg, png, webp, pdf)
    3. Valida tamaño (máx. 10MB)
    4. Genera path único: {user_id}/{YYYY}/{MM}/{uuid}.{ext}
    5. Sube a Supabase Storage
    6. Crea registro en attachments con status='uploaded'
         │
         ▼
[D] Asociación a transacción
    → Busca la última transacción del usuario sin comprobante (< 24 horas)
    → Si existe: asocia y confirma
    → Si no existe: guarda attachment "huérfano" (transaction_id = NULL)
                    → Responde "Guardé el comprobante, ¿a qué movimiento lo asocio?"
```

### Reglas de Validación
- Tipos permitidos: `image/jpeg`, `image/png`, `image/webp`, `application/pdf`
- Tamaño máximo: **10 MB**
- Almacenamiento: Supabase Storage (bucket `receipts`, privado)
- URLs firmadas con expiración de 1 hora para visualización en dashboard

---

## 9. Modelo de Autenticación para el Dashboard

### Estrategia: JWT con Access + Refresh Tokens

```
POST /api/auth/login
  body: { email, password }
  response: {
    access_token: JWT (exp: 15 minutos),
    refresh_token: JWT (exp: 7 días, almacenado en HttpOnly cookie)
  }

POST /api/auth/refresh
  cookie: refresh_token
  response: { access_token: nuevo JWT }

POST /api/auth/logout
  → Invalida refresh_token (flag en DB)
```

### Por qué este modelo
- Access token corto (15 min): reduce ventana de exposición si es interceptado
- Refresh token en HttpOnly cookie: inaccesible desde JavaScript, protege contra XSS
- Un campo `token_revoked` en la tabla `users` permite logout forzado

### Registro Inicial
Para el MVP: **registro manual**. Un usuario crea su cuenta con email+password y luego vincula su número de teléfono en "Configuración". El webhook identifica al usuario por teléfono.

### Consideración Futura (Fase 4 / SaaS)
- OAuth2 (Google)
- Magic links por email
- Invitaciones de equipo

---

## 10. Problemas de Escalabilidad Identificados

| # | Problema | Impacto | Solución MVP | Solución Escala |
|---|----------|---------|--------------|-----------------|
| S1 | Procesamiento síncrono de IA en webhook | Timeouts con > 50 usuarios simultáneos | `threading.Thread` | Celery + Redis |
| S2 | Ventana de contexto crece sin límite | Costo de tokens aumenta linealmente | Limitar a últimos 10 mensajes | Embeddings + RAG |
| S3 | Consultas SQL sin índices de rango temporal | Lento con > 100k transacciones | Índices por `(user_id, transaction_date)` | Partición por fecha |
| S4 | Descarga de media de WhatsApp en el hilo principal | Timeout en archivos grandes | Thread separado | Worker pool async |
| S5 | Categorías globales sin tenant isolation | Imposible personalizar por empresa en Fase 4 | `user_id NULL = global` ya contemplado | Row-Level Security en PostgreSQL |
| S6 | Sin caché para resúmenes financieros | Cada consulta hace query completa | Aceptable en MVP | Redis con TTL de 5 minutos |
| S7 | Logs de IA sin retención policy | La tabla `ai_logs` crece sin control | Aceptable en MVP | Archiving mensual a S3 |

---

## 11. Plan Técnico para el MVP (Fase 1)

### Objetivos del MVP
- Registrar gastos e ingresos por WhatsApp
- Adjuntar comprobantes
- Responder consultas básicas
- Dashboard con visualización

### Orden de Implementación

#### Sprint 1 — Fundación (2-3 días)
- [ ] Estructura de carpetas
- [ ] `config.py` con variables de entorno
- [ ] Modelos SQLAlchemy completos
- [ ] Migraciones Alembic iniciales
- [ ] `requirements.txt`
- [ ] `.env.example`

#### Sprint 2 — Canal WhatsApp (2 días)
- [ ] Endpoint `GET /webhook` (verificación)
- [ ] Endpoint `POST /webhook` (recepción)
- [ ] Deduplicación por `whatsapp_message_id`
- [ ] `UserRepository` — find_or_create por phone
- [ ] `ConversationService` — gestión de sesiones
- [ ] `WhatsAppService` — envío de mensajes

#### Sprint 3 — Motor IA (2-3 días)
- [ ] `OpenAIService` con manejo de errores y logs
- [ ] Prompts: `intent_classifier.txt`, `entity_extractor.txt`
- [ ] `WebhookProcessor` — orquestación del flujo completo
- [ ] Intenciones: REGISTER_EXPENSE, REGISTER_INCOME, QUERY, UNKNOWN
- [ ] `TransactionService` — create, update, soft_delete

#### Sprint 4 — Comprobantes (1-2 días)
- [ ] `AttachmentService` — descarga WhatsApp → Supabase Storage
- [ ] Lógica de asociación de comprobante a última transacción
- [ ] Validación de tipos y tamaños de archivo

#### Sprint 5 — Consultas Financieras (1-2 días)
- [ ] `FinancialSummaryService` — SQL directo para sumas/balances
- [ ] Prompt `query_assistant.txt` — IA formatea la respuesta con datos reales
- [ ] Contexto conversacional (ventana de 10 mensajes)

#### Sprint 6 — Autenticación Dashboard (1 día)
- [ ] `AuthService` — login, JWT access + refresh
- [ ] Endpoint `/api/auth/login`, `/api/auth/refresh`, `/api/auth/logout`
- [ ] Decorador `@jwt_required`

#### Sprint 7 — Dashboard Frontend (3-4 días)
- [ ] Setup Vite + React + TailwindCSS + Recharts
- [ ] Login page
- [ ] Layout con sidebar
- [ ] Home (balance, métricas, últimos movimientos)
- [ ] Página de Movimientos (tabla paginada + filtros)
- [ ] Página de Comprobantes (galería + vista previa)
- [ ] Página de Estadísticas (gráficos)

#### Sprint 8 — Testing y Deploy (1-2 días)
- [ ] Tests unitarios: `TransactionService`, `ConversationService`, `FinancialSummaryService`
- [ ] Tests de integración: flujo webhook end-to-end
- [ ] Configuración Railway (`Procfile`, variables de entorno)
- [ ] Deploy y smoke testing

---

## 12. Open Questions para el Usuario

> [!IMPORTANT]
> Estas decisiones impactan directamente la arquitectura. Requieren respuesta antes de escribir código.

**Q1 — Moneda y localización**
Los ejemplos usan pesos argentinos (ARS). ¿El sistema debe soportar múltiples monedas desde el inicio, o ARS es la única moneda del MVP?

**Q2 — Procesamiento asíncrono**
Para el MVP propongo `threading.Thread` para no bloquear el webhook. ¿Prefiere implementar Celery + Redis desde el inicio (más robusto pero más complejo), o empezar con threads y migrar si es necesario?

**Q3 — Número de teléfono del negocio**
¿Ya tienes un número de WhatsApp Business registrado en Meta para hacer el webhook? Esto puede demorar días en aprobarse.

**Q4 — Modelo de OpenAI**
¿Se usa `gpt-4o-mini` para clasificación (económico, ~$0.0002/1k tokens) y `gpt-4o` solo para consultas complejas? ¿O se prefiere un solo modelo?

**Q5 — Dashboard: ¿solo lectura o también puede registrar?**
CLAUDE.md dice "el dashboard es secundario" y PROJECT_CONTEXT dice "visualizar, no registrar". ¿Confirma que el dashboard NO tendrá formularios para crear transacciones? ¿O eventualmente sí?

**Q6 — Autenticación del dashboard**
¿El único acceso al dashboard es el dueño del sistema (uso personal), o desde el MVP debe soportar múltiples usuarios con sus propios datos?

> [!WARNING]
> **Q7 — Nombre del bucket de Supabase Storage**
> Las URLs de archivos adjuntos serán públicas (con firma temporal) o privadas. Confirme si el bucket debe ser privado (recomendado) para evitar exposición de datos financieros.

---

## 13. Variables de Entorno Completas (.env.example)

```env
# Flask
FLASK_ENV=development
SECRET_KEY=change-me-in-production
DEBUG=True

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/finanzas_ia

# WhatsApp Cloud API
WHATSAPP_TOKEN=your_permanent_token
WHATSAPP_VERIFY_TOKEN=your_custom_verify_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_API_VERSION=v18.0

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL_FAST=gpt-4o-mini
OPENAI_MODEL_SMART=gpt-4o
OPENAI_MAX_CONTEXT_MESSAGES=10

# Supabase Storage
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_BUCKET_RECEIPTS=receipts

# JWT
JWT_SECRET_KEY=change-me-in-production
JWT_ACCESS_TOKEN_EXPIRES=900      # 15 minutos en segundos
JWT_REFRESH_TOKEN_EXPIRES=604800  # 7 días en segundos

# Rate Limiting
RATE_LIMIT_PER_MINUTE=30
```
