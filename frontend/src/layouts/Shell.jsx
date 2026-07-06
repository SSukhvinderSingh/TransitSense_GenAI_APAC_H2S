import { NavLink } from 'react-router-dom';
import { MessageCircle, LayoutDashboard, Bus } from 'lucide-react';

export default function Shell({ children }) {
  const linkClass = ({ isActive }) =>
    `flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
      isActive
        ? 'bg-primary/10 text-primary'
        : 'text-text-dim hover:text-text hover:bg-surface-alt'
    }`;

  return (
    <div className="min-h-screen flex flex-col">
      <header className="h-16 border-b border-border bg-surface/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto h-full px-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <Bus size={18} className="text-white" />
            </div>
            <div>
              <span className="text-base font-semibold text-text">TransitSense</span>
              <span className="text-[10px] text-text-dim ml-2">AI Transit Copilot</span>
            </div>
          </div>

          <nav className="flex items-center gap-1">
            <NavLink to="/" end className={linkClass}>
              <MessageCircle size={16} />
              Chat
            </NavLink>
            <NavLink to="/dashboard" className={linkClass}>
              <LayoutDashboard size={16} />
              Dashboard
            </NavLink>
          </nav>
        </div>
      </header>

      <main className="flex-1">
        {children}
      </main>

      <footer className="border-t border-border bg-surface/50 px-4 py-2">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-[10px] text-text-dim">
          <span>TransitSense v0.1.0 — TGSRTC data</span>
          <span className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-warning" />
              simulated
            </span>
            <span className="inline-flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-success" />
              real
            </span>
          </span>
        </div>
      </footer>
    </div>
  );
}
