import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await login(username, password);
    } catch (err) {
      console.error('Erro capturado em Login:', err);
      const errorMessage = err.message || 'Erro ao fazer login. Tente novamente.';
      setError(errorMessage);
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', padding: '1rem', background: 'radial-gradient(circle at top right, #1e293b, #0f172a)' }}>
      <div className="glass-card fade-in" style={{ width: '100%', maxWidth: '400px' }}>
        <h2 style={{ marginBottom: '0.25rem', textAlign: 'center' }}>Avalia.AI</h2>
        <p style={{ color: 'var(--primary)', textAlign: 'center', fontSize: '0.7rem', fontWeight: '700', letterSpacing: '0.1em', marginBottom: '0.5rem' }}>v2.0</p>
        <p style={{ color: 'var(--text-muted)', textAlign: 'center', marginBottom: '2rem' }}>Acesse sua conta para continuar</p>
        
        {error && <p style={{ color: 'var(--danger)', textAlign: 'center', marginBottom: '1rem' }}>{error}</p>}
        
        <form onSubmit={handleSubmit}>
          <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Usuário</label>
          <input 
            type="text" 
            placeholder="Seu usuário..." 
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          
          <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Senha</label>
          <input 
            type="password" 
            placeholder="********" 
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          
          <button type="submit" className="btn-primary" style={{ width: '100%', justifyContent: 'center', marginTop: '1rem' }}>
            Entrar no Portal
          </button>
        </form>

        <div style={{ marginTop: '2rem', textAlign: 'center' }}>
          <p style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Não tem uma conta?</p>
          <button 
            onClick={() => window.dispatchEvent(new CustomEvent('switch-to-register'))}
            style={{ width: '100%', background: 'transparent', border: 'none', color: 'white', cursor: 'pointer', padding: '0.5rem' }}
          >
            Cadastrar-se Agora
          </button>
        </div>
      </div>
    </div>
  );
};

export default Login;
