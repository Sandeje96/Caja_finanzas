import { useEffect, useState } from 'react'

interface HealthCheck {
  status: 'ok' | 'degraded' | 'loading' | 'error'
  service?: string
  version?: string
  timestamp?: string
  checks?: { database: string }
}

export default function App() {
  const [health, setHealth] = useState<HealthCheck>({ status: 'loading' })

  useEffect(() => {
    fetch('/api/health')
      .then(r => r.json())
      .then(data => setHealth(data))
      .catch(() => setHealth({ status: 'error' }))
  }, [])

  const statusColor = {
    ok:       'text-green-400',
    degraded: 'text-yellow-400',
    loading:  'text-gray-400',
    error:    'text-red-400',
  }[health.status]

  const dbColor = health.checks?.database === 'ok' ? 'text-green-400' : 'text-red-400'

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-8">
      <div className="max-w-lg w-full">
        {/* Logo / Title */}
        <div className="text-center mb-12">
          <div className="text-5xl mb-4">💬</div>
          <h1 className="text-3xl font-bold text-white mb-2">
            Finanzas IA WhatsApp
          </h1>
          <p className="text-gray-400">
            Asistente financiero personal conversacional
          </p>
        </div>

        {/* Status Card */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 mb-6">
          <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-4">
            Estado del Sistema
          </h2>

          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-300">API Backend</span>
              <span className={`font-mono font-medium ${statusColor}`}>
                {health.status === 'loading' ? '...' : health.status}
              </span>
            </div>

            {health.checks && (
              <div className="flex justify-between items-center">
                <span className="text-gray-300">PostgreSQL</span>
                <span className={`font-mono font-medium ${dbColor}`}>
                  {health.checks.database}
                </span>
              </div>
            )}

            {health.version && (
              <div className="flex justify-between items-center">
                <span className="text-gray-300">Versión</span>
                <span className="font-mono text-gray-400">{health.version}</span>
              </div>
            )}
          </div>
        </div>

        {/* Endpoint info */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
          <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-4">
            Endpoints Disponibles
          </h2>
          <div className="space-y-2 font-mono text-sm">
            <div className="flex gap-3">
              <span className="text-green-400">GET</span>
              <span className="text-gray-300">/api/health</span>
              <span className="text-gray-600 ml-auto">✅ activo</span>
            </div>
            <div className="flex gap-3">
              <span className="text-green-400">GET</span>
              <span className="text-gray-300">/api/webhook</span>
              <span className="text-gray-600 ml-auto">✅ activo</span>
            </div>
            <div className="flex gap-3">
              <span className="text-blue-400">POST</span>
              <span className="text-gray-300">/api/webhook</span>
              <span className="text-gray-600 ml-auto">🔧 Sprint 2</span>
            </div>
            <div className="flex gap-3">
              <span className="text-blue-400">POST</span>
              <span className="text-gray-300">/api/auth/login</span>
              <span className="text-gray-600 ml-auto">🔧 Sprint 6</span>
            </div>
          </div>
        </div>

        <p className="text-center text-gray-600 text-xs mt-6">
          Sprint 1 completado — estructura base del proyecto
        </p>
      </div>
    </div>
  )
}
