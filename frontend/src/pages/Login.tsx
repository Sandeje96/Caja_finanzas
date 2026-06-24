import { useState } from 'react';
import { requestOtp, verifyOtp } from '../api/auth';
import { useNavigate } from 'react-router-dom';

export default function Login() {
  const [phone, setPhone] = useState('');
  const [otpMode, setOtpMode] = useState(false);
  const [otpCode, setOtpCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleRequestOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await requestOtp(phone);
      setOtpMode(true);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error al solicitar OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const data = await verifyOtp(phone, otpCode);
      localStorage.setItem('access_token', data.access_token);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.error || 'Código inválido');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-gray-900 border border-gray-800 rounded-2xl p-8 shadow-xl">
        <div className="text-center mb-8">
          <div className="text-4xl mb-4">💬</div>
          <h1 className="text-2xl font-bold text-white mb-2">Caja Finanzas</h1>
          <p className="text-gray-400 text-sm">Administra tus gastos inteligentemente</p>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded bg-red-500/10 border border-red-500/50 text-red-400 text-sm">
            {error}
          </div>
        )}

        {!otpMode ? (
          <form onSubmit={handleRequestOtp} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Número de WhatsApp</label>
              <input
                type="text"
                placeholder="+5491123456789"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="w-full bg-gray-950 border border-gray-800 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-colors"
                required
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-white text-gray-900 font-medium rounded-lg px-4 py-2.5 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-white/50 transition-all disabled:opacity-50"
            >
              {loading ? 'Enviando...' : 'Recibir código por WhatsApp'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleVerifyOtp} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Código de verificación</label>
              <input
                type="text"
                placeholder="000000"
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value)}
                maxLength={6}
                className="w-full bg-gray-950 border border-gray-800 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-colors text-center tracking-widest text-lg"
                required
              />
              <p className="text-xs text-gray-500 mt-2 text-center">Te enviamos un código por WhatsApp al {phone}</p>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-white text-gray-900 font-medium rounded-lg px-4 py-2.5 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-white/50 transition-all disabled:opacity-50"
            >
              {loading ? 'Verificando...' : 'Ingresar'}
            </button>
            <button
              type="button"
              onClick={() => setOtpMode(false)}
              className="w-full text-gray-400 text-sm hover:text-white transition-colors mt-2"
            >
              Cambiar número
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
