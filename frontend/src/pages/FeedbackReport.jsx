import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

const Icon = ({ name, size = 18, color = 'currentColor' }) => {
  const icons = {
    star:      <><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></>,
    thumbUp:   <><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z"/><path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></>,
    thumbDown: <><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3H10z"/><path d="M17 2h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"/></>,
    lightning: <><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></>,
    chart:     <><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></>,
    home:      <><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></>,
    sparkles:  <><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/><path d="M5 3v4"/><path d="M19 17v4"/><path d="M3 5h4"/><path d="M17 19h4"/></>,
    check:     <><polyline points="20 6 9 17 4 12"/></>,
    alert:     <><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></>,
    arrow:     <><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></>,
  };
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24"
      fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      {icons[name]}
    </svg>
  );
};

// ─── Score Gauge ──────────────────────────────────────────────────────────────
const ScoreGauge = ({ score }) => {
  const radius = 80;
  const circ = 2 * Math.PI * radius;
  const offset = circ - (score / 100) * circ;
  const color = score >= 80 ? '#00e676' : score >= 60 ? '#00e5ff' : score >= 40 ? '#ffb74d' : '#ff5252';

  return (
    <div className="fb-gauge-wrap">
      <svg width="220" height="220" viewBox="0 0 220 220">
        <circle cx="110" cy="110" r={radius} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="16" />
        <circle
          cx="110" cy="110" r={radius}
          fill="none" stroke={color} strokeWidth="16"
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          transform="rotate(-90 110 110)"
          style={{ transition: 'stroke-dashoffset 1.5s ease, stroke 0.5s ease', filter: `drop-shadow(0 0 12px ${color}80)` }}
        />
        <text x="110" y="100" textAnchor="middle" fill={color} fontSize="42" fontWeight="900" fontFamily="Outfit, sans-serif">
          {Math.round(score)}%
        </text>
        <text x="110" y="130" textAnchor="middle" fill="rgba(255,255,255,0.4)" fontSize="13" fontFamily="Outfit, sans-serif">
          Maturidade Geral
        </text>
      </svg>
    </div>
  );
};

// ─── Category Bar ─────────────────────────────────────────────────────────────
const CategoryBar = ({ name, score }) => {
  const [animated, setAnimated] = useState(false);
  useEffect(() => { setTimeout(() => setAnimated(true), 100); }, []);
  const color = score >= 80 ? 'var(--success)' : score >= 60 ? 'var(--primary)' : score >= 40 ? 'var(--warning)' : 'var(--danger)';

  return (
    <div className="fb-cat-row">
      <div className="fb-cat-header">
        <span className="fb-cat-name">{name}</span>
        <span className="fb-cat-score" style={{ color }}>{Math.round(score)}%</span>
      </div>
      <div className="fb-cat-track">
        <div className="fb-cat-fill" style={{ width: animated ? `${score}%` : '0%', background: color }} />
      </div>
    </div>
  );
};

// ─── Recommendation Card ──────────────────────────────────────────────────────
const RecommendationCard = ({ rec, index }) => {
  const isObj = typeof rec === 'object' && rec !== null;
  const title = isObj ? rec.title : `Recomendação ${index + 1}`;
  const description = isObj ? rec.description : rec;
  const priority = isObj ? rec.priority : 'média';

  const priorityColors = { alta: 'var(--danger)', média: 'var(--warning)', baixa: 'var(--success)' };
  const color = priorityColors[priority] || 'var(--text-muted)';

  return (
    <div className="fb-rec-card">
      <div className="fb-rec-priority" style={{ background: `${color}15`, borderColor: `${color}30` }}>
        <Icon name="lightning" size={14} color={color} />
        <span style={{ color, fontSize: '0.7rem', fontWeight: '700', textTransform: 'uppercase' }}>{priority}</span>
      </div>
      <p className="fb-rec-title">{title}</p>
      {description && description !== title && (
        <p className="fb-rec-desc">{description}</p>
      )}
    </div>
  );
};

