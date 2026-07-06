import { useRef, useEffect } from 'react';
import { useQuery } from '../hooks/useQuery';
import ChatMessage from '../components/chat/ChatMessage';
import InputBar from '../components/chat/InputBar';
import QuickActions from '../components/chat/QuickActions';
import { MessageCircle } from 'lucide-react';

export default function ChatPage() {
  const { messages, loading, error, send, clear } = useQuery();
  const bottomRef = useRef(null);
  const hasMessages = messages.length > 0;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex flex-col h-[calc(100vh-64px)]">
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-3xl mx-auto space-y-4">
          {!hasMessages && (
            <div className="text-center py-12">
              <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
                <MessageCircle size={32} className="text-primary" />
              </div>
              <h2 className="text-xl font-semibold text-text mb-2">Ask about Hyderabad bus routes</h2>
              <p className="text-sm text-text-dim mb-6 max-w-md mx-auto">
                Get delay analysis, forecasts, and route priority insights based on TGSRTC transit data.
              </p>
              <QuickActions onSelect={send} visible={!hasMessages} />
            </div>
          )}

          {messages.map((msg) => (
            <ChatMessage key={msg.id} message={msg} />
          ))}

          {loading && (
            <div className="flex gap-3 animate-slide-up">
              <div className="w-8 h-8 rounded-full bg-surface-alt flex items-center justify-center">
                <span className="w-2 h-2 bg-text-dim rounded-full animate-pulse" />
              </div>
              <div className="bg-surface border border-border rounded-2xl rounded-tl-sm px-4 py-3">
                <div className="flex gap-1.5">
                  <span className="w-2 h-2 bg-text-dim rounded-full animate-pulse" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 bg-text-dim rounded-full animate-pulse" style={{ animationDelay: '200ms' }} />
                  <span className="w-2 h-2 bg-text-dim rounded-full animate-pulse" style={{ animationDelay: '400ms' }} />
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="bg-destructive/10 border border-destructive/30 rounded-xl px-4 py-3 text-sm text-destructive">
              {error}
              <button onClick={clear} className="ml-2 underline text-destructive/80 hover:text-destructive cursor-pointer">
                Try again
              </button>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      <div className="border-t border-border bg-bg px-4 py-4">
        <div className="max-w-3xl mx-auto">
          <InputBar onSend={send} loading={loading} />
        </div>
      </div>
    </div>
  );
}
