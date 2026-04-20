import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import InterviewChat from './InterviewChat';
import FeedbackReport from './FeedbackReport';
import ManualForm from './ManualForm';

import { API_URL } from '../config';

// ─── Icons ────────────────────────────────────────────────────────────────────
const Icon = ({ name, size = 18, color = 'currentColor' }) => {
  const icons = {
    home:      <><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></>,
    folder:    <path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13c0 1.1.9 2 2 2z"/>,
    help:      <><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></>,
    plus:      <><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></>,
    trash:     <><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></>,
    edit:      <><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></>,
    logout:    <><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></>,
    stats:     <><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></>,
    users:     <><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></>,
    sparkles:  <><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/><path d="M5 3v4"/><path d="M19 17v4"/><path d="M3 5h4"/><path d="M17 19h4"/></>,
    mail:      <><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22 6 12 13 2 6"/></>,
    chat:      <><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 0 2 2z"/></>,
    report:    <><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></>,
    check:     <><polyline points="20 6 9 17 4 12"/></>,
    clock:     <><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></>,
    robot:     <><rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4"/><line x1="8" y1="16" x2="8" y2="16"/><line x1="16" y1="16" x2="16" y2="16"/></>,
    settings:  <><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></>,
    menu:      <><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></>,
    close:     <><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="18" x2="18" y2="6"/></>,
  };
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24"
      fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      {icons[name]}
    </svg>
  );
};

// ─── Pagination Component ─────────────────────────────────────────────────────
const Pagination = ({ page, totalPages, onPageChange }) => {
  if (totalPages <= 1) return null;
  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '1rem', marginTop: '1.5rem' }}>
      <button className="btn-secondary" disabled={page === 1} onClick={() => onPageChange(page - 1)} style={{ padding: '0.4rem 1rem', fontSize: '0.8rem' }}>Anterior</button>
      <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Página {page} de {totalPages}</span>
      <button className="btn-secondary" disabled={page === totalPages} onClick={() => onPageChange(page + 1)} style={{ padding: '0.4rem 1rem', fontSize: '0.8rem' }}>Próxima</button>
    </div>
  );
};

// ─── Admin: Lista de Usuários ──────────────────────────────────────────────────
const AdminUsersView = () => {
  const [users, setUsers] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUsers = async () => {
      setLoading(true);
      try {
        const token = localStorage.getItem('token');
        const res = await axios.get(`${API_URL}/admin/users?page=${page}&limit=10`, { headers: { Authorization: `Bearer ${token}` } });
        setUsers(res.data.items);
        setTotalPages(res.data.pages);
      } catch (err) { console.error(err); }
      finally { setLoading(false); }
    };
    fetchUsers();
  }, [page]);

  const roleColors = { ADMIN: 'var(--danger)', EVALUATOR: 'var(--primary)', COMPANY: 'var(--text-main)' };

  if (loading && page === 1) return <div className="glass-card">Carregando usuários...</div>;

  return (
    <div className="fade-in">
      <h4 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
        <Icon name="users" color="var(--primary)" /> Gerenciamento de Usuários
      </h4>
      <div style={{ display: 'grid', gap: '0.8rem' }}>
        {users.map(u => (
          <div key={u.id} className="glass-card" style={{ padding: '1.2rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <p style={{ fontWeight: '700', fontSize: '1rem' }}>{u.username}</p>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>{u.email}</p>
            </div>
            <div style={{ textAlign: 'right' }}>
              <span style={{ padding: '0.3rem 0.8rem', borderRadius: '15px', fontSize: '0.7rem', fontWeight: '800', border: `1px solid ${roleColors[u.role] || '#fff'}`, color: roleColors[u.role] || '#fff' }}>
                {u.role}
              </span>
              {u.company_name && <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.3rem' }}>{u.company_name}</p>}
            </div>
          </div>
        ))}
      </div>
      <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
    </div>
  );
};

// ─── Admin View ───────────────────────────────────────────────────────────────
const AdminView = () => {
  const [stats, setStats] = useState({ total_users: 0, companies: 0, evaluators: 0, assessments: 0, completed_assessments: 0, avg_score: 0 });
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await axios.get(`${API_URL}/admin/stats`, { headers: { Authorization: `Bearer ${token}` } });
        setStats(res.data);
      } catch (err) { console.error(err); }
    };
    fetchStats();
  }, []);
  return (
    <div className="fade-in">
      <h3>Visão Geral do Sistema (Admin)</h3>
      <div className="stack-mobile" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem', marginTop: '1.5rem' }}>
        {[
          { label: 'Usuários Cadastrados', val: stats.total_users, color: 'var(--primary)' },
          { label: 'Empresas Ativas', val: stats.companies, color: 'var(--text-main)' },
          { label: 'Avaliadores', val: stats.evaluators, color: 'var(--text-main)' },
          { label: 'Avaliações Processadas', val: stats.assessments, color: 'var(--warning)' },
          { label: 'Avaliações Concluídas', val: stats.completed_assessments, color: 'var(--success)' },
          { label: 'Score Médio Geral', val: stats.avg_score, color: 'var(--primary)' },
        ].map(({ label, val, color }) => (
          <div key={label} className="glass-card">
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{label}</p>
            <h2 style={{ color }}>{val}</h2>
          </div>
        ))}
      </div>
    </div>
  );
};

