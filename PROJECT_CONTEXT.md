# PROJECT_CONTEXT.md

# Contexto General

Este proyecto será desarrollado utilizando Claude Code y Antigravity.

El objetivo es construir una plataforma SaaS centrada en WhatsApp que permita a los usuarios gestionar sus finanzas personales mediante lenguaje natural.

La interfaz principal del producto NO es el dashboard web.

La interfaz principal es WhatsApp.

Todo el diseño arquitectónico debe asumir que el usuario utilizará WhatsApp el 90% del tiempo.

El dashboard es únicamente una herramienta de visualización y administración.

---

# Filosofía del Proyecto

La mayoría de aplicaciones financieras obligan al usuario a:

* abrir una app
* completar formularios
* seleccionar categorías
* cargar información manualmente

Este proyecto elimina esa fricción.

El usuario simplemente conversa.

Ejemplos:

Gasté 15000 en supermercado

Cobré 950000

Te envío el comprobante

¿Cuánto gasté este mes?

Buscame la factura de internet

La IA debe encargarse del resto.

---

# Arquitectura General

Frontend React

↓

Backend Flask

↓

Servicios de Negocio

↓

PostgreSQL

↓

Storage

↓

OpenAI

↓

WhatsApp Cloud API

---

# Estructura de Carpetas Esperada

backend/

app/

api/

services/

models/

repositories/

prompts/

utils/

storage/

whatsapp/

ai/

migrations/

tests/

frontend/

src/

components/

pages/

layouts/

hooks/

services/

types/

charts/

---

# Backend

Utilizar Flask.

Separar responsabilidades.

Evitar lógica de negocio en endpoints.

Los endpoints únicamente deben:

* validar
* delegar
* responder

Toda lógica compleja debe vivir en services.

---

# Patrón de Arquitectura

API Layer

↓

Service Layer

↓

Repository Layer

↓

Database

Nunca acceder directamente a SQLAlchemy desde controladores.

---

# Repositories

Cada entidad debe tener un repository.

Ejemplos:

UserRepository

TransactionRepository

CategoryRepository

AttachmentRepository

ConversationRepository

MessageRepository

---

# Services

La lógica de negocio debe concentrarse aquí.

Ejemplos:

TransactionService

FinancialSummaryService

ConversationService

AttachmentService

WhatsAppService

OpenAIService

---

# WhatsApp

Utilizar WhatsApp Cloud API.

Implementar:

GET /webhook

POST /webhook

El webhook debe ser extremadamente simple.

Debe:

1. recibir mensaje
2. guardar mensaje
3. procesar mensaje
4. responder usuario

---

# Flujo de Mensaje

Usuario

↓

Webhook

↓

ConversationService

↓

Intent Detection

↓

Business Logic

↓

Response Generation

↓

WhatsApp Reply

---

# Detección de Intención

La IA debe clasificar mensajes en:

REGISTER_EXPENSE

REGISTER_INCOME

ATTACH_RECEIPT

QUERY

UPDATE_TRANSACTION

HELP

UNKNOWN

---

# Estrategia IA

No utilizar IA para todo.

Utilizar IA únicamente cuando agregue valor.

Ejemplo:

Clasificar intención

Extraer entidades

Responder consultas complejas

No utilizar IA para:

CRUD básico

sumatorias simples

consultas SQL directas

cálculos básicos

---

# Extracción de Entidades

Siempre intentar obtener:

Monto

Categoría

Descripción

Fecha

Ejemplo:

Gasté 25000 en combustible

Resultado:

amount: 25000

category: combustible

description: combustible

date: hoy

---

# Prompt Engineering

Mantener prompts separados.

Crear carpeta:

backend/app/prompts

Ejemplos:

expense_parser.txt

income_parser.txt

query_assistant.txt

categorizer.txt

---

# OpenAI

Crear servicio único.

OpenAIService

Responsabilidades:

* llamadas a OpenAI
* manejo de errores
* logs
* control de costos

Nunca llamar OpenAI directamente desde endpoints.

---

# Costos

Optimizar consumo.

Preferir:

clasificar

extraer

estructurar

antes que conversaciones largas.

Guardar resultados estructurados.

No depender de IA para reconstruir información ya conocida.

---

# Base de Datos

PostgreSQL.

Todas las tablas deben tener:

id

created_at

updated_at

deleted_at

Utilizar soft delete.

---

# Storage

Guardar comprobantes fuera de PostgreSQL.

Utilizar storage compatible S3.

Guardar solamente:

url

metadata

referencias

en base de datos.

---

# Comprobantes

Tipos soportados:

jpg

jpeg

png

webp

pdf

Cada comprobante debe poder asociarse a una transacción.

Una transacción puede tener múltiples comprobantes.

---

# Dashboard

Objetivo:

visualizar

no registrar

Las operaciones principales se realizan desde WhatsApp.

---

# Dashboard Inicial

Home

Movimientos

Categorías

Comprobantes

Estadísticas

Configuración

---

# Home

Mostrar:

Balance actual

Ingresos mes

Gastos mes

Cantidad de movimientos

Últimos movimientos

---

# Estadísticas

Gastos por categoría

Ingresos por mes

Comparación mensual

Top gastos

Tendencias

---

# Consultas Inteligentes

El sistema debe responder preguntas como:

¿Cuánto gasté este mes?

¿Cuánto gasté en combustible?

¿Cuál fue mi gasto más grande?

¿Cuánto ingresé?

¿Qué categorías crecieron?

¿Cuánto gasté en supermercados?

¿Estoy gastando más que el mes pasado?

---

# Contexto Conversacional

Guardar TODOS los mensajes.

Nunca descartar historial.

Tablas:

conversations

messages

Esto permitirá futuras funciones avanzadas.

---

# Futuro

El diseño debe permitir agregar:

OCR

audio

transcripción

presupuestos

metas

familias

empresas

múltiples cuentas

tarjetas

inversiones

---

# Railway

El proyecto debe ser desplegable en Railway.

Configurar:

DATABASE_URL

OPENAI_API_KEY

WHATSAPP_TOKEN

WHATSAPP_VERIFY_TOKEN

WHATSAPP_PHONE_ID

STORAGE_ENDPOINT

STORAGE_ACCESS_KEY

STORAGE_SECRET_KEY

---

# GitHub

Seguir buenas prácticas.

Commits pequeños.

Variables sensibles fuera del repositorio.

Utilizar .env.

Agregar .env.example.

---

# Testing

Tests mínimos para:

TransactionService

ConversationService

FinancialSummaryService

OpenAIService

Webhook Processing

---

# Regla Principal

Antes de agregar complejidad:

preguntarse si la funcionalidad mejora la experiencia conversacional del usuario.

Si no mejora la experiencia de conversar con sus finanzas, probablemente no sea prioritaria.

La experiencia WhatsApp es el producto.
