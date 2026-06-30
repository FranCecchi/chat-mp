import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';

interface User {
  userId: string;
  username: string;
}

interface Classification {
  movimiento: string;
  logro: string;
  justificacion: string;
}

interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  state?: string;
  classification?: Classification | null;
}

interface Diagnosis {
  id: number;
  student_name: string;
  conversation_id: string;
  movimiento: string | null;
  logro: string | null;
  justificacion: string | null;
  activity_context: string | null;
  created_at: string;
  conversation_history?: string | null;
  feedback_status?: string | null;
  feedback_corrected_movement?: string | null;
}

const BACKEND_URL = import.meta.env.PROD ? 'https://api.chatmp.xyz' : 'http://localhost:8000';

const THINKING_MOVES = [
  {
    name: "Observar con atención y describir",
    desc: "Hacer notar las partes y características de un fenómeno, describiéndolo en detalle y en su totalidad.",
    logroEsperado: "La actividad guía a los estudiantes a observar con detalle y precisión, solicitando la descripción sistemática de aspectos específicos de manera detallada y completa."
  },
  {
    name: "Explicar y dar sentido",
    desc: "Proponer significados o interpretaciones que den cuenta de un fenómeno o hecho a partir del análisis de sus características, funcionamiento o relaciones, integrando información relevante.",
    logroEsperado: "La actividad orienta explícitamente a la construcción de explicaciones o interpretaciones propias que integran distintos aspectos y evidencian una comprensión profunda."
  },
  {
    name: "Justificar con evidencia",
    desc: "Fundamentar afirmaciones o explicaciones mediante datos, hechos o referencias que las sostengan.",
    logroEsperado: "La actividad requiere que los estudiantes fundamenten sus ideas mediante el uso de dos o más evidencias pertinentes, promoviendo su reflexión."
  },
  {
    name: "Relacionar ideas y conceptos",
    desc: "Vincular conocimientos nuevos con saberes ya conocidos (experiencias previas u otros contextos), así como aplicar lo aprendido a nuevas situaciones.",
    logroEsperado: "La actividad exige de manera explícita que los estudiantes establezcan conexiones significativas entre ideas o conceptos nuevos y saberes previos, o que apliquen lo aprendido a diferentes situaciones."
  },
  {
    name: "Considerar otras perspectivas",
    desc: "Reconocer la existencia de otras miradas o intereses implicados en un fenómeno, considerando la diversidad y la complejidad del saber.",
    logroEsperado: "La actividad invita a explorar y comparar diferentes perspectivas, promoviendo un análisis comparativo, crítico y abierto."
  },
  {
    name: "Identificar ideas claves y llegar a conclusiones",
    desc: "Sintetizar los aspectos fundamentales de una idea o fenómeno, distinguiéndolo de los detalles secundarios, para establecer afirmaciones o conclusiones derivadas.",
    logroEsperado: "La actividad guía a los estudiantes a identificar las ideas claves y llegar a conclusiones complejas y bien fundamentadas que evidencian su comprensión."
  },
  {
    name: "Formular preguntas propias",
    desc: "Formular interrogantes que promuevan la indagación, la curiosidad y la búsqueda de sentido.",
    logroEsperado: "La actividad fomenta de manera explícita la formulación de preguntas relevantes y desafiantes que motivan a los estudiantes a investigar y profundizar en el tema."
  },
  {
    name: "Explorar la complejidad del tema",
    desc: "Profundizar en un fenómeno identificando aspectos menos evidentes, relaciones y posibles tensiones, evitando interpretaciones simplificadas.",
    logroEsperado: "La actividad orienta explícitamente al análisis de múltiples factores y sus relaciones, promoviendo una exploración profunda y articulada."
  },
  {
    name: "Pensar metacognitivamente",
    desc: "Reflexionar sobre el propio pensamiento y los procesos implicados en la comprensión.",
    logroEsperado: "La actividad promueve de manera explícita la reflexión sobre su propio proceso de aprendizaje, permitiendo planificar, monitorear y evaluar sus estrategias."
  }
];

const LOGRO_COLORS: Record<string, string> = {
  'logro-esperado': '#22c55e',
  'logro-parcial': '#f59e0b',
  'logro-no-conseguido': '#94a3b8',
  'ninguno': '#94a3b8',
};

