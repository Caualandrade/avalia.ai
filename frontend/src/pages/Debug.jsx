// frontend/src/pages/Debug.jsx
// 🧪 PÁGINA DE DEBUG - Use isto para testar conexão com backend

import React, { useState } from 'react';
import { testBackendConnection, debugLogin } from '../debug-api';

const Debug = () => {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');

  const handleTestConnection = async () => {
    console.clear();
    await testBackendConnection();
  };

  const handleTestLogin = async () => {
    console.clear();
    if (!username || !password) {
      alert('Preencha username e password');
      return;
    }
    await debugLogin(username, password);
  };

  return (
    <div style={{ padding: '2rem', maxWidth: '600px', margin: '0 auto' }}>
      <h1>🧪 DEBUG - Testes de API</h1>
      <p style={{ color: '#888' }}>Abra o Console (F12) para ver os logs</p>

      <div style={{ background: '#f0f0f0', padding: '1rem', borderRadius: '8px', marginBottom: '2rem' }}>
        <h2>1️⃣ Testar Conexão</h2>
        <p>Verifica se o backend está respondendo</p>
        <button 
          onClick={handleTestConnection}
          style={{
            padding: '0.75rem 1.5rem',
            fontSize: '1rem',
            background: '#2563eb',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Testar Conexão
        </button>
      </div>

      <div style={{ background: '#f0f0f0', padding: '1rem', borderRadius: '8px' }}>
        <h2>2️⃣ Testar Login</h2>
        <p>Tenta fazer login e verificar token</p>
        
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem' }}>Username:</label>
          <input 
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="admin"
            style={{
              width: '100%',
              padding: '0.5rem',
              fontSize: '1rem',
              boxSizing: 'border-box'
            }}
          />
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem' }}>Password:</label>
          <input 
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="sua_senha"
            style={{
              width: '100%',
              padding: '0.5rem',
              fontSize: '1rem',
              boxSizing: 'border-box'
            }}
          />
        </div>

        <button 
          onClick={handleTestLogin}
          style={{
            padding: '0.75rem 1.5rem',
            fontSize: '1rem',
            background: '#16a34a',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Testar Login
        </button>
      </div>

      <div style={{ marginTop: '2rem', background: '#fff3cd', padding: '1rem', borderRadius: '4px' }}>
        <h3>💡 Dicas:</h3>
        <ul>
          <li>Abra o <strong>Console do navegador (F12 → Console)</strong></li>
          <li>Clique em "Testar Conexão" primeiro</li>
          <li>Se a conexão OK, tente fazer login</li>
          <li>Veja os logs detalhados no console</li>
          <li>Se vir CORS error, o problema está no CORS do backend</li>
        </ul>
      </div>
    </div>
  );
};

export default Debug;
