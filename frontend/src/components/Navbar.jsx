import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../AuthContext';

export default function Navbar() {
  const { user, logout } = useAuth();
  const { pathname } = useLocation();
  const active = (p) => pathname === p ? 'bg-emerald-50 text-emerald-700' : 'text-slate-600 hover:text-slate-900';

  return (
    <nav className="bg-white border-b border-slate-200 sticky top-0 z-30">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <span className="font-semibold text-emerald-700 text-lg tracking-tight">🧠 MindCare</span>
          <div className="flex gap-1">
            <Link to="/" className={`px-3 py-1.5 rounded-md text-sm font-medium transition ${active('/')}`}>Dashboard</Link>
            <Link to="/chat" className={`px-3 py-1.5 rounded-md text-sm font-medium transition ${active('/chat')}`}>AI Chat</Link>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <a href="https://findahelpline.com" target="_blank" rel="noopener noreferrer"
            className="text-xs text-orange-600 hover:underline hidden sm:inline">🚨 Crisis Help</a>
          <span className="text-sm text-slate-500 hidden sm:inline">{user?.username}</span>
          <button onClick={logout} className="text-sm text-slate-500 hover:text-red-600 transition">Logout</button>
        </div>
      </div>
    </nav>
  );
}