// ─── Application Settings ─────────────────────────────────────────────────────
const AppConfigSettings = () => {
  const [settings, setSettings] = useState({ openai_api_key: '', autonomous_questions: 5 });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);

  const handleTestConnection = async () => {
    if (!settings.openai_api_key) return alert('Por favor, insira uma chave antes.');
    setTestingConnection(true);
    try {
      const token = localStorage.getItem('token');
      const res = await axios.post(`${API_URL}/settings/test-api-key`, { api_key: settings.openai_api_key }, { headers: { Authorization: `Bearer ${token}` } });
      alert(res.data.message);
    } catch (err) {
      alert(err.response?.data?.detail || 'Falha ao conectar com a API');
    } finally {
      setTestingConnection(false);
    }
  };

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await axios.get(`${API_URL}/settings`, { headers: { Authorization: `Bearer ${token}` } });
        setSettings({
          openai_api_key: res.data.openai_api_key || '',
          autonomous_questions: res.data.autonomous_questions || 5
        });
      } catch (err) { console.error('Erro ao buscar configurações', err); }
      finally { setLoading(false); }
    };
    fetchSettings();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API_URL}/settings`, settings, { headers: { Authorization: `Bearer ${token}` } });
      alert('Configurações salvas com sucesso!');
    } catch (err) {
      alert('Erro ao salvar as configurações.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="glass-card">Carregando configurações...</div>;

  return (
    <div className="fade-in">
      <div className="glass-card" style={{ maxWidth: '600px' }}>
        <h4 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
          <Icon name="settings" color="var(--primary)" /> Configurações do AI Agent
        </h4>
        
        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: '700' }}>CHAVE DA API OPENAI</label>
          <input 
            type="password"
            value={settings.openai_api_key} 
            onChange={e => setSettings({ ...settings, openai_api_key: e.target.value })} 
            placeholder="sk-..." 
            style={{ marginTop: '0.5rem', width: '100%' }} 
          />
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
            A chave da API será enviada para o servidor e utilizada pelo LangChain no backend.
          </p>
        </div>

        <div style={{ marginBottom: '2rem' }}>
          <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: '700' }}>QUANTIDADE DE PERGUNTAS (MODO AUTÔNOMO)</label>
          <input 
            type="number" 
            min="1" 
            max="20"
            value={settings.autonomous_questions} 
            onChange={e => setSettings({ ...settings, autonomous_questions: parseInt(e.target.value) || 5 })} 
            style={{ marginTop: '0.5rem', width: '100%' }} 
          />
        </div>

        <div style={{ display: 'flex', gap: '1rem' }}>
          <button className="btn-secondary" onClick={handleTestConnection} disabled={testingConnection || saving}>
            {testingConnection ? <div className="loader" /> : 'Testar Conexão'}
          </button>
          <button className="btn-primary" onClick={handleSave} disabled={saving || testingConnection}>
            {saving ? <div className="loader" /> : <><Icon name="check" size={16} color="#00363d" /> Salvar Configurações</>}
          </button>
        </div>
      </div>
    </div>
  );
};


// ─── Evaluator: Domains / Categories ──────────────────────────────────────────
const EvaluatorDomains = () => {
  const [categories, setCategories] = useState([]);
  const [newCat, setNewCat] = useState('');
  const [newSub, setNewSub] = useState({ name: '', category_id: '' });

  const fetchCats = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API_URL}/categories`, { headers: { Authorization: `Bearer ${token}` } });
      setCategories(res.data);
    } catch (err) { console.error(err); }
  };
  useEffect(() => { fetchCats(); }, []);

  const handleCreateCategory = async () => {
    if (!newCat) return;
    const token = localStorage.getItem('token');
    await axios.post(`${API_URL}/categories`, { name: newCat }, { headers: { Authorization: `Bearer ${token}` } });
    setNewCat(''); fetchCats();
  };
  const handleCreateSub = async () => {
    if (!newSub.name || !newSub.category_id) return;
    const token = localStorage.getItem('token');
    await axios.post(`${API_URL}/subcategories`, newSub, { headers: { Authorization: `Bearer ${token}` } });
    setNewSub({ name: '', category_id: '' }); fetchCats();
  };

  const handleDeleteCategory = async (id) => {
    if (!window.confirm('Excluir este Domínio e TODAS as suas subcategorias e perguntas?')) return;
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API_URL}/categories/${id}`, { headers: { Authorization: `Bearer ${token}` } });
      fetchCats();
    } catch (err) { console.error(err); alert("Erro ao excluir."); }
  };

  const handleDeleteSubcategory = async (id) => {
    if (!window.confirm('Excluir esta Estrutura e TODAS as suas perguntas?')) return;
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API_URL}/subcategories/${id}`, { headers: { Authorization: `Bearer ${token}` } });
      fetchCats();
    } catch (err) { console.error(err); alert("Erro ao excluir."); }
  };

  return (
    <div className="fade-in">
      <h4 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
        <Icon name="folder" color="var(--primary)" /> Gerenciar Domínios e Estrutura
      </h4>
      <div className="creation-header" style={{ marginBottom: '3rem' }}>
        <div className="glass-card">
          <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: '700', letterSpacing: '1px' }}>NOVO DOMÍNIO</label>
          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
            <input value={newCat} onChange={e => setNewCat(e.target.value)} placeholder="Ex: Governança" style={{ marginBottom: 0 }} onKeyDown={e => e.key === 'Enter' && handleCreateCategory()} />
            <button className="btn-primary" onClick={handleCreateCategory}><Icon name="plus" /></button>
          </div>
        </div>
        <div className="glass-card">
          <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: '700', letterSpacing: '1px' }}>NOVA SUBCATEGORIA</label>
          <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
            <select value={newSub.category_id} onChange={e => setNewSub({ ...newSub, category_id: e.target.value })} style={{ marginBottom: 0 }}>
              <option value="">Destino...</option>
              {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
            <input value={newSub.name} onChange={e => setNewSub({ ...newSub, name: e.target.value })} placeholder="Ex: Estratégia" style={{ marginBottom: 0 }} />
            <button className="btn-primary" onClick={handleCreateSub} disabled={!newSub.category_id}><Icon name="plus" /></button>
          </div>
        </div>
      </div>
      <div className="questions-explorer">
        {categories.map(cat => (
          <div key={cat.id} className="group-container">
            <div className="group-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span><Icon name="folder" size={24} /> {cat.name}</span>
              <button className="icon-btn delete" onClick={() => handleDeleteCategory(cat.id)}><Icon name="trash" size={18} /></button>
            </div>
            {cat.subcategories.map(sub => (
              <div key={sub.id} className="subgroup-container" style={{ paddingBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div className="subgroup-title" style={{ marginBottom: 0 }}><Icon name="stats" size={16} color="var(--text-muted)" /> {sub.name}</div>
                <button className="icon-btn delete" onClick={() => handleDeleteSubcategory(sub.id)}><Icon name="trash" size={16} /></button>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};

// ─── Evaluator: Question Bank ──────────────────────────────────────────────────
const EvaluatorQuestions = () => {
  const [categories, setCategories] = useState([]);
  const [newQuest, setNewQuest] = useState({ text: '', subcategory_id: '' });
  const [aiSuggestions, setAiSuggestions] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);

  const fetchCats = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API_URL}/categories`, { headers: { Authorization: `Bearer ${token}` } });
      setCategories(res.data);
    } catch (err) { console.error(err); }
  };
  useEffect(() => { fetchCats(); }, []);

  const handleCreateQuest = async (textToUse = null) => {
    const text = textToUse || newQuest.text;
    if (!text || !newQuest.subcategory_id) return;
    const token = localStorage.getItem('token');
    await axios.post(`${API_URL}/questions`, { ...newQuest, text }, { headers: { Authorization: `Bearer ${token}` } });
    if (!textToUse) setNewQuest({ ...newQuest, text: '' });
    fetchCats();
  };
  const handleDeleteQuest = async (id) => {
    if (!window.confirm('Excluir esta pergunta?')) return;
    const token = localStorage.getItem('token');
    await axios.delete(`${API_URL}/questions/${id}`, { headers: { Authorization: `Bearer ${token}` } });
    fetchCats();
  };
  const handleEditQuest = async (id, currentText) => {
    const newText = window.prompt('Editar pergunta:', currentText);
    if (!newText || newText === currentText) return;
    const token = localStorage.getItem('token');
    await axios.put(`${API_URL}/questions/${id}`, { text: newText }, { headers: { Authorization: `Bearer ${token}` } });
    fetchCats();
  };
  const handleSuggestAI = async () => {
    if (!newQuest.subcategory_id) return alert('Selecione uma subcategoria!');
    setIsGenerating(true);
    try {
      const token = localStorage.getItem('token');
      let catName = '', subName = '';
      categories.forEach(c => {
        const s = c.subcategories.find(sb => sb.id === parseInt(newQuest.subcategory_id));
        if (s) { catName = c.name; subName = s.name; }
      });
      const res = await axios.post(`${API_URL}/ai/generate-questions`, { category: catName, subcategory: subName }, { headers: { Authorization: `Bearer ${token}` } });
      setAiSuggestions(res.data.suggestions);
    } catch (err) { console.error(err); } finally { setIsGenerating(false); }
  };

  return (
    <div className="fade-in">
      <h4 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
        <Icon name="help" color="var(--primary)" /> Gerenciar Banco de Questões
      </h4>
      <div className="glass-card" style={{ marginBottom: '3rem' }}>
        <h4 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '0.9rem' }}>
          <Icon name="plus" color="var(--primary)" /> Nova Pergunta
        </h4>
        <div className="stack-mobile" style={{ display: 'grid', gridTemplateColumns: 'minmax(200px, 300px) 1fr 120px', gap: '1.5rem', alignItems: 'end' }}>
          <div>
            <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: '700' }}>DESTINO TÉCNICO</label>
            <select value={newQuest.subcategory_id} onChange={e => { setNewQuest({ ...newQuest, subcategory_id: e.target.value }); setAiSuggestions([]); }} style={{ marginBottom: 0, marginTop: '0.5rem' }}>
              <option value="">Selecione a Subcategoria...</option>
              {categories.flatMap(c => c.subcategories.map(s => ({ ...s, catName: c.name }))).map(s => (
                <option key={s.id} value={s.id}>{s.catName} / {s.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: '700' }}>ENUNCIADO DA PERGUNTA</label>
            <input value={newQuest.text} onChange={e => setNewQuest({ ...newQuest, text: e.target.value })} placeholder="Descreva o critério de avaliação..." style={{ marginBottom: 0, marginTop: '0.5rem' }} />
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button className="btn-primary" onClick={() => handleCreateQuest()} style={{ padding: '0.9rem 1rem' }}><Icon name="plus" size={20} color="#00363d" /></button>
            <button className="btn-secondary" onClick={handleSuggestAI} disabled={isGenerating} style={{ padding: '0.9rem 1rem' }}>
              {isGenerating ? <div className="loader" /> : <Icon name="sparkles" size={20} color="var(--primary)" />}
            </button>
          </div>
        </div>
        {aiSuggestions.length > 0 && (
          <div style={{ marginTop: '2rem', padding: '1.5rem', background: 'rgba(0,229,255,.03)', borderRadius: '15px', border: '1px solid rgba(0,229,255,.1)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', color: 'var(--primary)', fontSize: '0.8rem', fontWeight: '700' }}>
              <Icon name="sparkles" size={14} /> SUGESTÕES GERADAS POR IA
            </div>
            {aiSuggestions.map((sug, idx) => (
              <div key={idx} className="question-row" style={{ marginBottom: '0.5rem', background: 'var(--surface-high)' }}>
                <span style={{ fontSize: '0.9rem' }}>{sug}</span>
                <button className="btn-primary" style={{ padding: '0.5rem 1rem', fontSize: '0.75rem' }} onClick={() => { handleCreateQuest(sug); setAiSuggestions(aiSuggestions.filter(s => s !== sug)); }}>Adicionar</button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="questions-explorer">
        {categories.map(cat => (
          <div key={cat.id} className="group-container">
            <div className="group-title"><Icon name="folder" size={24} /> {cat.name}</div>
            {cat.subcategories.map(sub => (
              <div key={sub.id} className="subgroup-container">
                <div className="subgroup-title"><Icon name="stats" size={16} color="var(--text-muted)" /> {sub.name}</div>
                <div className="questions-list">
                  {sub.questions.map(q => (
                    <div key={q.id} className="question-row">
                      <span style={{ fontSize: '0.95rem' }}>{q.text}</span>
                      <div className="action-btns">
                        <button className="icon-btn edit" onClick={() => handleEditQuest(q.id, q.text)}><Icon name="edit" size={18} /></button>
                        <button className="icon-btn delete" onClick={() => handleDeleteQuest(q.id)}><Icon name="trash" size={18} /></button>
                      </div>
                    </div>
                  ))}
                  {sub.questions.length === 0 && <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', padding: '1rem' }}>Sem perguntas nesta seção.</p>}
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Evaluator: Invite Panel ──────────────────────────────────────────────────
const EvaluatorInvitePanel = () => {
  const [companies, setCompanies] = useState([]);
  const [categories, setCategories] = useState([]);
  const [form, setForm] = useState({ company_id: '', category_ids: [], message: '' });
  const [invites, setInvites] = useState([]);
  const [sending, setSending] = useState(false);
  const [success, setSuccess] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [viewingChatId, setViewingChatId] = useState(null);
  const [viewingFeedbackId, setViewingFeedbackId] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const headers = { Authorization: `Bearer ${token}` };
    axios.get(`${API_URL}/users/companies`, { headers }).then(r => setCompanies(r.data)).catch(console.error);
    axios.get(`${API_URL}/categories`, { headers }).then(r => setCategories(r.data)).catch(console.error);
  }, []);

  useEffect(() => {
    const token = localStorage.getItem('token');
    axios.get(`${API_URL}/invites/my?page=${page}&limit=10`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => {
        setInvites(r.data.items);
        setTotalPages(r.data.pages);
      }).catch(console.error);
  }, [success, page]);

  const toggleCategory = (id) => {
    setForm(f => ({
      ...f,
      category_ids: f.category_ids.includes(id)
        ? f.category_ids.filter(c => c !== id)
        : [...f.category_ids, id]
    }));
  };

  const sendInvite = async () => {
    if (!form.company_id || form.category_ids.length === 0) return alert('Selecione a empresa e ao menos uma categoria.');
    setSending(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API_URL}/invites`, {
        company_id: parseInt(form.company_id),
        category_ids: form.category_ids,
        message: form.message,
      }, { headers: { Authorization: `Bearer ${token}` } });
      setSuccess(s => !s);
      setForm({ company_id: '', category_ids: [], message: '' });
    } catch (err) { alert('Erro ao enviar convite.'); }
    finally { setSending(false); }
  };

  const handleViewChat = async (assessmentId) => {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API_URL}/assessments/${assessmentId}/session`, { headers: { Authorization: `Bearer ${token}` } });
      setViewingChatId(res.data.id);
    } catch (err) { alert('Erro ao carregar histórico do chat.'); }
  };

  const statusColors = { PENDING: 'var(--warning)', ACCEPTED: 'var(--success)', EXPIRED: 'var(--text-muted)' };
  const statusLabels = { PENDING: 'Pendente', ACCEPTED: 'Aceito', EXPIRED: 'Expirado' };

  if (viewingChatId) return <InterviewChat sessionId={viewingChatId} readOnly={true} onBack={() => setViewingChatId(null)} />;
  if (viewingFeedbackId) return <FeedbackReport assessmentId={viewingFeedbackId} onBack={() => setViewingFeedbackId(null)} />;

  return (
    <div className="fade-in">
      {/* Form */}
      <div className="glass-card" style={{ marginBottom: '3rem' }}>
        <h4 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <Icon name="mail" color="var(--primary)" /> Enviar Convite de Entrevista
        </h4>
        <div className="stack-mobile" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
          <div>
            <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: '700' }}>EMPRESA</label>
            <select value={form.company_id} onChange={e => setForm({ ...form, company_id: e.target.value })} style={{ marginTop: '0.5rem' }}>
              <option value="">Selecione a empresa...</option>
              {companies.map(c => <option key={c.id} value={c.id}>{c.company_name || c.username}</option>)}
            </select>
          </div>
          <div>
            <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: '700' }}>MENSAGEM (OPCIONAL)</label>
            <input value={form.message} onChange={e => setForm({ ...form, message: e.target.value })} placeholder="Adicione uma mensagem personalizada..." style={{ marginTop: '0.5rem' }} />
          </div>
        </div>
        <div style={{ marginTop: '0.5rem' }}>
          <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: '700' }}>CATEGORIAS A COBRIR</label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.8rem', marginTop: '1rem' }}>
            {categories.map(cat => (
              <button key={cat.id}
                onClick={() => toggleCategory(cat.id)}
                className={form.category_ids.includes(cat.id) ? 'btn-primary' : 'btn-secondary'}
                style={{ padding: '0.6rem 1.2rem', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <Icon name="folder" size={14} color={form.category_ids.includes(cat.id) ? '#00363d' : 'currentColor'} />
                {cat.name}
                {form.category_ids.includes(cat.id) && <Icon name="check" size={12} color="#00363d" />}
              </button>
            ))}
          </div>
        </div>
        <button className="btn-primary" onClick={sendInvite} disabled={sending || !form.company_id || form.category_ids.length === 0} style={{ marginTop: '1.5rem' }}>
          {sending ? <div className="loader" /> : <><Icon name="mail" size={16} color="#00363d" /> Enviar Convite</>}
        </button>
      </div>

      {/* Invites List */}
      <h4 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
        <Icon name="clock" color="var(--text-muted)" /> Convites Enviados
      </h4>
      {invites.length === 0 && <p style={{ color: 'var(--text-muted)' }}>Nenhum convite enviado ainda.</p>}
      <div style={{ display: 'grid', gap: '1rem' }}>
        {invites.map(inv => (
          <div key={inv.id} className="glass-card" style={{ padding: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <p style={{ fontWeight: '700' }}>{inv.company?.company_name || inv.company?.username}</p>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.3rem' }}>
                {inv.category_ids?.length} categoria(s) · {new Date(inv.created_at).toLocaleDateString('pt-BR')}
              </p>
              {inv.message && <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontStyle: 'italic', marginTop: '0.3rem' }}>"{inv.message}"</p>}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <span style={{ padding: '0.4rem 1rem', borderRadius: '20px', fontSize: '0.75rem', fontWeight: '700', background: `${statusColors[inv.status]}20`, color: statusColors[inv.status] }}>
                {statusLabels[inv.status]}
              </span>
              {inv.assessment && ['COMPLETED', 'FEEDBACK_READY'].includes(inv.assessment.status) && (
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button onClick={() => handleViewChat(inv.assessment.id)} className="btn-secondary" style={{ padding: '0.5rem 1rem', display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.75rem' }}>
                    <Icon name="chat" size={14} /> Histórico
                  </button>
                  <button onClick={() => setViewingFeedbackId(inv.assessment.id)} className="btn-primary" style={{ padding: '0.5rem 1rem', display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.75rem' }}>
                    <Icon name="report" size={14} color="#00363d" /> Resultados
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
    </div>
  );
};

// ─── Company: Invites & Interviews ────────────────────────────────────────────
const CompanyInterviews = ({ onStartInterview }) => {
  const [invites, setInvites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [startingInterview, setStartingInterview] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const fetchInvites = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API_URL}/invites/my?page=${page}&limit=10`, { headers: { Authorization: `Bearer ${token}` } });
      setInvites(res.data.items);
      setTotalPages(res.data.pages);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchInvites(); }, [page]);

  const startGuidedInterview = async (inviteId, mode = 'GUIDED') => {
    setStartingInterview(true);
    try {
      const token = localStorage.getItem('token');
      const res = await axios.post(`${API_URL}/interviews/start`, {
        invite_id: inviteId,
        mode: mode,
      }, { headers: { Authorization: `Bearer ${token}` } });
      onStartInterview(res.data.id, res.data.assessment_id, mode, inviteId);
    } catch (err) {
      setStartingInterview(false);
      alert(err.response?.data?.detail || 'Erro ao iniciar entrevista.');
    }
  };

  const startAutonomousInterview = async () => {
    setStartingInterview(true);
    try {
      const token = localStorage.getItem('token');
      const res = await axios.post(`${API_URL}/interviews/start`, {
        mode: 'AUTONOMOUS',
      }, { headers: { Authorization: `Bearer ${token}` } });
      onStartInterview(res.data.id, res.data.assessment_id, 'AUTONOMOUS');
    } catch (err) {
      setStartingInterview(false);
      alert(err.response?.data?.detail || 'Erro ao iniciar entrevista autônoma.');
    }
  };

  // ─── Tela de Carregamento Premium ──────────────────────────────────────
  if (startingInterview) {
    return (
      <div className="interview-loading-screen">
        <div className="interview-loading-content">
          <div className="interview-loading-orb">
            <div className="interview-loading-orb-inner">
              <Icon name="sparkles" size={36} color="#00363d" />
            </div>
            <div className="interview-loading-ring" />
            <div className="interview-loading-ring ring-2" />
          </div>
          <h2 className="interview-loading-title">Preparando sua entrevista</h2>
          <p className="interview-loading-subtitle">
            O agente de IA está sendo configurado para conduzir sua avaliação de maturidade...
          </p>
          <div className="interview-loading-bar">
            <div className="interview-loading-bar-fill" />
          </div>
          <div className="interview-loading-steps">
            <span className="step active">Inicializando agente</span>
            <span className="step-dot">→</span>
            <span className="step">Carregando contexto</span>
            <span className="step-dot">→</span>
            <span className="step">Pronto!</span>
          </div>
        </div>
      </div>
    );
  }

  if (loading) return <div className="glass-card">Carregando...</div>;

  const pending = invites.filter(i => i.status === 'PENDING');
  const accepted = invites.filter(i => i.status === 'ACCEPTED');

  return (
    <div className="fade-in">
      {/* Autonomous */}
      <div className="glass-card" style={{ marginBottom: '2rem', background: 'linear-gradient(135deg, rgba(0,229,255,0.05), rgba(0,0,0,0))' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', marginBottom: '0.8rem' }}>
              <div style={{ padding: '0.5rem', background: 'rgba(0,229,255,0.1)', borderRadius: '10px' }}>
                <Icon name="robot" color="var(--primary)" size={20} />
              </div>
              <h4>Avaliação Autônoma</h4>
            </div>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '500px' }}>
              O agente de IA conduz uma entrevista completa baseada em frameworks COBIT, ITIL e ISO 27001, sem necessidade de convite de avaliador.
            </p>
          </div>
          <button className="btn-primary" onClick={startAutonomousInterview} style={{ minWidth: '180px' }}>
            <Icon name="sparkles" size={16} color="#00363d" /> Iniciar Agora
          </button>
        </div>
      </div>

      {/* Pending Invites */}
      <h4 style={{ marginBottom: '1.2rem', display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
        <Icon name="mail" color="var(--primary)" /> Convites Pendentes
        {pending.length > 0 && <span style={{ background: 'var(--primary)', color: '#00363d', borderRadius: '20px', padding: '0.1rem 0.6rem', fontSize: '0.75rem', fontWeight: '800' }}>{pending.length}</span>}
      </h4>
      {pending.length === 0 && <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>Nenhum convite pendente.</p>}
      <div style={{ display: 'grid', gap: '1rem', marginBottom: '2.5rem' }}>
        {pending.map(inv => (
          <div key={inv.id} className="glass-card" style={{ padding: '1.5rem 2rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', marginBottom: '0.5rem' }}>
                <Icon name="users" size={16} color="var(--primary)" />
                <p style={{ fontWeight: '700' }}>Avaliador: {inv.evaluator?.username}</p>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                {inv.category_ids?.length} categoria(s) · Recebido em {new Date(inv.created_at).toLocaleDateString('pt-BR')}
              </p>
              {inv.message && <p style={{ fontSize: '0.85rem', marginTop: '0.5rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>"{inv.message}"</p>}
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.8rem' }}>
              <button className="btn-secondary" onClick={() => startGuidedInterview(inv.id, 'MANUAL_FORM')} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}>
                <Icon name="report" size={14} /> Responder Formulário
              </button>
              <button className="btn-primary" onClick={() => startGuidedInterview(inv.id, 'GUIDED')} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}>
                <Icon name="chat" size={16} color="#00363d" /> Modo Chat (IA)
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* In Progress */}
      {accepted.length > 0 && (
        <>
          <h4 style={{ marginBottom: '1.2rem', display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
            <Icon name="clock" color="var(--text-muted)" /> Em Andamento / Concluídos
          </h4>
          <div style={{ display: 'grid', gap: '1rem' }}>
            {accepted.map(inv => (
              <div key={inv.id} className="glass-card" style={{ padding: '1.5rem 2rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', opacity: 0.7 }}>
                <div>
                  <p style={{ fontWeight: '700' }}>Avaliador: {inv.evaluator?.username}</p>
                  <p style={{ fontSize: '0.8rem', color: 'var(--success)', marginTop: '0.3rem' }}>
                    ✓ Iniciado em {inv.accepted_at ? new Date(inv.accepted_at).toLocaleDateString('pt-BR') : '-'}
                  </p>
                </div>
                <span style={{ fontSize: '0.75rem', color: 'var(--success)', fontWeight: '700' }}>ACEITO</span>
              </div>
            ))}
          </div>
        </>
      )}
      <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
    </div>
  );
};

// ─── Company: My Feedbacks ─────────────────────────────────────────────────────
const CompanyFeedbacks = ({ onViewFeedback }) => {
  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    const fetchAssessments = async () => {
      try {
        setLoading(true);
        const token = localStorage.getItem('token');
        const res = await axios.get(`${API_URL}/assessments/my/list?page=${page}&limit=10`, { headers: { Authorization: `Bearer ${token}` } });
        setAssessments(res.data.items);
        setTotalPages(res.data.pages);
      } catch (err) { console.error(err); }
      finally { setLoading(false); }
    };
    fetchAssessments();
  }, [page]);

  const modeLabels = { GUIDED: 'Guiada', AUTONOMOUS: 'Autônoma' };
  const statusLabels = { PENDING: 'Pendente', IN_PROGRESS: 'Em Andamento', COMPLETED: 'Concluída', FEEDBACK_READY: 'Feedback Pronto' };
  const statusColors = { PENDING: 'var(--text-muted)', IN_PROGRESS: 'var(--warning)', COMPLETED: 'var(--primary)', FEEDBACK_READY: 'var(--success)' };

  if (loading) return <div className="glass-card">Carregando...</div>;
  if (assessments.length === 0) return (
    <div className="glass-card" style={{ textAlign: 'center', padding: '4rem' }}>
      <Icon name="report" size={40} color="var(--text-muted)" />
      <p style={{ color: 'var(--text-muted)', marginTop: '1rem' }}>Nenhuma avaliação encontrada.</p>
    </div>
  );

  return (
    <div className="fade-in" style={{ display: 'grid', gap: '1rem' }}>
      {assessments.map(a => (
        <div key={a.id} className="glass-card" style={{ padding: '1.5rem 2rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', gap: '0.8rem', alignItems: 'center', marginBottom: '0.5rem' }}>
              <span style={{ fontSize: '0.7rem', padding: '0.2rem 0.8rem', borderRadius: '10px', background: 'rgba(0,229,255,0.1)', color: 'var(--primary)', fontWeight: '700' }}>
                {modeLabels[a.mode] || a.mode}
              </span>
              <span style={{ fontSize: '0.7rem', padding: '0.2rem 0.8rem', borderRadius: '10px', background: `${statusColors[a.status]}15`, color: statusColors[a.status], fontWeight: '700' }}>
                {statusLabels[a.status] || a.status}
              </span>
            </div>
            <p style={{ fontWeight: '600' }}>Avaliação #{a.id}</p>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              {new Date(a.created_at).toLocaleDateString('pt-BR')}
            </p>
          </div>
          {a.has_feedback && (
            <button className="btn-primary" onClick={() => onViewFeedback(a.id)}>
              <Icon name="report" size={16} color="#00363d" /> Ver Feedback
            </button>
          )}
        </div>
      ))}
      <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
    </div>
  );
};

// ─── Company: Dashboard Home ───────────────────────────────────────────────────
const CompanyHome = ({ onGoToInterviews, onGoToFeedbacks }) => {
  const [assessments, setAssessments] = useState([]);
  const [invites, setInvites] = useState([]);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const headers = { Authorization: `Bearer ${token}` };
    axios.get(`${API_URL}/assessments/my/list?limit=100`, { headers }).then(r => setAssessments(r.data.items || [])).catch(() => {});
    axios.get(`${API_URL}/invites/my?limit=100`, { headers }).then(r => setInvites(r.data.items || [])).catch(() => {});
  }, []);

  const pendingInvites = invites.filter(i => i.status === 'PENDING').length;
  const completedWithFeedback = assessments.filter(a => a.has_feedback).length;
  const lastAssessment = assessments[0];

  return (
    <div className="fade-in">
      <div className="stack-mobile" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem', marginBottom: '3rem' }}>
        <div className="glass-card" style={{ cursor: 'pointer' }} onClick={onGoToInterviews}>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Convites Pendentes</p>
          <h2 style={{ color: pendingInvites > 0 ? 'var(--warning)' : 'var(--text-main)' }}>{pendingInvites}</h2>
        </div>
        <div className="glass-card" style={{ cursor: 'pointer' }} onClick={onGoToFeedbacks}>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Feedbacks Disponíveis</p>
          <h2 style={{ color: 'var(--success)' }}>{completedWithFeedback}</h2>
        </div>
        <div className="glass-card">
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Total de Avaliações</p>
          <h2 style={{ color: 'var(--primary)' }}>{assessments.length}</h2>
        </div>
      </div>

      {lastAssessment?.has_feedback && (
        <div className="glass-card" style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <p style={{ fontSize: '0.8rem', color: 'var(--primary)', fontWeight: '700', marginBottom: '0.5rem' }}>ÚLTIMO FEEDBACK DISPONÍVEL</p>
            <p style={{ fontWeight: '700' }}>Avaliação #{lastAssessment.id} · {new Date(lastAssessment.created_at).toLocaleDateString('pt-BR')}</p>
          </div>
          <button className="btn-primary" onClick={onGoToFeedbacks}>Ver Feedback <Icon name="arrow" size={16} color="#00363d" /></button>
        </div>
      )}

      <div className="stack-mobile" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        <div className="glass-card" style={{ textAlign: 'center', padding: '3rem' }}>
          <div style={{ padding: '1rem', background: 'rgba(0,229,255,0.1)', borderRadius: '50%', width: 'fit-content', margin: '0 auto 1.5rem' }}>
            <Icon name="mail" size={32} color="var(--primary)" />
          </div>
          <h4 style={{ marginBottom: '0.8rem' }}>Entrevista Guiada</h4>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '2rem' }}>Responda a entrevistas enviadas por avaliadores especializados</p>
          <button className="btn-secondary" onClick={onGoToInterviews}>Ver Convites</button>
        </div>
        <div className="glass-card" style={{ textAlign: 'center', padding: '3rem', background: 'linear-gradient(135deg, rgba(0,229,255,0.05), rgba(0,0,0,0))' }}>
          <div style={{ padding: '1rem', background: 'rgba(0,229,255,0.15)', borderRadius: '50%', width: 'fit-content', margin: '0 auto 1.5rem' }}>
            <Icon name="sparkles" size={32} color="var(--primary)" />
          </div>
          <h4 style={{ marginBottom: '0.8rem' }}>Avaliação Autônoma</h4>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '2rem' }}>O AI Agent conduz a entrevista completa sem avaliador</p>
          <button className="btn-primary" onClick={onGoToInterviews}>Iniciar Agora</button>
        </div>
      </div>
    </div>
  );
};

