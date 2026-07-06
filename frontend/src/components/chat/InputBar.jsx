import { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';

const PLACEHOLDERS = [
  'Ask about transit performance...',
  'Try: "How is Secunderabad doing?"',
  'Try: "Why is route 219 always late?"',
  'Try: "What are the worst routes?"',
];

export default function InputBar({ onSend, loading }) {
  const [value, setValue] = useState('');
  const [phIndex, setPhIndex] = useState(0);
  const inputRef = useRef(null);

  useEffect(() => {
    const iv = setInterval(() => {
      setPhIndex(i => (i + 1) % PLACEHOLDERS.length);
    }, 4000);
    return () => clearInterval(iv);
  }, []);

  function handleSubmit() {
    const trimmed = value.trim();
    if (!trimmed || loading) return;
    onSend(trimmed);
    setValue('');
  }

  return (
    <div className="flex gap-2">
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={e => setValue(e.target.value)}
        onKeyDown={e => e.key === 'Enter' && handleSubmit()}
        placeholder={PLACEHOLDERS[phIndex]}
        disabled={loading}
        className="flex-1 px-4 py-3 rounded-xl bg-surface border border-border text-text placeholder-text-dim focus:outline-none focus:border-primary transition-colors text-sm disabled:opacity-50"
      />
      <button
        onClick={handleSubmit}
        disabled={loading || !value.trim()}
        className="px-4 py-3 rounded-xl bg-primary text-white hover:bg-primary-dark disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer"
      >
        <Send size={18} />
      </button>
    </div>
  );
}
