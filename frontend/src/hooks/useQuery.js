import { useState, useCallback, useRef } from 'react';
import { postQuery } from '../utils/api';

let sessionCounter = 0;

export function useQuery() {
  const sessionId = useRef(`web-${Date.now()}-${++sessionCounter}`);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const send = useCallback(async (text) => {
    const userMsg = { role: 'user', text, id: Date.now() };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);
    setError(null);

    try {
      const data = await postQuery(text, sessionId.current);
      const botMsg = {
        role: 'bot',
        text: data.answer_text,
        id: Date.now() + 1,
        meta: {
          skill: data.source_skill,
          provenance: data.data_provenance,
          metrics: data.cited_metrics,
        },
      };
      setMessages(prev => [...prev, botMsg]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const clear = useCallback(() => {
    setMessages([]);
    setError(null);
    sessionId.current = `web-${Date.now()}-${++sessionCounter}`;
  }, []);

  return { messages, loading, error, send, clear };
}
