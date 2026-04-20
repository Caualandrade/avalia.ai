import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_URL } from '../config';

const Icon = ({ name, size = 18, color = 'currentColor' }) => {
  const icons = {
    check:     <><polyline points="20 6 9 17 4 12"/></>,
    arrowLeft: <><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></>,
    send:      <><line x1="22" y1="2" x2="11" y2="13"/><polyline points="22 2 15 22 11 13 2 9 22 2"/></>,
    help:      <><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></>,
  };
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24"
      fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      {icons[name]}
    </svg>
  );
};

const ManualForm = ({ assessmentId, inviteId, onComplete, onBack }) => {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [answers, setAnswers] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    const fetchQuestions = async () => {
      try {
        const token = localStorage.getItem('token');
        const inviteRes = await axios.get(`${API_URL}/invites/my`, { headers: { Authorization: `Bearer ${token}` } });
        const invite = inviteRes.data.items.find(i => i.id === inviteId);
        
        if (invite) {
          const catIds = invite.category_ids;
          const allCatsRes = await axios.get(`${API_URL}/categories`, { headers: { Authorization: `Bearer ${token}` } });
          const filteredCats = allCatsRes.data.filter(c => catIds.includes(c.id));
          setCategories(filteredCats);
        }
      } catch (err) {
        console.error("Erro ao buscar perguntas do formulário:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchQuestions();
  }, [inviteId]);

  const handleAnswerChange = (questionId, value) => {
    setAnswers(prev => ({ ...prev, [questionId]: value }));
  };

  const handleSubmit = async () => {
    const totalQuestions = categories.reduce((acc, cat) => 
      acc + cat.subcategories.reduce((acc2, sub) => acc2 + sub.questions.length, 0), 0);
    
    if (Object.keys(answers).length < totalQuestions) {
      if (!window.confirm("Algumas perguntas não foram respondidas. Deseja enviar mesmo assim?")) return;
    }

    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      const payload = {
        answers: Object.keys(answers).map(qId => ({
          question_id: parseInt(qId),
          raw_answer: answers[qId]
        }))
      };
      await axios.post(`${API_URL}/assessments/${assessmentId}/submit-form`, payload, { 
        headers: { Authorization: `Bearer ${token}` } 
      });
      
      setSubmitted(true);
      // Aguarda 2 segundos para o usuário ler a mensagem de sucesso antes de ir para o feedback
      setTimeout(() => {
        onComplete();
      }, 2500);

    } catch (err) {
      setSubmitting(false);
      alert("Erro ao enviar formulário. Tente novamente.");
    }
  };

  if (loading) return (
    <div className="interview-loading-screen">
      <div className="loader" style={{ width: '50px', height: '50px' }} />
      <p style={{ marginTop: '1rem' }}>Carregando formulário...</p>
    </div>
  );

  if (submitted) return (
    <div className="interview-loading-screen">
      <div className="interview-loading-content">
        <div className="interview-loading-orb" style={{ borderColor: 'var(--success)' }}>
          <div className="interview-loading-orb-inner" style={{ background: 'var(--success)' }}>
            <Icon name="check" size={36} color="#00363d" />
          </div>
        </div>
        <h2 className="interview-loading-title">Formulário Enviado!</h2>
        <p className="interview-loading-subtitle">
          Suas respostas foram recebidas com sucesso. Agora nossa IA está analisando-as para gerar o relatório final...
        </p>
        <div className="interview-loading-bar">
          <div className="interview-loading-bar-fill" style={{ background: 'var(--success)', animationDuration: '2s' }} />
        </div>
      </div>
    </div>
  );

  return (
    <div className="fade-in manual-form-wrapper" style={{ maxWidth: '900px', margin: '0 auto', padding: '2rem' }}>
      <button className="btn-secondary" onClick={onBack} style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <Icon name="arrowLeft" size={16} /> Voltar
      </button>

      <div className="glass-card" style={{ padding: '3rem' }}>
        <h2 style={{ marginBottom: '1rem', color: 'var(--primary)' }}>Formulário de Avaliação</h2>
        <p style={{ color: 'var(--text-muted)', marginBottom: '3rem' }}>
          Responda às questões abaixo detalhadamente para que nossa IA possa processar seu nível de maturidade.
        </p>

        {categories.map(cat => (
          <div key={cat.id} style={{ marginBottom: '4rem' }}>
            <h3 style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '0.5rem', marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
               <span style={{ color: 'var(--primary)' }}>#</span> {cat.name}
            </h3>
            
            {cat.subcategories.map(sub => (
              <div key={sub.id} style={{ marginBottom: '2rem', paddingLeft: '1.5rem' }}>
                <h4 style={{ fontSize: '1rem', color: 'var(--text-main)', marginBottom: '1.5rem', opacity: 0.8 }}>{sub.name}</h4>
                
                {sub.questions.map(q => (
                  <div key={q.id} style={{ marginBottom: '2rem' }}>
                    <label style={{ display: 'block', fontSize: '1rem', marginBottom: '1rem', fontWeight: '500' }}>
                      {q.text}
                    </label>
                    <textarea
                      placeholder="Descreva a situação atual da sua empresa em relação a este critério..."
                      value={answers[q.id] || ''}
                      onChange={(e) => handleAnswerChange(q.id, e.target.value)}
                      style={{ 
                        width: '100%', 
                        minHeight: '120px', 
                        background: 'rgba(255,255,255,0.03)',
                        border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: '12px',
                        padding: '1rem',
                        color: 'white',
                        resize: 'vertical'
                      }}
                    />
                  </div>
                ))}
              </div>
            ))}
          </div>
        ))}

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '4rem', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '2rem' }}>
          <button 
            className="btn-primary" 
            onClick={handleSubmit} 
            disabled={submitting}
            style={{ padding: '1rem 3rem', fontSize: '1.1rem', borderRadius: '15px' }}
          >
            {submitting ? <div className="loader" /> : <><Icon name="send" size={18} color="#00363d" /> Finalizar e Enviar </>}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ManualForm;
