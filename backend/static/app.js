const { useState, useEffect, useRef } = React;

const API = "/api";

// ─── API helpers ────────────────────────────────────────────────────
async function apiFetch(path, options = {}) {
  const res = await fetch(API + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// ─── ListenButton ────────────────────────────────────────────────────
function ListenButton({ text }) {
  const [state, setState] = useState("idle"); // idle | loading | playing | error
  const audioRef = useRef(null);

  async function handleListen() {
    if (state === "playing") {
      audioRef.current?.pause();
      setState("idle");
      return;
    }
    setState("loading");
    try {
      const data = await apiFetch("/tts", {
        method: "POST",
        body: JSON.stringify({ text }),
      });
      const blob = new Blob(
        [Uint8Array.from(atob(data.audio_base64), c => c.charCodeAt(0))],
        { type: "audio/mp3" }
      );
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => setState("idle");
      audio.play();
      setState("playing");
    } catch {
      setState("error");
      setTimeout(() => setState("idle"), 3000);
    }
  }

  const label = state === "loading" ? "Loading…"
    : state === "playing" ? "⏹ Stop"
    : state === "error" ? "TTS unavailable"
    : "🔊 Listen";

  return (
    <button
      className={`listen-btn ${state === "playing" ? "playing" : ""}`}
      onClick={handleListen}
      disabled={state === "loading"}
    >
      {state === "loading" && <span className="spinner">⟳</span>}
      {label}
    </button>
  );
}

// ─── SourceLinks ─────────────────────────────────────────────────────
function SourceLinks({ sources }) {
  if (!sources || sources.length === 0) return null;
  return (
    <div className="sources-list">
      <div className="sources-label">Sources</div>
      {sources.map((s, i) => (
        <a
          key={i}
          href={s.url}
          target="_blank"
          rel="noopener noreferrer"
          className="source-card"
        >
          <div className="source-title">{s.title}</div>
          {(s.description || s.excerpt) && (
            <div className="source-desc">{s.description || s.excerpt}</div>
          )}
        </a>
      ))}
    </div>
  );
}

// ─── FeedbackPanel ───────────────────────────────────────────────────
function FeedbackPanel({ result }) {
  return (
    <div className={`feedback-panel ${result.correct ? "correct-feedback" : "wrong-feedback"}`}>
      <div className="feedback-verdict">
        {result.correct ? "✅ Correct!" : `❌ Not quite — the answer is: ${result.correct_answer}`}
      </div>
      <div className="feedback-explanation">{result.explanation}</div>
      <div style={{ display: "flex", gap: "10px", alignItems: "center", marginBottom: "12px" }}>
        <ListenButton text={result.explanation} />
      </div>
      <SourceLinks sources={result.sources} />
    </div>
  );
}

// ─── QuizArea ────────────────────────────────────────────────────────
function QuizArea({ topic }) {
  const questions = topic.trivia_questions;
  const [index, setIndex] = useState(0);
  const [selected, setSelected] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [score, setScore] = useState(0);

  const q = questions[index];
  const progress = ((index) / questions.length) * 100;

  async function handleSelect(choice) {
    if (selected || loading) return;
    setSelected(choice);
    setLoading(true);
    try {
      const data = await apiFetch("/quiz/submit", {
        method: "POST",
        body: JSON.stringify({
          topic_id: topic.id,
          question_id: q.id,
          user_answer: choice,
        }),
      });
      setResult(data);
      if (data.correct) setScore(s => s + 1);
    } catch (e) {
      setResult({ correct: false, correct_answer: "Error", explanation: e.message, sources: [] });
    } finally {
      setLoading(false);
    }
  }

  function handleNext() {
    if (index + 1 >= questions.length) {
      setDone(true);
    } else {
      setIndex(i => i + 1);
      setSelected(null);
      setResult(null);
    }
  }

  function handleRestart() {
    setIndex(0);
    setSelected(null);
    setResult(null);
    setDone(false);
    setScore(0);
  }

  if (done) {
    const pct = Math.round((score / questions.length) * 100);
    const subject = topic.title.replace(/\s+Quiz$/i, "");
    return (
      <div className="quiz-area">
        <div className="quiz-complete">
          <div className="score-ring">{pct >= 80 ? "🏆" : pct >= 50 ? "📚" : "💡"}</div>
          <h3>{score} / {questions.length} correct</h3>
          <p>
            {pct >= 80 ? `Excellent! You really know ${subject}.`
              : pct >= 50 ? `Good work! A bit more reading and you'll master ${subject}.`
              : `Keep exploring ${subject} and try again.`}
          </p>
          <button className="btn btn-primary" onClick={handleRestart}>Try Again</button>
        </div>
      </div>
    );
  }

  return (
    <div className="quiz-area">
      <div className="progress-bar-wrap">
        <span className="progress-label">Question {index + 1} of {questions.length}</span>
        <div className="progress-track">
          <div className="progress-fill" style={{ width: `${progress}%` }} />
        </div>
      </div>

      <div className="question-text">{q.question}</div>

      <div className="choices">
        {q.choices.map(choice => {
          let cls = "choice-btn";
          if (selected) {
            if (choice === result?.correct_answer) cls += " correct";
            else if (choice === selected && !result?.correct) cls += " wrong";
            else cls += " revealed";
          }
          return (
            <button
              key={choice}
              className={cls}
              onClick={() => handleSelect(choice)}
              disabled={!!selected || loading}
            >
              {choice}
            </button>
          );
        })}
      </div>

      {loading && (
        <div style={{ marginTop: "16px", color: "var(--text-muted)", fontSize: "0.9rem" }}>
          Checking your answer…
        </div>
      )}

      {result && <FeedbackPanel result={result} />}

      {result && (
        <div className="quiz-nav">
          <button className="btn btn-primary" onClick={handleNext}>
            {index + 1 >= questions.length ? "See Results" : "Next Question →"}
          </button>
        </div>
      )}
    </div>
  );
}

// ─── MessageBubble ───────────────────────────────────────────────────
function MessageBubble({ msg }) {
  if (msg.role === "user") {
    return (
      <div className="message-bubble user">
        <div className="bubble-text">{msg.content}</div>
      </div>
    );
  }
  return (
    <div className="message-bubble assistant">
      <div className="bubble-text">{msg.content}</div>
      <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
        <ListenButton text={msg.content} />
      </div>
      {msg.sources && <SourceLinks sources={msg.sources} />}
    </div>
  );
}

// ─── ChatbotPanel ────────────────────────────────────────────────────
function ChatbotPanel({ topic }) {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: `Ask me anything about ${topic.title}! Try: "Why did King Sejong invent Hangul?"`,
      sources: [],
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    const q = input.trim();
    if (!q || loading) return;
    setInput("");
    setMessages(ms => [...ms, { role: "user", content: q }]);
    setLoading(true);
    try {
      const data = await apiFetch("/chat", {
        method: "POST",
        body: JSON.stringify({ topic_id: topic.id, question: q }),
      });
      setMessages(ms => [
        ...ms,
        { role: "assistant", content: data.answer, sources: data.sources },
      ]);
    } catch (e) {
      setMessages(ms => [
        ...ms,
        { role: "assistant", content: `Something went wrong — ${e.message}`, sources: [] },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="chatbot-panel">
      <div className="chatbot-header">
        <span>🤖</span>
        <h3>Research Assistant</h3>
        <span className="model-badge">watsonx Orchestrate</span>
      </div>

      <div className="message-list">
        {messages.map((msg, i) => <MessageBubble key={i} msg={msg} />)}
        {loading && (
          <div className="message-bubble assistant">
            <div className="bubble-text">
              <div className="loading-dots">
                <span /><span /><span />
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="chat-input-row">
        <textarea
          className="chat-input"
          placeholder="Ask a question about this topic…"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />
        <button
          className="btn btn-primary"
          onClick={handleSend}
          disabled={!input.trim() || loading}
        >
          {loading ? <span className="spinner">⟳</span> : "Send"}
        </button>
      </div>
    </div>
  );
}

// ─── TopicPage ───────────────────────────────────────────────────────
function TopicPage({ topic }) {
  return (
    <div>
      <div className="topic-header">
        <h2>{topic.title}</h2>
        <div className="subtitle">{topic.subtitle}</div>
        <div className="badges">
          <span className="badge history">{topic.topic_metadata.category}</span>
          <span className="badge beginner">{topic.topic_metadata.difficulty}</span>
          <span className="badge">⏱ {topic.topic_metadata.estimated_minutes} min</span>
        </div>
        <div className="primer-text">{topic.primer}</div>
        <div style={{ marginTop: "14px" }}>
          <ListenButton text={topic.primer} />
        </div>
      </div>

      <div className="section-title">Quiz — Test Your Knowledge</div>
      <QuizArea topic={topic} />

      <div className="section-title">Chatbot — Ask Anything</div>
      <ChatbotPanel topic={topic} />
    </div>
  );
}

// ─── App Root ────────────────────────────────────────────────────────
function App() {
  const [topics, setTopics] = useState([]);
  const [activeTopic, setActiveTopic] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    apiFetch("/topics")
      .then(setTopics)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (topics.length > 0 && !activeTopic) {
      // Auto-load the first topic
      apiFetch(`/topics/${topics[0].id}`)
        .then(setActiveTopic)
        .catch(e => setError(e.message));
    }
  }, [topics]);

  function selectTopic(id) {
    setActiveTopic(null);
    apiFetch(`/topics/${id}`)
      .then(setActiveTopic)
      .catch(e => setError(e.message));
  }

  return (
    <div className="app">
      <header className="app-header">
        <span className="logo">📖</span>
        <h1>EduTrivia</h1>
      </header>

      {topics.length > 1 && (
        <div className="topic-tabs" role="tablist" aria-label="Quiz topics">
          {topics.map(t => (
            <button
              key={t.id}
              type="button"
              role="tab"
              className={`topic-tab ${activeTopic?.id === t.id ? "active" : ""}`}
              aria-selected={activeTopic?.id === t.id}
              onClick={() => selectTopic(t.id)}
            >
              {t.title}
            </button>
          ))}
        </div>
      )}

      {loading && (
        <div style={{ textAlign: "center", color: "var(--text-muted)", padding: "60px 0" }}>
          Loading topics…
        </div>
      )}

      {error && (
        <div style={{
          background: "#f8717118",
          border: "1px solid var(--red)",
          borderRadius: "8px",
          padding: "16px",
          color: "var(--red)",
          marginBottom: "20px",
        }}>
          Error: {error}
        </div>
      )}

      {activeTopic && <TopicPage topic={activeTopic} />}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
