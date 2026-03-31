import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';

import { API_URL, WS_URL } from '../config';

// ─── Ícones ───────────────────────────────────────────────────────────────────
const Icon = ({ name, size = 18, color = 'currentColor' }) => {
  const icons = {
    send: <><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></>,
    bot: <><rect width="18" height="10" x="3" y="11" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4"/><line x1="8" y1="16" x2="8" y2="16"/><line x1="16" y1="16" x2="16" y2="16"/></>,
    user: <><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></>,
    check: <><polyline points="20 6 9 17 4 12"/></>,
    sparkles: <><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/><path d="M5 3v4"/><path d="M19 17v4"/><path d="M3 5h4"/><path d="M17 19h4"/></>,
    arrow: <><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></>,
  };
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24"
      fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      {icons[name]}
    </svg>
  );
};

// ─── Typing Indicator ─────────────────────────────────────────────────────────
const TypingIndicator = () => (
  <div className="ic-message agent">
    <div className="ic-avatar agent"><Icon name="bot" size={16} /></div>
    <div className="ic-bubble agent" style={{ padding: '1rem 1.5rem' }}>
      <div className="ic-dots">
        <span className="ic-dot" />
        <span className="ic-dot" />
        <span className="ic-dot" />
      </div>
    </div>
  </div>
);

// ─── Message Bubble ───────────────────────────────────────────────────────────
const MessageBubble = ({ msg, isNew }) => {
  const isAgent = msg.role === 'agent';
  return (
    <div className={`ic-message ${isAgent ? 'agent' : 'user'} ${isNew ? 'msg-new' : ''}`}>
      {isAgent && (
        <div className="ic-avatar agent">
          <Icon name="bot" size={16} />
        </div>
      )}
      <div className={`ic-bubble ${isAgent ? 'agent' : 'user'}`}>
        <p className="ic-bubble-text">{msg.content}</p>
        <span className="ic-timestamp">
          {new Date(msg.timestamp).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
      {!isAgent && (
        <div className="ic-avatar user">
          <Icon name="user" size={16} />
        </div>
      )}
    </div>
  );
};

// ─── Progress Bar ─────────────────────────────────────────────────────────────
const ProgressBar = ({ asked, total }) => {
  const pct = total > 0 ? Math.min((asked / total) * 100, 100) : 0;
  return (
    <div className="ic-progress-wrap">
      <div className="ic-progress-track">
        <div className="ic-progress-fill" style={{ width: `${pct}%` }} />
      </div>
      <span className="ic-progress-label">{asked}/{total}</span>
    </div>
  );
};

// ─── Main InterviewChat Component ─────────────────────────────────────────────
const InterviewChat = ({ sessionId, onComplete, onBack, readOnly = false }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isFinished, setIsFinished] = useState(false);
  const [progress, setProgress] = useState({ asked: 0, total: 20 });
  const [newMsgIdx, setNewMsgIdx] = useState(null);
  const [loadingHistory, setLoadingHistory] = useState(true);

  const wsRef = useRef(null);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // Carrega histórico inicial
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await axios.get(`${API_URL}/interviews/${sessionId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setMessages(res.data.messages || []);
        setProgress({ asked: res.data.questions_asked, total: res.data.total_questions });
        setIsFinished(!res.data.is_active);
      } catch (err) { console.error(err); }
      finally { setLoadingHistory(false); }
    };
    fetchHistory();
  }, [sessionId]);

  // Conecta WebSocket
  useEffect(() => {
    if (readOnly) {
      setIsConnected(true);
      return;
    }
    const ws = new WebSocket(`${WS_URL}/ws/interview/${sessionId}`);
    wsRef.current = ws;

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);
    ws.onerror = () => setIsConnected(false);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'typing') {
        setIsTyping(true);
      } else if (data.type === 'message') {
        setIsTyping(false);
        const newMsg = {
          id: Date.now(),
          role: 'agent',
          content: data.content,
          timestamp: new Date().toISOString(),
          is_evaluation_question: true,
        };
        setMessages(prev => {
          setNewMsgIdx(prev.length);
          return [...prev, newMsg];
        });
        if (data.questions_asked !== undefined) {
          setProgress({ asked: data.questions_asked, total: data.total_questions });
        }
      } else if (data.type === 'interview_complete') {
        setIsTyping(false);
        setIsFinished(true);
        if (onComplete) onComplete(data.assessment_id);
      } else if (data.type === 'error') {
        setIsTyping(false);
        console.error('WS Error:', data.content);
      }
    };

    return () => ws.close();
  }, [sessionId, onComplete]);

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const sendMessage = useCallback(() => {
    const text = input.trim();
    if (!text || !isConnected || isFinished || isTyping) return;

    const userMsg = {
      id: Date.now(),
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    wsRef.current?.send(JSON.stringify({ message: text }));
    inputRef.current?.focus();
  }, [input, isConnected, isFinished, isTyping]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (loadingHistory) {
    return (
      <div className="ic-wrapper" style={{ justifyContent: 'center', alignItems: 'center' }}>
        <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
          <div className="loader" style={{ margin: '0 auto 1rem' }} />
          Carregando entrevista...
        </div>
      </div>
    );
  }

  return (
    <div className="ic-wrapper">
      {/* Header */}
      <div className="ic-header">
        <div className="ic-header-left">
          <button className="ic-back-btn" onClick={onBack}>
            <Icon name="arrow" size={18} />
          </button>
          <div className="ic-agent-avatar-lg">
            <Icon name="sparkles" size={22} color="#00363d" />
          </div>
          <div className="ic-header-info">
            <p className="ic-agent-name">Agente de Maturidade TI</p>
            <p className="ic-agent-status">
              <span className={`ic-status-dot ${isConnected ? 'online' : 'offline'}`} />
              {readOnly ? 'Histórico da Entrevista' : (isFinished ? 'Entrevista concluída' : isConnected ? 'Conectado' : 'Reconectando...')}
            </p>
          </div>
        </div>
        {progress.total > 0 && (
          <ProgressBar asked={progress.asked} total={progress.total} />
        )}
      </div>

      {/* Messages */}
      <div className="ic-messages">
        {messages.map((msg, idx) => (
          <MessageBubble key={msg.id || idx} msg={msg} isNew={idx === newMsgIdx} />
        ))}
        {isTyping && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Finished Banner */}
      {!readOnly && isFinished && (
        <div className="ic-finished-banner">
          <Icon name="check" size={20} color="var(--success)" />
          <span>Entrevista concluída! Seu feedback está sendo gerado...</span>
        </div>
      )}

      {/* Input Area */}
      {!readOnly && !isFinished && (
        <div className="ic-input-area">
          <div className="ic-input-wrap">
            <textarea
              ref={inputRef}
              className="ic-textarea"
              placeholder="Digite sua resposta... (Enter para enviar, Shift+Enter para nova linha)"
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                e.target.style.height = 'auto';
                e.target.style.height = e.target.scrollHeight + 'px';
              }}
              onKeyDown={handleKeyDown}
              rows={1}
              disabled={!isConnected || isTyping}
            />
            <button
              className="ic-send-btn"
              onClick={sendMessage}
              disabled={!input.trim() || !isConnected || isTyping}
            >
              <Icon name="send" size={18} color={input.trim() && isConnected && !isTyping ? '#00363d' : 'currentColor'} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default InterviewChat;