// ─── Sidebar ──────────────────────────────────────────────────────────────────
const Sidebar = ({ activeTab, setActiveTab, role, logout, open, onClose }) => {
  const menuItems = {
    ADMIN: [
      { id: 'MAIN', label: 'Monitoramento', icon: 'stats' },
      { id: 'USERS', label: 'Usuários', icon: 'users' },
      { id: 'settings', label: 'Configurações', icon: 'settings' },
    ],
    EVALUATOR: [
      { id: 'MAIN', label: 'Início', icon: 'home' },
      { id: 'categories', label: 'Domínios / Estrutura', icon: 'folder' },
      { id: 'questions', label: 'Banco de Questões', icon: 'help' },
      { id: 'invites', label: 'Entrevistas', icon: 'mail' },
      { id: 'settings', label: 'Configurações', icon: 'settings' },
    ],
    COMPANY: [
      { id: 'MAIN', label: 'Início', icon: 'home' },
      { id: 'interviews', label: 'Entrevistas', icon: 'chat' },
      { id: 'feedbacks', label: 'Meus Feedbacks', icon: 'report' },
    ],
  };
  return (
    <aside className={`sidebar ${open ? 'open' : ''}`}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '4rem' }}>
        <div style={{ width: '45px', height: '45px', background: 'var(--primary)', borderRadius: '14px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#00363d' }}>
          <Icon name="sparkles" />
        </div>
        <h2 style={{ letterSpacing: '-1px', fontSize: '1.3rem', fontWeight: '900', flex: 1 }}>AVALIA.<span style={{ color: 'var(--primary)' }}>AI</span></h2>
        {onClose && (
          <button onClick={onClose} className="hide-desktop" aria-label="Fechar menu"
            style={{ background: 'transparent', border: 'none', color: 'var(--text-main)', cursor: 'pointer', padding: '0.4rem' }}>
            <Icon name="close" size={22} />
          </button>
        )}
      </div>
      <nav className="sidebar-nav" style={{ flex: 1 }}>
        {menuItems[role]?.map(item => (
          <button key={item.id} className={`sidebar-item ${activeTab === item.id ? 'active' : ''}`} onClick={() => setActiveTab(item.id)}>
            <Icon name={item.icon} size={20} /> {item.label}
          </button>
        ))}
      </nav>
      <div style={{ marginTop: 'auto', borderTop: '1px solid var(--glass-border)', paddingTop: '2rem' }}>
        <button onClick={logout} className="sidebar-item" style={{ color: 'var(--danger)' }}>
          <Icon name="logout" size={20} /> Encerrar Sessão
        </button>
      </div>
    </aside>
  );
};

