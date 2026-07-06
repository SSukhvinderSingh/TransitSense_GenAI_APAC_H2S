import { Bot, User } from 'lucide-react';
import ProvenanceBadge from './ProvenanceBadge';

function renderText(text) {
  if (!text) return '';
  const lines = text.split('\n');
  return lines.map((line, i) => {
    const trimmed = line.trim();
    if (!trimmed) return <br key={i} />;
    if (trimmed.startsWith('📍') || trimmed.startsWith('**')) {
      return (
        <div key={i} className="mb-1 last:mb-0">
          {trimmed.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/^📍/, '📍').split('<strong>').map((part, j) =>
            part.includes('</strong>') ? (
              <strong key={j}>{part.replace('</strong>', '')}</strong>
            ) : (
              part.startsWith('📍') ? <span key={j}>📍</span> : part
            )
          )}
        </div>
      );
    }
    if (trimmed.startsWith('•') || trimmed.startsWith('-')) {
      return (
        <div key={i} className="flex gap-2 ml-2 text-sm">
          <span className="text-primary mt-0.5">•</span>
          <span>{trimmed.replace(/^[•\-]\s*/, '')}</span>
        </div>
      );
    }
    if (/^\d+\./.test(trimmed)) {
      return (
        <div key={i} className="flex gap-2 ml-2 text-sm">
          <span className="text-primary mt-0.5 font-mono text-xs">{trimmed.match(/^\d+/)?.[0]}.</span>
          <span>{trimmed.replace(/^\d+\.\s*/, '')}</span>
        </div>
      );
    }
    return <div key={i} className="text-sm mb-0.5">{trimmed}</div>;
  });
}

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user';
  const isBot = message.role === 'bot';

  return (
    <div className={`flex gap-3 animate-slide-up ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
        isUser ? 'bg-primary/20' : 'bg-surface-alt'
      }`}>
        {isUser ? <User size={16} className="text-primary" /> : <Bot size={16} className="text-text-dim" />}
      </div>

      <div className={`max-w-[75%] ${isUser ? 'items-end' : 'items-start'}`}>
        {isBot && message.meta?.skill && (
          <div className="text-xs text-text-dim mb-1 font-medium">{message.meta.skill}</div>
        )}

        <div className={`rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-primary text-white rounded-tr-sm'
            : 'bg-surface border border-border rounded-tl-sm'
        }`}>
          {isUser ? (
            <p className="text-sm">{message.text}</p>
          ) : (
            <div className="prose-sm max-w-none">{renderText(message.text)}</div>
          )}
        </div>

        {isBot && (
          <div className="flex items-center gap-2 mt-1.5">
            {message.meta?.provenance && <ProvenanceBadge text={message.meta.provenance} />}
            {message.meta?.skill && (
              <span className="text-[10px] text-text-dim capitalize">{message.meta.skill}</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
