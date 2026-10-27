import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "motion/react";

export interface Message {
  id: string;
  role: "user" | "ai";
  text: string;
}

interface Props {
  initialQuery: string;
  chatUrl?: string;
}

const uid = () => Math.random().toString(36).slice(2);

export default function ChatScreen({ initialQuery, chatUrl = "/api/chat" }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const started = useRef(false); // Prevent duplicate execution in React StrictMode

  const send = async (text: string) => {
    const userMsg: Message = { id: uid(), role: "user", text };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await fetch(chatUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: text }),
      });
      if (!res.ok) throw new Error(String(res.status));
      const data = await res.json(); // expected: { answer: string }
      setMessages((prev) => [...prev, { id: uid(), role: "ai", text: data.answer }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { id: uid(), role: "ai", text: "Sorry, there was an issue retrieving the answer. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Send the initial query automatically
  useEffect(() => {
    if (started.current) return;
    started.current = true;
    send(initialQuery);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const t = input.trim();
    if (!t || loading) return;
    setInput("");
    send(t);
  };

  return (
    <motion.div
      className="chat"
      // Slide upward from below to full screen
      initial={{ y: "100%" }}
      animate={{ y: 0 }}
      exit={{ y: "100%" }}
      transition={{ type: "spring", stiffness: 70, damping: 16 }}
    >
      <div className="chat-header">💬 Chat</div>

      <div className="chat-messages">
        <AnimatePresence initial={false}>
          {messages.map((m) => (
            <motion.div
              key={m.id}
              className={`bubble ${m.role}`}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.25 }}
            >
              {m.text}
            </motion.div>
          ))}

          {loading && (
            <motion.div
              key="typing"
              className="bubble ai typing"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              {[0, 1, 2].map((i) => (
                <motion.span
                  key={i}
                  animate={{ y: [0, -6, 0] }}
                  transition={{ repeat: Infinity, duration: 0.7, delay: i * 0.15 }}
                />
              ))}
            </motion.div>
          )}
        </AnimatePresence>
        <div ref={bottomRef} />
      </div>

      <form className="chat-input" onSubmit={submit}>
        <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Type your message…" />
        <motion.button type="submit" whileTap={{ scale: 0.9 }} disabled={loading || !input.trim()}>
          Send
        </motion.button>
      </form>
    </motion.div>
  );
}