// ─── Top Navbar ───────────────────────────────────────────────────────────────
const TopNavbar = ({ user, activeTab, onMenuClick }) => {
  const labels = {
    MAIN: 'Painel Central', categories: 'Domínios e Estrutura', questions: 'Base de Conhecimento',
    invites: 'Entrevistas', interviews: 'Minhas Entrevistas', feedbacks: 'Meus Feedbacks',
    settings: 'Configurações do AI Agent'
  };
  return (
    <header className="top-navbar">
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', minWidth: 0 }}>
        <button className="hamburger-btn hide-desktop" onClick={onMenuClick} aria-label="Abrir menu">
          <Icon name="menu" size={22} />
        </button>
        <div className="breadcrumb">
          <Icon name="home" size={14} />
          <span style={{ opacity: 0.2 }}>/</span>
          <span style={{ color: 'var(--text-main)', fontWeight: '700', fontSize: '0.9rem' }}>{labels[activeTab] || activeTab}</span>
        </div>
      </div>
      <div className="user-badge" style={{ padding: '0.8rem 1.5rem' }}>
        <div style={{ textAlign: 'right' }}>
          <p style={{ fontWeight: '800', fontSize: '0.9rem' }}>{user?.username?.toUpperCase()}</p>
          <p style={{ fontSize: '0.65rem', color: 'var(--primary)', fontWeight: '800', letterSpacing: '1px' }}>{user?.role}</p>
        </div>
        <div style={{ width: '38px', height: '38px', background: 'var(--surface-highest)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid var(--glass-border)' }}>
          <Icon name="users" size={16} />
        </div>
      </div>
    </header>
  );
};

