import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_URL } from '../config';

// ─── Score Gauge (SVG circular) ───────────────────────────────────────────────
const ScoreGauge = ({ score }) => {
  const r = 70;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color = score >= 80 ? '#00e676' : score >= 60 ? '#00e5ff' : score >= 40 ? '#ffb74d' : '#ff5252';
  return (
    <svg width="180" height="180" viewBox="0 0 180 180" style={{ display: 'block' }}>
      <circle cx="90" cy="90" r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="14" />
      <circle
        cx="90" cy="90" r={r} fill="none"
        stroke={color} strokeWidth="14" strokeLinecap="round"
        strokeDasharray={circ} strokeDashoffset={offset}
        transform="rotate(-90 90 90)"
        style={{ transition: 'stroke-dashoffset 1.4s ease', filter: `drop-shadow(0 0 10px ${color}80)` }}
      />
      <text x="90" y="82" textAnchor="middle" fill={color} fontSize="36" fontWeight="900" fontFamily="Outfit,sans-serif">
        {Math.round(score)}%
      </text>
      <text x="90" y="104" textAnchor="middle" fill="rgba(255,255,255,0.35)" fontSize="11" fontFamily="Outfit,sans-serif">
        Maturidade Geral
      </text>
    </svg>
  );
};

// ─── Bar de progresso ─────────────────────────────────────────────────────────
const ScoreBar = ({ score }) => {
  const [w, setW] = useState(0);
  useEffect(() => { setTimeout(() => setW(score), 80); }, [score]);
  const color = score >= 80 ? '#00e676' : score >= 60 ? '#00e5ff' : score >= 40 ? '#ffb74d' : '#ff5252';
  return (
    <div style={{ background: 'rgba(255,255,255,0.06)', borderRadius: '6px', height: '8px', overflow: 'hidden', flex: 1 }}>
      <div style={{ height: '100%', width: `${w}%`, background: color, borderRadius: '6px', transition: 'width 1s ease', boxShadow: `0 0 8px ${color}60` }} />
    </div>
  );
};

// ─── Severity badge ───────────────────────────────────────────────────────────
const SeverityBadge = ({ severity }) => {
  const cfg = {
    'CRÍTICO': { bg: 'rgba(255,82,82,0.15)', border: 'rgba(255,82,82,0.4)', color: '#ff5252' },
    'ALTO':    { bg: 'rgba(255,152,0,0.15)', border: 'rgba(255,152,0,0.4)',  color: '#ff9800' },
    'MÉDIO':   { bg: 'rgba(255,183,77,0.15)',border: 'rgba(255,183,77,0.4)', color: '#ffb74d' },
    'BAIXO':   { bg: 'rgba(0,230,118,0.12)', border: 'rgba(0,230,118,0.35)', color: '#00e676' },
  };
  const s = cfg[severity] || cfg['BAIXO'];
  return (
    <span style={{ display: 'inline-block', padding: '0.2rem 0.65rem', borderRadius: '6px', fontSize: '0.65rem', fontWeight: '800', letterSpacing: '0.5px', background: s.bg, border: `1px solid ${s.border}`, color: s.color }}>
      {severity}
    </span>
  );
};

// ─── Status KPI badge ─────────────────────────────────────────────────────────
const KpiStatus = ({ status }) => {
  const cfg = {
    'ABAIXO': { color: '#ff5252', label: 'ABAIXO' },
    'OK':     { color: '#00e676', label: 'OK' },
    'ACIMA':  { color: '#00e5ff', label: 'ACIMA' },
  };
  const s = cfg[status] || cfg['OK'];
  return (
    <span style={{ padding: '0.2rem 0.7rem', borderRadius: '6px', fontSize: '0.65rem', fontWeight: '800', background: `${s.color}18`, border: `1px solid ${s.color}40`, color: s.color }}>
      {s.label}
    </span>
  );
};

