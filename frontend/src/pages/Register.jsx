import React, { useState } from 'react';
import axios from 'axios';
import { API_URL } from '../config';

const Register = ({ onBackToLogin }) => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    role: 'COMPANY',
    company_name: ''
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await axios.post(`${API_URL}/register`, formData);
      setSuccess(true);
      setTimeout(() => onBackToLogin(), 2000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao realizar cadastro.');
    }
  };

  if (success) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: 'radial-gradient(circle at top right, #1e293b, #0f172a)' }}>
        <div className="glass-card fade-in" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '3rem', color: 'var(--success)', marginBottom: '1rem' }}>✓</div>
          <h2>Cadastro Realizado!</h2>
          <p>Redirecionando para o login...</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: 'radial-gradient(circle at top right, #1e293b, #0f172a)' }}>
      <div className="glass-card fade-in" style={{ width: '450px' }}>
        <h2 style={{ textAlign: 'center', marginBottom: '0.5rem' }}>Criar Nova Conta</h2>
        <p style={{ color: 'var(--text-muted)', textAlign: 'center', marginBottom: '2rem' }}>Junte-se à plataforma de Maturidade TI</p>

        {error && <p style={{ color: 'var(--danger)', textAlign: 'center', marginBottom: '1rem' }}>{error}</p>}

        <form onSubmit={handleSubmit}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Usuário</label>
              <input 
                type="text" 
                placeholder="Ex: joao_ti"
                value={formData.username}
                onChange={(e) => setFormData({...formData, username: e.target.value})}
                required
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.5rem' }}>E-mail</label>
              <input 
                type="email" 
                placeholder="seu@email.com"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                required
              />
            </div>
          </div>

          <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.5rem', marginTop: '1rem' }}>Senha</label>
          <input 
            type="password" 
            placeholder="********"
            value={formData.password}
            onChange={(e) => setFormData({...formData, password: e.target.value})}
            required
          />

          <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.5rem', marginTop: '1rem' }}>Perfil</label>
          <select 
            value={formData.role}
            onChange={(e) => setFormData({...formData, role: e.target.value})}
            style={{ width: '100%', padding: '0.8rem', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)', color: 'white' }}
          >
            <option value="COMPANY" style={{ background: '#1e293b', color: 'white' }}>Empresa (Quero ser avaliado)</option>
            <option value="EVALUATOR" style={{ background: '#1e293b', color: 'white' }}>Avaliador (Quero aplicar avaliações)</option>
          </select>

          {formData.role === 'COMPANY' && (
            <div style={{ marginTop: '1rem' }}>
              <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Nome da Empresa</label>
              <input 
                type="text" 
                placeholder="Nome fantasia da empresa"
                value={formData.company_name}
                onChange={(e) => setFormData({...formData, company_name: e.target.value})}
                required
              />
            </div>
          )}

          <button type="submit" className="btn-primary" style={{ width: '100%', marginTop: '2rem', justifyContent: 'center' }}>
            Finalizar Cadastro
          </button>
        </form>

        <button 
          onClick={onBackToLogin}
          style={{ width: '100%', marginTop: '1rem', background: 'transparent', border: 'none', color: 'white', cursor: 'pointer', padding: '0.5rem' }}
        >
          Já tenho conta? Ir para Login
        </button>
      </div>
    </div>
  );
};

export default Register;