// ─── Main FeedbackReport ──────────────────────────────────────────────────────
const FeedbackReport = ({ assessmentId, onBack }) => {
  const [feedback, setFeedback] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [retries, setRetries] = useState(0);

  useEffect(() => {
    const fetchFeedback = async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await axios.get(`${API_URL}/assessments/${assessmentId}/feedback`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setFeedback(res.data);
        setLoading(false);
      } catch (err) {
        if (err.response?.status === 404 && retries < 24) {
          // Aumentado para 24 tentativas (~2 minutos)
          setTimeout(() => setRetries(r => r + 1), 5000);
        } else {
          setError(
            err.response?.status === 404 
              ? 'A IA está levando mais tempo que o esperado para processar as questões. Tente recarregar em alguns instantes.' 
              : 'Não foi possível carregar o feedback.'
          );
          setLoading(false);
        }
      }
    };
    fetchFeedback();
  }, [assessmentId, retries]);

  const loadingMessages = [
    "Analisando suas respostas...",
    "Calculando maturidade por domínio...",
    "A IA está processando as recomendações...",
    "Quase pronto, consolidando seu relatório...",
    "Estamos finalizando os últimos detalhes..."
  ];

  if (loading) {
    const msgIndex = Math.min(Math.floor(retries / 5), loadingMessages.length - 1);
    return (
      <div className="fb-loading">
        <div className="fb-loading-inner">
          <div className="fb-loading-icon">
            <Icon name="sparkles" size={40} color="var(--primary)" />
          </div>
          <h3>Gerando seu feedback com IA</h3>
          <p>{loadingMessages[msgIndex]}</p>
          <div className="fb-loading-dots">
            <span /><span /><span />
          </div>
          <p style={{ marginTop: '2rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Tentativa {retries + 1} de 24.
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fb-loading">
        <div className="fb-loading-inner" style={{ padding: '2rem' }}>
          <div style={{ background: 'rgba(255, 82, 82, 0.1)', padding: '2rem', borderRadius: '20px', border: '1px solid rgba(255, 82, 82, 0.2)' }}>
            <Icon name="alert" size={40} color="var(--danger)" />
            <h3 style={{ color: 'var(--danger)', marginTop: '1rem' }}>Processamento em andamento</h3>
            <p style={{ margin: '1rem 0' }}>{error}</p>
            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', marginTop: '2rem' }}>
              <button className="btn-secondary" onClick={onBack}>
                Voltar ao Painel
              </button>
              <button className="btn-primary" onClick={() => { setError(null); setLoading(true); setRetries(0); }}>
                Tentar Agora
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const categoryScores = feedback.category_scores || {};

  return (
    <div className="fb-wrapper fade-in">
      {/* Hero Header */}
      <div className="fb-hero">
        <div className="fb-hero-left">
          <button className="ic-back-btn" onClick={onBack} style={{ marginBottom: '1.5rem' }}>
            <Icon name="arrow" size={18} style={{ transform: 'rotate(180deg)' }} />
          </button>
          <div className="fb-nivel-badge">
            <Icon name="star" size={16} color="var(--primary)" />
            <span>{feedback.nivel}</span>
          </div>
          <h1 className="fb-hero-score">{Math.round(feedback.score_geral)}%</h1>
          <p className="fb-hero-label">Score de Maturidade de TI</p>
        </div>
        <ScoreGauge score={feedback.score_geral} />
      </div>

      {/* Summary */}
      <div className="glass-card fb-section">
        <div className="fb-section-title">
          <Icon name="sparkles" size={20} color="var(--primary)" />
          <h3>Resumo Executivo</h3>
        </div>
        <p className="fb-summary-text">{feedback.overall_summary}</p>
      </div>

      {/* Grid: Strengths + Weaknesses */}
      <div className="fb-grid-2">
        <div className="glass-card fb-section">
          <div className="fb-section-title">
            <Icon name="thumbUp" size={18} color="var(--success)" />
            <h3 style={{ color: 'var(--success)' }}>Pontos Fortes</h3>
          </div>
          <ul className="fb-list">
            {(feedback.strengths || []).map((s, i) => (
              <li key={i} className="fb-list-item strength">
                <Icon name="check" size={14} color="var(--success)" />
                <span>{s}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="glass-card fb-section">
          <div className="fb-section-title">
            <Icon name="thumbDown" size={18} color="var(--warning)" />
            <h3 style={{ color: 'var(--warning)' }}>Oportunidades de Melhoria</h3>
          </div>
          <ul className="fb-list">
            {(feedback.weaknesses || []).map((w, i) => (
              <li key={i} className="fb-list-item weakness">
                <Icon name="alert" size={14} color="var(--warning)" />
                <span>{w}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Category Scores */}
      {Object.keys(categoryScores).length > 0 && (
        <div className="glass-card fb-section">
          <div className="fb-section-title">
            <Icon name="chart" size={18} color="var(--primary)" />
            <h3>Score por Domínio</h3>
          </div>
          <div className="fb-cats">
            {Object.entries(categoryScores).map(([name, score]) => (
              <CategoryBar key={name} name={name} score={score} />
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {feedback.recommendations?.length > 0 && (
        <div className="glass-card fb-section">
          <div className="fb-section-title">
            <Icon name="lightning" size={18} color="var(--warning)" />
            <h3>Recomendações</h3>
          </div>
          <div className="fb-recs-grid">
            {feedback.recommendations.map((rec, i) => (
              <RecommendationCard key={i} rec={rec} index={i} />
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="fb-footer">
        <p>Relatório gerado em {new Date(feedback.generated_at).toLocaleString('pt-BR')}</p>
        <button className="btn-secondary" onClick={onBack}>← Voltar ao Painel</button>
      </div>
    </div>
  );
};

export default FeedbackReport;
