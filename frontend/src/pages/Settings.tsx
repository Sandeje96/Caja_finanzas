import { useQuery } from '@tanstack/react-query';
import { getMe } from '../api/auth';

export default function Settings() {
  const { data: user, isLoading } = useQuery({
    queryKey: ['me'],
    queryFn: getMe,
  });

  if (isLoading) {
    return <div className="text-gray-500">Cargando configuración...</div>;
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-bold text-white">Configuración</h1>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-6">
        <h2 className="text-lg font-medium text-white border-b border-gray-800 pb-2">Perfil de Usuario</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Nombre</label>
            <input
              type="text"
              value={user?.name || ''}
              readOnly
              className="w-full bg-gray-950 border border-gray-800 rounded-lg px-4 py-2.5 text-gray-300 focus:outline-none cursor-not-allowed opacity-70"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">WhatsApp</label>
            <input
              type="text"
              value={user?.phone || ''}
              readOnly
              className="w-full bg-gray-950 border border-gray-800 rounded-lg px-4 py-2.5 text-gray-300 focus:outline-none cursor-not-allowed opacity-70"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Zona Horaria</label>
            <input
              type="text"
              value={user?.timezone || ''}
              readOnly
              className="w-full bg-gray-950 border border-gray-800 rounded-lg px-4 py-2.5 text-gray-300 focus:outline-none cursor-not-allowed opacity-70"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Moneda</label>
            <input
              type="text"
              value={user?.currency || ''}
              readOnly
              className="w-full bg-gray-950 border border-gray-800 rounded-lg px-4 py-2.5 text-gray-300 focus:outline-none cursor-not-allowed opacity-70"
            />
          </div>
        </div>
      </div>
      
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h2 className="text-lg font-medium text-white border-b border-gray-800 pb-2 mb-4">Integraciones</h2>
        <p className="text-sm text-gray-400 mb-4">
          La configuración de OpenAI y la base de datos se maneja a nivel de variables de entorno del servidor.
        </p>
      </div>
    </div>
  );
}
