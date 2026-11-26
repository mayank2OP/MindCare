import { useState, useRef, useEffect } from 'react';
import { api } from '../api';

const PROMPTS = [
  { emoji: '📱', text: 'How can I stop scrolling before sleep?' },
  { emoji: '🧘', text: 'What is the 5-4-3-2-1 anxiety technique?' },
  { emoji: '⏱️', text: 'How does Pomodoro reduce fatigue?' },
  { emoji: '🏃', text: 'WHO exercise guidelines for students?' },
];

export default function Chat() {
  const [messages, setMessages] = useState([
    { role: 'assistant', text: "Hello! I'm your MindCare wellness assistant. Ask me about sleep, stress, screen time, or study habits — grounded in WHO, Harvard, and Stanford guidelines.", sources: [] },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottom = useRef(null);

  useEffect(() => { bottom.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const send = async (text) => {
    if (!text.trim() || loading) return;
    setMessages(p => [...p, { role: 'user', text }]);
    setInput('');
    setLoading(true);
    try {
      const res = await api.chat({ message: text });
      if (!res.ok) throw new Error('Failed');
      const d = await res.json();
      setMessages(p => [...p, { role: 'assistant', text: d.reply, sources: d.sources || [], isCrisis: d.is_crisis }]);
    } catch {
      setMessages(p => [...p, { role: 'assistant', text: 'Sorry, something went wrong. Please try again.' }]);
    } finally { setLoading(false); }
  };

  return (
    <div className="max-w-3xl mx-auto p-4 flex flex-col" style={{ height: 'calc(100vh - 56px)' }}>
      <div className="flex items-center justify-between mb-3">
        <div>
          <h1 className="text-lg font-bold text-slate-800">💬 AI Wellness Assistant</h1>
          <p className="text-xs text-slate-500">Grounded in verified health guidelines • Non-diagnostic</p>
        </div>
        <span className="text-[10px] font-mono bg-emerald-50 text-emerald-700 px-2 py-1 rounded-full">🟢 Guardrails Active</span>
      </div>

      {/* Quick prompts */}
      <div className="flex gap-2 mb-3 overflow-x-auto pb-1">
        {PROMPTS.map((p, i) => (
          <button key={i} onClick={() => send(p.text)} disabled={loading}
            className="shrink-0 text-xs px-3 py-1.5 bg-white border border-slate-200 rounded-full text-slate-600 hover:border-emerald-400 hover:text-emerald-700 transition disabled:opacity-50">
            {p.emoji} {p.text}
          </button>
        ))}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-3 mb-3">
        {messages.map((m, i) => (
          <div key={i} className={`flex gap-2.5 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-sm shrink-0 ${
              m.role === 'user' ? 'bg-emerald-600 text-white' : m.isCrisis ? 'bg-red-100 text-red-600' : 'bg-emerald-50 text-emerald-600'
            }`}>
              {m.role === 'user' ? '👤' : m.isCrisis ? '🚨' : '🌱'}
            </div>
            <div className={`max-w-[80%] rounded-xl px-3.5 py-2.5 text-sm leading-relaxed ${
              m.role === 'user' ? 'bg-emerald-600 text-white'
                : m.isCrisis ? 'bg-red-50 border border-red-200 text-red-800'
                : 'bg-white border border-slate-200 text-slate-700'
            }`}>
              <p className="whitespace-pre-wrap">{m.text}</p>
              {m.sources?.length > 0 && (
                <p className="text-[10px] mt-2 opacity-70 font-mono">📚 {m.sources.map(s => s.source).join(' • ')}</p>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex gap-2.5">
            <div className="w-7 h-7 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center text-sm">🌱</div>
            <div className="bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm text-slate-400 italic">Searching guidelines…</div>
          </div>
        )}
        <div ref={bottom} />
      </div>

      {/* Input */}
      <form onSubmit={e => { e.preventDefault(); send(input); }} className="flex gap-2">
        <input value={input} onChange={e => setInput(e.target.value)} disabled={loading}
          placeholder="Ask about sleep, stress, screen time…"
          className="flex-1 px-3.5 py-2.5 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent disabled:opacity-50" />
        <button type="submit" disabled={loading || !input.trim()}
          className="px-5 py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-semibold hover:bg-emerald-700 disabled:opacity-50 transition">
          Send
        </button>
      </form>
    </div>
  );
}