// ─── Main Dashboard ───────────────────────────────────────────────────────────
const Dashboard = () => {
  const { user, logout } = useAuth();
  const [view, setView] = useState('MAIN');  // MAIN | INTERVIEW | FEEDBACK
  const [activeTab, setActiveTab] = useState('MAIN');
  const [interviewData, setInterviewData] = useState({ sessionId: null, assessmentId: null, mode: null, inviteId: null });
  const [feedbackAssessmentId, setFeedbackAssessmentId] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [navOpen, setNavOpen] = useState(false);

  useEffect(() => {
    document.body.style.overflow = navOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [navOpen]);

  const handleStartInterview = (sessionId, assessmentId, mode = 'GUIDED', inviteId = null) => {
    setInterviewData({ sessionId, assessmentId, mode, inviteId });
    setView(mode === 'MANUAL_FORM' ? 'FORM' : 'INTERVIEW');
  };

  const handleInterviewComplete = (assessmentId) => {
    setFeedbackAssessmentId(assessmentId);
    setView('FEEDBACK');
  };

  const handleViewFeedback = (assessmentId) => {
    setFeedbackAssessmentId(assessmentId);
    setView('FEEDBACK');
  };

  const handleSidebarNav = (tab) => {
    setView('MAIN');
    setActiveTab(tab);
    setNavOpen(false);
  };

  const handleBack = () => {
    setView('MAIN');
    setRefreshKey(prev => prev + 1);
  };

  // Full-screen views (no sidebar)
  if (view === 'INTERVIEW') {
    return (
      <InterviewChat
        sessionId={interviewData.sessionId}
        onComplete={handleInterviewComplete}
        onBack={handleBack}
      />
    );
  }

  if (view === 'FORM') {
    return (
      <ManualForm
        assessmentId={interviewData.assessmentId}
        inviteId={interviewData.inviteId}
        onComplete={() => handleInterviewComplete(interviewData.assessmentId)}
        onBack={handleBack}
      />
    );
  }

  if (view === 'FEEDBACK') {
    return (
      <FeedbackReport
        assessmentId={feedbackAssessmentId}
        onBack={handleBack}
      />
    );
  }

  return (
    <div className="layout-wrapper">
      {navOpen && <div className="sidebar-backdrop hide-desktop" onClick={() => setNavOpen(false)} />}
      <Sidebar activeTab={activeTab} setActiveTab={handleSidebarNav} role={user?.role} logout={logout} open={navOpen} onClose={() => setNavOpen(false)} />
      <div className="main-content">
        <TopNavbar user={user} activeTab={activeTab} onMenuClick={() => setNavOpen(true)} />
        <main className="dashboard-main" style={{ padding: '4rem' }}>
          {/* ADMIN */}
          {user?.role === 'ADMIN' && activeTab === 'MAIN' && <AdminView />}
          {user?.role === 'ADMIN' && activeTab === 'USERS' && <AdminUsersView />}

          {/* EVALUATOR */}
          {user?.role === 'EVALUATOR' && activeTab === 'MAIN' && (
            <div className="fade-in glass-card" style={{ textAlign: 'center', padding: '5rem 2rem' }}>
              <h2 style={{ fontSize: '3rem', marginBottom: '1rem' }}>Olá, Avaliador</h2>
              <p style={{ color: 'var(--text-muted)', marginBottom: '3rem', fontSize: '1.1rem' }}>Gerencie o banco de questões ou envie convites de entrevista.</p>
              <div style={{ display: 'flex', gap: '2rem', justifyContent: 'center' }}>
                <button className="btn-primary" onClick={() => setActiveTab('invites')} style={{ padding: '2.5rem', flex: 1, maxWidth: '350px', fontSize: '1.1rem' }}>
                  <Icon name="mail" size={24} color="#00363d" /> Enviar Convite
                </button>
                <button className="btn-secondary" onClick={() => setActiveTab('questions')} style={{ padding: '2.5rem', flex: 1, maxWidth: '350px', fontSize: '1.1rem' }}>
                  <Icon name="help" size={24} /> Banco de Questões
                </button>
              </div>
            </div>
          )}
          {user?.role === 'EVALUATOR' && activeTab === 'categories' && <EvaluatorDomains />}
          {user?.role === 'EVALUATOR' && activeTab === 'questions' && <EvaluatorQuestions />}
          {user?.role === 'EVALUATOR' && activeTab === 'invites' && <EvaluatorInvitePanel />}

          {/* EVALUATOR & ADMIN Settings */}
          {(user?.role === 'EVALUATOR' || user?.role === 'ADMIN') && activeTab === 'settings' && <AppConfigSettings />}

          {/* COMPANY */}
          {user?.role === 'COMPANY' && activeTab === 'MAIN' && (
            <CompanyHome
              onGoToInterviews={() => setActiveTab('interviews')}
              onGoToFeedbacks={() => setActiveTab('feedbacks')}
            />
          )}
          {user?.role === 'COMPANY' && activeTab === 'interviews' && (
            <CompanyInterviews key={`int-${refreshKey}`} onStartInterview={handleStartInterview} />
          )}
          {user?.role === 'COMPANY' && activeTab === 'feedbacks' && (
            <CompanyFeedbacks key={`fb-${refreshKey}`} onViewFeedback={handleViewFeedback} />
          )}
        </main>
      </div>
    </div>
  );
};

export default Dashboard;