// ─── Section title ─────────────────────────────────────────────────────────────
const SectionTitle = ({ children, accent = 'var(--primary)' }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: '0.7rem', marginBottom: '1.5rem' }}>
    <div style={{ width: '3px', height: '22px', background: accent, borderRadius: '2px', flexShrink: 0 }} />
    <h3 style={{ fontSize: '1rem', fontWeight: '800', letterSpacing: '-0.3px', color: 'var(--text-main)' }}>{children}</h3>
  </div>
);

// ─── Main Report component ────────────────────────────────────────────────────
const Report = ({ assessmentId, onBack }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await axios.get(`${API_URL}/assessments/${assessmentId}/report`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setData(res.data);
      } catch (err) {
        setError(err.response?.data?.detail || 'Erro ao carregar relatório.');
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [assessmentId]);

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', flexDirection: 'column', gap: '1rem' }}>
      <div className="loader" style={{ width: '40px', height: '40px', borderWidth: '3px' }} />
      <p style={{ color: 'var(--text-muted)' }}>Carregando relatório...</p>
    </div>
  );

  if (error) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', flexDirection: 'column', gap: '1.5rem' }}>
      <p style={{ color: 'var(--danger)' }}>{error}</p>
      <button className="btn-secondary" onClick={onBack}>← Voltar</button>
    </div>
  );

  const {
    company, evaluator, score_geral, nivel, nivel_numerico, nivel_descricao,
    overall_summary, strengths, weaknesses, recommendations,
    category_scores_enriched, findings, critical_findings_count,
    action_plan_90d, framework_diagnoses, kpi_indicators, generated_at,
  } = data;

  const scoreColor = score_geral >= 80 ? '#00e676' : score_geral >= 60 ? '#00e5ff' : score_geral >= 40 ? '#ffb74d' : '#ff5252';

  return (
    <div className="rpt-root fade-in">
      {/* Print styles */}
      <style>{`
        @media print {
          .rpt-actions { display: none !important; }
          .rpt-root { background: #fff !important; color: #111 !important; padding: 0 !important; }
          .rpt-header { background: #0a2a3a !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
          .glass-card, .rpt-card { box-shadow: none !important; border: 1px solid #ddd !important; background: #fff !important; }
          body { background: #fff !important; }
        }
      `}</style>

      {/* ─── Action Bar ────────────────────────────────────────────────────── */}
      <div className="rpt-actions no-print">
        <button className="btn-secondary" onClick={onBack} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
          ← Voltar
        </button>
        <button className="btn-primary" onClick={() => window.print()} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#00363d" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
          Imprimir / Exportar PDF
        </button>
        <a
          href={`${API_URL}/assessments/${assessmentId}/report/pdf?token=${localStorage.getItem('token')}`}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-primary"
          style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', textDecoration: 'none' }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#00363d" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Baixar PDF
        </a>
      </div>

      <div className="rpt-container">

        {/* ══════════════════════════════════════════════════════════════════
            SEÇÃO 1 — CABEÇALHO
        ══════════════════════════════════════════════════════════════════ */}
        <div className="rpt-header glass-card">
          <div className="rpt-header-meta">
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', marginBottom: '0.5rem' }}>
                <div style={{ width: '36px', height: '36px', background: 'var(--primary)', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#00363d', fontWeight: '900', fontSize: '1rem' }}>A</div>
                <span style={{ fontSize: '0.7rem', fontWeight: '800', letterSpacing: '2px', color: 'var(--text-muted)' }}>AVALIA.AI — DIAGNÓSTICO DE MATURIDADE DE TI</span>
              </div>
              <h1 className="rpt-company-name">{company.name}</h1>
              <div className="rpt-meta-pills">
                {company.sector && <span className="rpt-pill">{company.sector}</span>}
                {company.employee_count && <span className="rpt-pill">{company.employee_count} funcionários</span>}
                {company.it_model && <span className="rpt-pill">TI {company.it_model}</span>}
                {company.regulations?.map(r => <span key={r} className="rpt-pill rpt-pill-accent">{r}</span>)}
              </div>
              <div style={{ marginTop: '1rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                {evaluator && <span>Avaliador: <strong style={{ color: 'var(--text-main)' }}>{evaluator.name}</strong> &nbsp;·&nbsp; </span>}
                <span>Gerado em {new Date(generated_at).toLocaleString('pt-BR')}</span>
              </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem', flexShrink: 0 }}>
              <ScoreGauge score={score_geral} />
              <div style={{ textAlign: 'center' }}>
                <span className="rpt-nivel-badge" style={{ background: `${scoreColor}18`, border: `1px solid ${scoreColor}40`, color: scoreColor }}>
                  Nível {nivel_numerico}/5 — {nivel}
                </span>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem', maxWidth: '220px', textAlign: 'center' }}>{nivel_descricao}</p>
              </div>
            </div>
          </div>

          {/* Badge strip */}
          <div className="rpt-badge-strip">
            <div className="rpt-badge-item">
              <span className="rpt-badge-value" style={{ color: 'var(--primary)' }}>{category_scores_enriched?.length || 0}</span>
              <span className="rpt-badge-label">Domínios Avaliados</span>
            </div>
            <div className="rpt-badge-sep" />
            <div className="rpt-badge-item">
              <span className="rpt-badge-value" style={{ color: critical_findings_count > 0 ? '#ff5252' : '#00e676' }}>{critical_findings_count}</span>
              <span className="rpt-badge-label">Achados Críticos</span>
            </div>
            <div className="rpt-badge-sep" />
            <div className="rpt-badge-item">
              <span className="rpt-badge-value" style={{ color: 'var(--warning)' }}>{findings?.length || 0}</span>
              <span className="rpt-badge-label">Total de Achados</span>
            </div>
            <div className="rpt-badge-sep" />
            <div className="rpt-badge-item">
              <span className="rpt-badge-value" style={{ color: 'var(--success)' }}>{kpi_indicators?.length || 0}</span>
              <span className="rpt-badge-label">Indicadores KPI</span>
            </div>
          </div>

          {/* Resumo executivo */}
          <div style={{ marginTop: '1.5rem', padding: '1.2rem 1.5rem', background: 'rgba(0,229,255,0.04)', borderRadius: '12px', borderLeft: '3px solid var(--primary)' }}>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', lineHeight: '1.7' }}>{overall_summary}</p>
          </div>
        </div>

        {/* ══════════════════════════════════════════════════════════════════
            SEÇÃO 2 — SCORES POR CATEGORIA
        ══════════════════════════════════════════════════════════════════ */}
        {category_scores_enriched?.length > 0 && (
          <div className="glass-card rpt-section">
            <SectionTitle>Scores por Domínio</SectionTitle>
            <div style={{ display: 'grid', gap: '1rem' }}>
              {category_scores_enriched.map(cat => {
                const c = cat.score >= 80 ? '#00e676' : cat.score >= 60 ? '#00e5ff' : cat.score >= 40 ? '#ffb74d' : '#ff5252';
                return (
                  <div key={cat.name} style={{ display: 'grid', gridTemplateColumns: '1fr auto 160px auto', alignItems: 'center', gap: '1rem' }}>
                    <div>
                      <p style={{ fontWeight: '600', fontSize: '0.9rem' }}>{cat.name}</p>
                      <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>{cat.framework}</p>
                    </div>
                    <span style={{ fontSize: '1rem', fontWeight: '800', color: c, minWidth: '44px', textAlign: 'right' }}>{Math.round(cat.score)}%</span>
                    <ScoreBar score={cat.score} />
                    <span style={{ fontSize: '0.7rem', padding: '0.2rem 0.6rem', borderRadius: '5px', background: `${c}15`, color: c, fontWeight: '700', whiteSpace: 'nowrap' }}>
                      {cat.score >= 80 ? 'EXCELENTE' : cat.score >= 60 ? 'BOM' : cat.score >= 40 ? 'REGULAR' : 'CRÍTICO'}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ══════════════════════════════════════════════════════════════════
            SEÇÃO 3 — INDICADORES OPERACIONAIS (KPIs)
        ══════════════════════════════════════════════════════════════════ */}
        {kpi_indicators?.length > 0 && (
          <div className="glass-card rpt-section">
            <SectionTitle accent="var(--warning)">Indicadores Operacionais</SectionTitle>
            <div style={{ overflowX: 'auto' }}>
              <table className="rpt-table">
                <thead>
                  <tr>
                    <th>Indicador</th>
                    <th>Valor Atual</th>
                    <th>Benchmark</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {kpi_indicators.map((kpi, i) => (
                    <tr key={i}>
                      <td style={{ fontWeight: '600' }}>{kpi.name}</td>
                      <td>{kpi.current}</td>
                      <td style={{ color: 'var(--text-muted)' }}>{kpi.benchmark}</td>
                      <td><KpiStatus status={kpi.status} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ══════════════════════════════════════════════════════════════════
            SEÇÃO 4 — ACHADOS E VULNERABILIDADES
        ══════════════════════════════════════════════════════════════════ */}
        {findings?.length > 0 && (
          <div className="glass-card rpt-section">
            <SectionTitle accent="var(--danger)">Achados e Vulnerabilidades</SectionTitle>
            <div style={{ display: 'grid', gap: '0.8rem' }}>
              {findings.map((f, i) => (
                <div key={i} className="rpt-card" style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem' }}>
                  <SeverityBadge severity={f.severity} />
                  <p style={{ fontSize: '0.9rem', lineHeight: '1.6', paddingTop: '0.05rem' }}>{f.description}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ══════════════════════════════════════════════════════════════════
            SEÇÃO 5 — PLANO DE AÇÃO 90 DIAS
        ══════════════════════════════════════════════════════════════════ */}
        {action_plan_90d && Object.keys(action_plan_90d).length > 0 && (
          <div className="glass-card rpt-section">
            <SectionTitle accent="var(--success)">Plano de Ação — 90 Dias</SectionTitle>
            <div className="rpt-plan-grid">
              {[
                { key: 'fase_0_15',  label: '0 – 15 dias',  color: '#ff5252', desc: 'Ações imediatas e críticas' },
                { key: 'fase_15_45', label: '15 – 45 dias', color: '#ffb74d', desc: 'Implementações prioritárias' },
                { key: 'fase_45_90', label: '45 – 90 dias', color: '#00e676', desc: 'Consolidação e melhoria' },
              ].map(({ key, label, color, desc }) => (
                <div key={key} className="rpt-plan-col">
                  <div style={{ padding: '0.6rem 1rem', background: `${color}15`, borderRadius: '10px 10px 0 0', borderBottom: `2px solid ${color}40`, marginBottom: '1rem' }}>
                    <p style={{ fontSize: '0.85rem', fontWeight: '800', color }}>{label}</p>
                    <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{desc}</p>
                  </div>
                  <ul style={{ listStyle: 'none', padding: '0 0.5rem', display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                    {(action_plan_90d[key] || []).map((item, i) => (
                      <li key={i} style={{ display: 'flex', gap: '0.6rem', fontSize: '0.85rem', alignItems: 'flex-start' }}>
                        <span style={{ color, fontWeight: '900', lineHeight: '1.5', flexShrink: 0 }}>›</span>
                        <span style={{ color: 'var(--text-muted)' }}>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ══════════════════════════════════════════════════════════════════
            SEÇÃO 6 — DIAGNÓSTICO POR FRAMEWORK
        ══════════════════════════════════════════════════════════════════ */}
        {framework_diagnoses?.length > 0 && (
          <div className="glass-card rpt-section">
            <SectionTitle>Diagnóstico Consolidado por Framework</SectionTitle>
            <div className="rpt-fw-grid">
              {framework_diagnoses.map((fw, i) => {
                const lvl = fw.level_num ?? 0;
                const fwColor = lvl >= 4 ? '#00e676' : lvl >= 3 ? '#00e5ff' : lvl >= 2 ? '#ffb74d' : '#ff5252';
                return (
                  <div key={i} className="rpt-card rpt-fw-card">
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.8rem' }}>
                      <p style={{ fontWeight: '800', fontSize: '0.95rem' }}>{fw.framework}</p>
                      <span style={{ fontSize: '0.65rem', padding: '0.2rem 0.6rem', borderRadius: '5px', background: `${fwColor}18`, color: fwColor, fontWeight: '800', border: `1px solid ${fwColor}35` }}>
                        {fw.level}
                      </span>
                    </div>
                    {/* Level progress dots */}
                    <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '0.8rem' }}>
                      {[0,1,2,3,4,5].map(n => (
                        <div key={n} style={{ flex: 1, height: '4px', borderRadius: '2px', background: n <= lvl ? fwColor : 'rgba(255,255,255,0.08)', transition: 'background 0.3s' }} />
                      ))}
                    </div>
                    <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: '1.6' }}>{fw.description}</p>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ══════════════════════════════════════════════════════════════════
            PONTOS FORTES + OPORTUNIDADES + RECOMENDAÇÕES
        ══════════════════════════════════════════════════════════════════ */}
        <div className="rpt-grid-2">
          {strengths?.length > 0 && (
            <div className="glass-card rpt-section">
              <SectionTitle accent="var(--success)">Pontos Fortes</SectionTitle>
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                {strengths.map((s, i) => (
                  <li key={i} style={{ display: 'flex', gap: '0.6rem', fontSize: '0.88rem', alignItems: 'flex-start' }}>
                    <span style={{ color: '#00e676', fontWeight: '900', flexShrink: 0, lineHeight: '1.6' }}>✓</span>
                    <span style={{ color: 'var(--text-muted)' }}>{s}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {weaknesses?.length > 0 && (
            <div className="glass-card rpt-section">
              <SectionTitle accent="var(--warning)">Oportunidades de Melhoria</SectionTitle>
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                {weaknesses.map((w, i) => (
                  <li key={i} style={{ display: 'flex', gap: '0.6rem', fontSize: '0.88rem', alignItems: 'flex-start' }}>
                    <span style={{ color: '#ffb74d', fontWeight: '900', flexShrink: 0, lineHeight: '1.6' }}>!</span>
                    <span style={{ color: 'var(--text-muted)' }}>{w}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {recommendations?.length > 0 && (
          <div className="glass-card rpt-section">
            <SectionTitle accent="var(--warning)">Recomendações Estratégicas</SectionTitle>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '1rem' }}>
              {recommendations.map((rec, i) => {
                const isObj = typeof rec === 'object' && rec !== null;
                const title = isObj ? (rec.title || rec.action || rec.area || `Recomendação ${i+1}`) : `Recomendação ${i+1}`;
                const desc  = isObj ? (rec.description || rec.action || '') : String(rec);
                const prio  = isObj ? (rec.priority || '').toLowerCase() : '';
                const prioColor = prio === 'alta' || prio === 'alto' ? '#ff5252' : prio === 'média' || prio === 'medio' ? '#ffb74d' : '#00e5ff';
                return (
                  <div key={i} className="rpt-card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {prio && <span style={{ fontSize: '0.65rem', fontWeight: '800', color: prioColor, letterSpacing: '0.5px' }}>PRIORIDADE {prio.toUpperCase()}</span>}
                    <p style={{ fontWeight: '700', fontSize: '0.88rem' }}>{title}</p>
                    {desc && desc !== title && <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>{desc}</p>}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Footer */}
        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)', fontSize: '0.78rem', borderTop: '1px solid var(--glass-border)', marginTop: '1rem' }}>
          Relatório gerado automaticamente pela plataforma Avalia.AI · Avaliação #{assessmentId} · {new Date(generated_at).toLocaleString('pt-BR')}
        </div>
      </div>
    </div>
  );
};

export default Report;