function getLogro(logro: string | null): string {
  if (!logro) return 'ninguno';
  return logro.toLowerCase().replace(/ /g, '-');
}

// ── Teacher Dashboard ──────────────────────────────────────────────────────

function TeacherDashboard({ password, onLogout }: { password: string; onLogout: () => void }) {
  const [diagnoses, setDiagnoses] = useState<Diagnosis[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [showTranscript, setShowTranscript] = useState<Record<number, boolean>>({});

  const [correctingId, setCorrectingId] = useState<number | null>(null);
  const [selectedMovement, setSelectedMovement] = useState<string>('Observar con atención y describir');
  const [submittingFeedback, setSubmittingFeedback] = useState<Record<number, boolean>>({});

  const toggleTranscript = (id: number) => {
    setShowTranscript((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const parseHistory = (rawJson: string | null) => {
    if (!rawJson) return [];
    try {
      return JSON.parse(rawJson);
    } catch (e) {
      console.error('Failed to parse conversation history', e);
      return [];
    }
  };

  const handleFeedback = async (diagnosisId: number, isCorrect: boolean, movement?: string) => {
    setSubmittingFeedback(prev => ({ ...prev, [diagnosisId]: true }));
    try {
      const res = await fetch(`${BACKEND_URL}/teacher/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Teacher-Password': password,
        },
        body: JSON.stringify({
          diagnosis_id: diagnosisId,
          is_correct: isCorrect,
          correct_movement: movement || null,
        }),
      });
      if (!res.ok) throw new Error('Failed to submit feedback');
      const data = await res.json();
      
      setDiagnoses(prev =>
        prev.map(d =>
          d.id === diagnosisId
            ? {
                ...d,
                feedback_status: data.feedback_status,
                feedback_corrected_movement: movement || null,
              }
            : d
        )
      );
      setCorrectingId(null);
    } catch (e) {
      alert('Error al enviar la retroalimentación.');
    } finally {
      setSubmittingFeedback(prev => ({ ...prev, [diagnosisId]: false }));
    }
  };

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/teacher/history`, {
          headers: { 'X-Teacher-Password': password },
        });
        if (res.status === 401) {
          setError('Contraseña incorrecta.');
          return;
        }
        if (!res.ok) throw new Error('Error del servidor');
        setDiagnoses(await res.json());
      } catch {
        setError('No se pudo conectar con el servidor.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [password]);

  // Stats
  const total = diagnoses.length;
  const movCounts: Record<string, number> = {};
  const lograCounts: Record<string, number> = { 'logro-esperado': 0, 'logro-parcial': 0, 'logro-no-conseguido': 0, 'ninguno': 0 };

  diagnoses.forEach((d) => {
    const mov = d.movimiento || 'Ninguno';
    movCounts[mov] = (movCounts[mov] || 0) + 1;
    const key = getLogro(d.logro);
    lograCounts[key] = (lograCounts[key] || 0) + 1;
  });

  const topMov = Object.entries(movCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || '—';
  const esperadoPct = total > 0 ? Math.round((lograCounts['logro-esperado'] / total) * 100) : 0;

  function formatDate(raw: string) {
    const d = new Date(raw + 'Z');
    return d.toLocaleString('es-AR', { dateStyle: 'short', timeStyle: 'short' });
  }

  return (
    <div className="teacher-dashboard">
      <header className="teacher-header">
        <div className="logo-section">
          <div className="logo-dot" />
          <span className="logo-text">Panel Docente</span>
        </div>
        <button onClick={onLogout} className="secondary-btn">Salir</button>
      </header>

      <div className="teacher-body">
        {loading && <p className="teacher-status">Cargando diagnósticos…</p>}
        {error && <p className="teacher-status teacher-error">{error}</p>}

        {!loading && !error && (
          <>
            {/* Stats row */}
            <div className="stats-row">
              <div className="stat-card">
                <span className="stat-value">{total}</span>
                <span className="stat-label">Actividades analizadas</span>
              </div>
              <div className="stat-card">
                <span className="stat-value stat-small">{total > 0 ? topMov : '—'}</span>
                <span className="stat-label">Movimiento más frecuente</span>
              </div>
              <div className="stat-card">
                <span className="stat-value" style={{ color: '#22c55e' }}>{esperadoPct}%</span>
                <span className="stat-label">Logro esperado</span>
              </div>
            </div>

            {/* Distribution bar */}
            {total > 0 && (
              <div className="distrib-section">
                <h3 className="distrib-title">Distribución de Movimientos</h3>
                <div className="distrib-bars">
                  {Object.entries(movCounts).sort((a, b) => b[1] - a[1]).map(([mov, count]) => (
                    <div key={mov} className="distrib-row">
                      <span className="distrib-label">{mov}</span>
                      <div className="distrib-track">
                        <div
                          className="distrib-fill"
                          style={{ width: `${Math.round((count / total) * 100)}%` }}
                        />
                      </div>
                      <span className="distrib-count">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Diagnosis list */}
            <div className="diagnoses-list">
              <h3 className="distrib-title">Historial de Diagnósticos</h3>
              {diagnoses.length === 0 && (
                <p className="teacher-status">Todavía no hay diagnósticos registrados.</p>
              )}
              {diagnoses.map((d) => {
                const logroKey = getLogro(d.logro);
                const color = LOGRO_COLORS[logroKey] || '#94a3b8';
                const isOpen = expandedId === d.id;
                return (
                  <div key={d.id} className="diagnosis-row">
                    <div
                      className="diagnosis-summary"
                      onClick={() => setExpandedId(isOpen ? null : d.id)}
                    >
                      <div className="diagnosis-meta">
                        <span className="diagnosis-student">{d.student_name}</span>
                        <span className="diagnosis-date">{formatDate(d.created_at)}</span>
                      </div>
                      <div className="diagnosis-badges">
                        <span className="diagnosis-mov">{d.movimiento || 'Ninguno'}</span>
                        <span className="diagnosis-logro" style={{ color, borderColor: color }}>
                          {d.logro || 'Sin logro'}
                        </span>
                        <span className="diagnosis-expand">{isOpen ? '▲' : '▼'}</span>
                      </div>
                    </div>
                    {isOpen && (
                      <div className="diagnosis-detail">
                        {d.activity_context && (
                          <p><strong>Actividad descrita:</strong> {d.activity_context}</p>
                        )}
                        {d.justificacion && (
                          <p><strong>Justificación:</strong> {d.justificacion}</p>
                        )}
                        
                        {d.conversation_history ? (
                          <div className="transcript-section">
                            <button
                              type="button"
                              className="secondary-btn view-chat-btn"
                              onClick={(e) => {
                                e.stopPropagation();
                                toggleTranscript(d.id);
                              }}
                            >
                              {showTranscript[d.id] ? "Ocultar chat completo" : "Ver chat completo"}
                            </button>
                            
                            {showTranscript[d.id] && (
                              <div className="chat-transcript">
                                {parseHistory(d.conversation_history).map((msg: any, idx: number) => (
                                  <div key={idx} className={`transcript-bubble ${msg.role}`}>
                                    <span className="bubble-role">{msg.role === 'user' ? 'Alumno' : 'Asistente'}</span>
                                    <p className="bubble-text">{msg.content}</p>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        ) : (
                          <p className="no-transcript-label"><em>Chat no disponible para este diagnóstico.</em></p>
                        )}

                        {/* Bucle de Feedback de Diagnóstico */}
                        <div className="feedback-container">
                          <strong>¿Esta clasificación es correcta?</strong>
                          
                          {d.feedback_status ? (
                            <div className="feedback-result-badge">
                              {d.feedback_status === 'correct' ? (
                                <span className="feedback-badge success">👍 Clasificación verificada</span>
                              ) : (
                                <span className="feedback-badge error">
                                  👎 Clasificación corregida (Movimiento correcto: <strong>{d.feedback_corrected_movement}</strong>)
                                </span>
                              )}
                            </div>
                          ) : correctingId === d.id ? (
                            <div className="feedback-correction-form">
                              <label htmlFor={`correct-mov-select-${d.id}`} className="feedback-select-label">Elegí el movimiento correcto:</label>
                              <div className="feedback-form-row">
                                <select
                                  id={`correct-mov-select-${d.id}`}
                                  className="text-input feedback-select"
                                  value={selectedMovement}
                                  onChange={(e) => setSelectedMovement(e.target.value)}
                                  disabled={submittingFeedback[d.id]}
                                >
                                  {THINKING_MOVES.map(m => (
                                    <option key={m.name} value={m.name}>{m.name}</option>
                                  ))}
                                  <option value="Ninguno">Ninguno</option>
                                </select>
                                <button
                                  type="button"
                                  className="primary-btn feedback-save-btn"
                                  onClick={() => handleFeedback(d.id, false, selectedMovement)}
                                  disabled={submittingFeedback[d.id]}
                                >
                                  {submittingFeedback[d.id] ? 'Guardando...' : 'Confirmar'}
                                </button>
                                <button
                                  type="button"
                                  className="secondary-btn feedback-cancel-btn"
                                  onClick={() => setCorrectingId(null)}
                                  disabled={submittingFeedback[d.id]}
                                >
                                  Cancelar
                                </button>
                              </div>
                            </div>
                          ) : (
                            <div className="feedback-buttons-row">
                              <button
                                type="button"
                                className="feedback-action-btn thumbs-up"
                                onClick={() => handleFeedback(d.id, true)}
                                disabled={submittingFeedback[d.id]}
                                title="Clasificación correcta"
                              >
                                👍 Sí, es correcta
                              </button>
                              <button
                                type="button"
                                className="feedback-action-btn thumbs-down"
                                onClick={() => {
                                  setCorrectingId(d.id);
                                  setSelectedMovement(d.movimiento || 'Observar con atención y describir');
                                }}
                                disabled={submittingFeedback[d.id]}
                                title="Corregir clasificación"
                              >
                                👎 No, corregir
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ── Main App ───────────────────────────────────────────────────────────────

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [usernameInput, setUsernameInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);

  // Sidebar states
  const [isSidebarOpen, setIsSidebarOpen] = useState(() => window.innerWidth > 768);
  const [expandedMove, setExpandedMove] = useState<string | null>(null);

  // Login mode: 'student' | 'teacher'
  const [loginMode, setLoginMode] = useState<'student' | 'teacher'>('student');
  const [teacherPasswordInput, setTeacherPasswordInput] = useState('');
  const [teacherToken, setTeacherToken] = useState<string | null>(
    () => sessionStorage.getItem('teacher_token')
  );

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load user session + persisted chat on mount
  useEffect(() => {
    const savedUser = localStorage.getItem('chat_mp_user');
    if (!savedUser) return;
    try {
      const parsedUser: User = JSON.parse(savedUser);
      setUser(parsedUser);

      const savedMessages = localStorage.getItem(`chat_mp_messages_${parsedUser.userId}`);
      if (savedMessages) setMessages(JSON.parse(savedMessages));

      const savedConvId = localStorage.getItem(`chat_mp_conv_${parsedUser.userId}`);
      if (savedConvId) setConversationId(savedConvId);
    } catch (e) {
      localStorage.removeItem('chat_mp_user');
    }
  }, []);

  // Persist messages whenever they change
  useEffect(() => {
    if (user && messages.length > 0) {
      localStorage.setItem(`chat_mp_messages_${user.userId}`, JSON.stringify(messages));
    }
  }, [messages, user]);

  // Persist conversationId whenever it changes
  useEffect(() => {
    if (user && conversationId) {
      localStorage.setItem(`chat_mp_conv_${user.userId}`, conversationId);
    }
  }, [conversationId, user]);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleTeacherLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (!teacherPasswordInput.trim()) return;
    sessionStorage.setItem('teacher_token', teacherPasswordInput.trim());
    setTeacherToken(teacherPasswordInput.trim());
  };

  const handleTeacherLogout = () => {
    sessionStorage.removeItem('teacher_token');
    setTeacherToken(null);
    setTeacherPasswordInput('');
    setLoginMode('student');
  };

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (!usernameInput.trim()) return;

    const userId = 'usr_' + Math.random().toString(36).substring(2, 11);
    const newUser: User = { userId, username: usernameInput.trim() };
    const welcome: Message = {
      id: 'welcome',
      sender: 'assistant',
      text: `¡Hola, ${newUser.username}! Soy tu asistente pedagógico. Contame qué hicieron hoy en clase para que podamos analizar qué movimientos de pensamiento promovieron.`,
      state: 'CHATTING',
    };

    localStorage.setItem('chat_mp_user', JSON.stringify(newUser));
    localStorage.setItem(`chat_mp_messages_${newUser.userId}`, JSON.stringify([welcome]));
    setUser(newUser);
    setMessages([welcome]);
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user || !inputText.trim() || isLoading) return;

    const userText = inputText.trim();
    const messageId = 'msg_' + Date.now();

    const userMsg: Message = { id: messageId, sender: 'user', text: userText };

    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setIsLoading(true);

    try {
      const response = await fetch(`${BACKEND_URL}/chat/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: user.userId,
          username: user.username,
          message: userText,
          conversation_id: conversationId,
        }),
      });

      if (!response.ok) throw new Error('API server returned error');

      const data = await response.json();

      if (data.conversation_id) setConversationId(data.conversation_id);

      const assistantMsg: Message = {
        id: 'reply_' + Date.now(),
        sender: 'assistant',
        text: data.reply,
        state: data.state,
        classification: data.classification,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: 'err_' + Date.now(),
          sender: 'assistant',
          text: 'Lo siento, no pude comunicarme con el servidor. Por favor, asegurate de que el backend esté en ejecución.',
          state: 'ERROR',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = async () => {
    if (!user) return;
    setIsLoading(true);
    try {
      await fetch(`${BACKEND_URL}/chat/reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: user.userId }),
      });
    } catch (e) {
      console.error('Failed to reset conversation in backend', e);
    }

    const resetMsg: Message = {
      id: 'welcome_' + Date.now(),
      sender: 'assistant',
      text: `Memoria reiniciada. Contame de nuevo, ¿qué hicieron hoy en clase?`,
      state: 'CHATTING',
    };
    setMessages([resetMsg]);
    setConversationId(null);
    setIsLoading(false);

    localStorage.setItem(`chat_mp_messages_${user.userId}`, JSON.stringify([resetMsg]));
    localStorage.removeItem(`chat_mp_conv_${user.userId}`);
  };

  const handleLogout = () => {
    if (user) {
      localStorage.removeItem(`chat_mp_messages_${user.userId}`);
      localStorage.removeItem(`chat_mp_conv_${user.userId}`);
    }
    localStorage.removeItem('chat_mp_user');
    setUser(null);
    setMessages([]);
    setConversationId(null);
  };

  // ── Teacher mode ──────────────────────────────────────────────────────────
  if (teacherToken) {
    return <TeacherDashboard password={teacherToken} onLogout={handleTeacherLogout} />;
  }

  // ── Auth screen ───────────────────────────────────────────────────────────
  if (!user) {
    return (
      <div className="auth-container">
        <div className="auth-logo">
          <div className="auth-logo-mark" />
          <span className="auth-title">Chat Movimientos de Pensamiento</span>
        </div>

        {/* Role toggle */}
        <div className="auth-role-toggle">
          <button
            type="button"
            className={`role-btn ${loginMode === 'student' ? 'active' : ''}`}
            onClick={() => setLoginMode('student')}
          >
            Soy alumno
          </button>
          <button
            type="button"
            className={`role-btn ${loginMode === 'teacher' ? 'active' : ''}`}
            onClick={() => setLoginMode('teacher')}
          >
            Soy docente
          </button>
        </div>

        {loginMode === 'student' ? (
          <>
            <p className="auth-subtitle">
              Asistente pedagógico para identificar<br />movimientos de pensamiento en clase.
            </p>
            <form onSubmit={handleLogin}>
              <div className="input-group">
                <label className="input-label" htmlFor="username">Tu nombre</label>
                <input
                  id="username"
                  type="text"
                  className="text-input"
                  placeholder="Ej: Clara Gómez"
                  value={usernameInput}
                  onChange={(e) => setUsernameInput(e.target.value)}
                  required
                  autoFocus
                />
              </div>
              <button type="submit" className="primary-btn">Comenzar sesión</button>
            </form>
          </>
        ) : (
          <>
            <p className="auth-subtitle">
              Ingresá la contraseña del panel docente.
            </p>
            <form onSubmit={handleTeacherLogin}>
              <div className="input-group">
                <label className="input-label" htmlFor="teacher-pwd">Contraseña</label>
                <input
                  id="teacher-pwd"
                  type="password"
                  className="text-input"
                  placeholder="••••••••"
                  value={teacherPasswordInput}
                  onChange={(e) => setTeacherPasswordInput(e.target.value)}
                  required
                  autoFocus
                />
              </div>
              <button type="submit" className="primary-btn">Entrar al panel</button>
            </form>
          </>
        )}
      </div>
    );
  }

  // ── Find the last classification detected in the thread, if any ───────────
  const latestClassification = [...messages]
    .reverse()
    .find((m) => m.classification)?.classification;

  const currentState = [...messages].reverse().find((m) => m.state)?.state || 'CHATTING';

  // ── Chat view ─────────────────────────────────────────────────────────────
  return (
    <div className="chat-workspace">
      <header className="chat-header">
        <div className="logo-section">
          <div className="logo-dot" />
          <span className="logo-text">Chat Movimientos de Pensamiento</span>
          {currentState === 'COMPLETED' ? (
            <span className="status-badge completed">Análisis Finalizado</span>
          ) : (
            <span className="status-badge chatting">Indagando Actividad</span>
          )}
        </div>
        <div className="user-controls">
          <span className="user-tag">@{user.username}</span>
          <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="secondary-btn toggle-sidebar-btn">
            {isSidebarOpen ? 'Ocultar Rúbricas' : 'Ver Rúbricas'}
          </button>
          <button onClick={handleReset} className="secondary-btn" title="Reiniciar chat">
            Reiniciar
          </button>
          <button onClick={handleLogout} className="secondary-btn" title="Salir">
            Cerrar Sesión
          </button>
        </div>
      </header>

      <div className="chat-layout-body">
        <main className="chat-area">
          <div className="chat-messages">
            {messages.map((msg) => {
              const isAssistant = msg.sender === 'assistant';
              const hasClassification = isAssistant && msg.classification;

              return (
                <div key={msg.id} className={`message-row ${msg.sender}`}>
                  {isAssistant ? (
                    <div className="message-bubble-wrapper">
                      <div className="message-bubble">
                        <ReactMarkdown>{msg.text}</ReactMarkdown>
                      </div>

                      {hasClassification && msg.classification && (
                        <div className="report-card">
                          <div className="report-card-header">
                            <span className="report-card-tag">Diagnóstico Pedagógico</span>
                            <span className={`achievement-badge ${msg.classification.logro.toLowerCase().replace(/ /g, '-')}`}>
                              {msg.classification.logro}
                            </span>
                          </div>
                          <h4 className="report-card-title">
                            {msg.classification.movimiento}
                          </h4>
                          <p className="report-card-justification">
                            {msg.classification.justificacion}
                          </p>
                          <div className="report-card-actions">
                            <button onClick={handleReset} className="primary-btn reset-report-btn">
                              Evaluar otra actividad
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="message-bubble">
                      {msg.text}
                    </div>
                  )}
                </div>
              );
            })}
            {isLoading && (
              <div className="message-row assistant">
                <div className="message-bubble">
                  <div className="typing-indicator">
                    <span className="typing-dot" />
                    <span className="typing-dot" />
                    <span className="typing-dot" />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={handleSendMessage} className="chat-input-bar">
            <input
              type="text"
              className="chat-input"
              placeholder={
                currentState === 'COMPLETED'
                  ? "Análisis terminado. Hacé clic en 'Reiniciar' para evaluar otra actividad."
                  : "Describí tu actividad de clase aquí..."
              }
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              disabled={isLoading || currentState === 'COMPLETED'}
              autoFocus
            />
            <button
              type="submit"
              className="send-btn"
              disabled={isLoading || !inputText.trim() || currentState === 'COMPLETED'}
            >
              Enviar
            </button>
          </form>
        </main>

        {isSidebarOpen && (
          <aside className="pedagogical-sidebar">
            <div className="sidebar-header">
              <h3>Rúbrica de Movimientos</h3>
              <p>Los 9 movimientos de pensamiento para promover comprensión profunda.</p>
            </div>
            <div className="moves-list">
              {THINKING_MOVES.map((move) => {
                const isDetected = latestClassification?.movimiento === move.name;
                const isExpanded = expandedMove === move.name;

                return (
                  <div
                    key={move.name}
                    className={`move-card ${isDetected ? 'detected' : ''} ${isExpanded ? 'expanded' : ''}`}
                    onClick={() => setExpandedMove(isExpanded ? null : move.name)}
                  >
                    <div className="move-card-header">
                      <span className="move-name">{move.name}</span>
                      {isDetected && <span className="detected-tag">Detectado</span>}
                    </div>
                    <p className="move-desc">{move.desc}</p>
                    {isExpanded && (
                      <div className="move-detail-exp">
                        <strong>Logro esperado:</strong>
                        <p>{move.logroEsperado}</p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </aside>
        )}
      </div>
    </div>
  );
}

export default App;
