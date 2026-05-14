'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Loader2, Sparkles, ChevronDown, ChevronRight, Check, Circle } from 'lucide-react';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  toolCalls?: ToolStep[];
}

interface ToolStep {
  id: number;
  tool: string;
  label: string;
  agent?: string;
  done: boolean;
  type: 'tool' | 'thought';
  isNarration?: boolean;
}

const WELCOME: ChatMessage = {
  role: 'assistant',
  content: `I'm Jobby Bot, your job application assistant! Here's what I can help you with:

**Job Search** — Search across LinkedIn, Indeed, and Google. Filter by location, remote work, and more.

**Resume Generation** — Customized, ATS-optimized resumes in PDF, markdown, and text.

**Cover Letter Writing** — Personalized cover letters matched to each job.

**Email Management** — Send application emails with resume and cover letter attached.

**Auto-Apply** — Browser automation to fill out and submit job application forms.

**Application Tracking** — Track all applications in a Notion database.

Just tell me what you're looking for! For example:
- "Find 20 remote software engineer jobs"
- "Search for data analyst positions in Seattle"
- "Generate a resume for this role"`,
  timestamp: new Date(),
};

const SUGGESTIONS = [
  'Search for AI engineer jobs in Toronto',
  'Help me tailor my resume for this role',
  'Write a cover letter for my top match',
  'What are my application stats?',
];

/* ── Simple markdown renderer for chat ── */
function renderMarkdown(text: string) {
  // Split by **bold** markers, then render alternating spans
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} style={{ fontWeight: 600, color: 'var(--ink)' }}>{part.slice(2, -2)}</strong>;
    }
    return <span key={i}>{part}</span>;
  });
}

/* ── Collapsible thinking block ── */
function ThinkingBlock({ steps, isLive }: { steps: ToolStep[]; isLive: boolean }) {
  const [expanded, setExpanded] = useState(isLive);
  const doneCount = steps.filter((s) => s.done).length;
  const totalCount = steps.length;
  const allDone = doneCount === totalCount && totalCount > 0;

  // Auto-expand while live, but allow user toggle
  useEffect(() => {
    if (isLive) setExpanded(true);
  }, [isLive]);

  if (steps.length === 0) return null;

  return (
    <div className="mb-2 ml-10" style={{ maxWidth: 'calc(75% - 28px)' }}>
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 text-[11px] font-medium py-1 px-2 rounded-md transition-colors w-full"
        style={{
          color: allDone && !isLive ? 'var(--green-ink)' : 'var(--ink-3)',
          background: allDone && !isLive ? 'var(--green-soft)' : 'var(--accent-softer)',
        }}
      >
        {expanded ? <ChevronDown size={11} /> : <ChevronRight size={11} />}
        {isLive ? (
          <><Loader2 size={10} className="animate-spin" /> Working...</>
        ) : (
          <><Check size={10} /> Completed {totalCount} step{totalCount !== 1 ? 's' : ''}</>
        )}
      </button>

      {expanded && (
        <div
          className="mt-1 rounded-lg px-3 py-2 text-[11px] leading-[1.8] animate-fadeIn"
          style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
        >
          {steps.map((step) => {
            if (step.type === 'thought') {
              // Show first line of thinking content, truncated
              const preview = step.label.split('\n')[0].slice(0, 120);
              return (
                <div key={step.id} className="flex items-start gap-2" style={{ color: 'var(--ink-4)' }}>
                  {step.done ? (
                    <Check size={9} style={{ color: 'var(--ink-4)', flexShrink: 0, marginTop: 4 }} />
                  ) : (
                    <Loader2 size={9} className="animate-spin" style={{ flexShrink: 0, marginTop: 4 }} />
                  )}
                  <span className="truncate" style={{ fontStyle: 'italic', maxWidth: '100%' }}>{preview}{step.label.length > 120 ? '...' : ''}</span>
                </div>
              );
            }
            return (
              <div key={step.id} className="flex items-start gap-2" style={{ color: step.done ? 'var(--green-ink)' : 'var(--ink-3)' }}>
                {step.done ? (
                  <Check size={10} style={{ color: 'var(--green)', flexShrink: 0, marginTop: 3 }} />
                ) : (
                  <Circle size={8} className="animate-pulse" style={{ color: 'var(--amber)', flexShrink: 0, fill: 'var(--amber)', marginTop: 4 }} />
                )}
                <span>{step.label}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME]);
  const [draft, setDraft] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [activeTools, setActiveTools] = useState<ToolStep[]>([]);
  const [statusText, setStatusText] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const stepIdRef = useRef(0);

  const scrollToBottom = useCallback(() => {
    setTimeout(() => scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' }), 50);
  }, []);

  useEffect(() => { scrollToBottom(); }, [messages, streamingContent, activeTools, scrollToBottom]);

  const sendMessage = async () => {
    const text = draft.trim();
    if (!text || isLoading) return;

    setMessages((prev) => [...prev, { role: 'user', content: text, timestamp: new Date() }]);
    setDraft('');
    setIsLoading(true);
    setStreamingContent('');
    setActiveTools([]);
    setStatusText('');
    stepIdRef.current = 0;

    try {
      const res = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, history: messages.slice(-10).map((m) => ({ role: m.role, content: m.content })) }),
      });
      if (!res.ok) throw new Error(`Chat failed: ${res.status}`);

      const reader = res.body?.getReader();
      if (!reader) throw new Error('No stream reader');

      const decoder = new TextDecoder();
      let buffer = '';
      let fullContent = '';
      const toolHistory: ToolStep[] = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const raw = line.slice(6).trim();
          if (!raw) continue;

          try {
            const evt = JSON.parse(raw);

            switch (evt.type) {
              case 'status':
                setStatusText(evt.content || '');
                break;

              case 'tool_start': {
                // Move any pre-tool streaming content into thinking block (narration only)
                if (fullContent) {
                  stepIdRef.current += 1;
                  toolHistory.push({
                    id: stepIdRef.current,
                    tool: `thought_${stepIdRef.current}`,
                    label: fullContent,
                    done: false,
                    type: 'thought',
                    isNarration: true,
                  });
                  fullContent = '';
                  setStreamingContent('');
                }
                stepIdRef.current += 1;
                const step: ToolStep = {
                  id: stepIdRef.current,
                  tool: evt.tool,
                  label: evt.label || evt.tool,
                  agent: evt.agent,
                  done: false,
                  type: 'tool',
                };
                toolHistory.push(step);
                setActiveTools([...toolHistory]);
                setStatusText('');
                break;
              }

              case 'thinking': {
                // Accumulate thinking content into a single entry (skip narration entries)
                const chunk = evt.content || '';
                if (chunk) {
                  const existing = toolHistory.find((x) => x.type === 'thought' && !x.done && !x.isNarration);
                  if (existing) {
                    existing.label += chunk;
                  } else {
                    stepIdRef.current += 1;
                    toolHistory.push({
                      id: stepIdRef.current,
                      tool: `thought_${stepIdRef.current}`,
                      label: chunk,
                      done: false,
                      type: 'thought',
                    });
                  }
                  setActiveTools([...toolHistory]);
                }
                break;
              }

              case 'tool_end': {
                // Match by tool base name (backend sends unique keys like "search_jobs_1")
                const t = toolHistory.find((x) => x.tool.startsWith(evt.tool) && !x.done);
                if (t) t.done = true;
                setActiveTools([...toolHistory]);
                break;
              }

              case 'content': {
                const hasTools = toolHistory.some((x) => x.type === 'tool');
                if (hasTools) {
                  // Tools were used — route content to thinking block (skip narration entries)
                  const chunk = evt.content || '';
                  if (chunk) {
                    const existing = toolHistory.find((x) => x.type === 'thought' && !x.done && !x.isNarration);
                    if (existing) {
                      existing.label += chunk;
                    } else {
                      stepIdRef.current += 1;
                      toolHistory.push({
                        id: stepIdRef.current,
                        tool: `thought_${stepIdRef.current}`,
                        label: chunk,
                        done: false,
                        type: 'thought',
                      });
                    }
                    setActiveTools([...toolHistory]);
                  }
                } else {
                  // No tools — stream directly as response
                  const openThought = toolHistory.find((x) => x.type === 'thought' && !x.done);
                  if (openThought) openThought.done = true;
                  fullContent += evt.content;
                  setStreamingContent(fullContent);
                  setActiveTools([...toolHistory]);
                }
                setStatusText('');
                break;
              }

              case 'error':
                fullContent += evt.content || 'An error occurred.';
                setStreamingContent(fullContent);
                break;

              case 'done': {
                // If tools were used, all content arrived as 'thinking'.
                // Extract non-narration thinking text as the response.
                let responseText = fullContent;
                if (!responseText) {
                  const thoughts = toolHistory.filter((x) => x.type === 'thought' && !x.isNarration);
                  responseText = thoughts.map((t) => t.label).join('');
                }
                // Mark all thoughts as done
                toolHistory.forEach((t) => { if (t.type === 'thought') t.done = true; });

                if (responseText) {
                  setMessages((prev) => [...prev, {
                    role: 'assistant',
                    content: responseText,
                    timestamp: new Date(),
                    toolCalls: toolHistory.filter((t) => t.type === 'tool').length > 0
                      ? toolHistory.filter((t) => t.type === 'tool')
                      : undefined,
                  }]);
                }
                setStreamingContent('');
                setActiveTools([]);
                setStatusText('');
                break;
              }
            }
          } catch {
            // skip malformed JSON
          }
        }
      }

      // Safety: if stream ended without 'done' event
      const hasContent = fullContent || toolHistory.some((x) => x.type === 'thought' && !x.isNarration);
      if (hasContent && !messages.find((m) => m.content === fullContent)) {
        const fallbackText = fullContent || toolHistory.filter((x) => x.type === 'thought' && !x.isNarration).map((t) => t.label).join('');
        setMessages((prev) => [...prev, {
          role: 'assistant',
          content: fallbackText,
          timestamp: new Date(),
          toolCalls: toolHistory.filter((t) => t.type === 'tool').length > 0 ? toolHistory.filter((t) => t.type === 'tool') : undefined,
        }]);
        setStreamingContent('');
        setActiveTools([]);
      }

    } catch {
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Couldn\'t connect to the backend. Make sure the API server is running.', timestamp: new Date() }]);
      setStreamingContent('');
      setActiveTools([]);
    } finally {
      setIsLoading(false);
      setStatusText('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  const showSuggestions = messages.length <= 1 && !draft;

  return (
    <div className="flex-1 flex flex-col min-h-0" style={{ background: 'var(--bg)' }}>
      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        <div className="max-w-2xl mx-auto px-4 py-6 flex flex-col gap-5">
          {/* Welcome header */}
          {showSuggestions && (
            <div className="text-center py-8 animate-fadeIn">
              <div
                className="inline-flex items-center justify-center w-14 h-14 rounded-2xl mb-4"
                style={{ background: 'linear-gradient(135deg, var(--accent-soft) 0%, var(--purple-soft) 100%)', border: '1px solid var(--accent)' }}
              >
                <span className="font-display text-[24px] font-bold" style={{ color: 'var(--accent)' }}>J</span>
              </div>
              <h2 className="font-display text-[24px]" style={{ letterSpacing: '-0.03em' }}>
                How can I help?
              </h2>
              <p className="text-[13px] mt-1" style={{ color: 'var(--ink-3)' }}>
                Ask anything about your job search.
              </p>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i}>
              {/* Collapsible thinking block for completed tool calls */}
              {msg.role === 'assistant' && msg.toolCalls && msg.toolCalls.length > 0 && (
                <ThinkingBlock steps={msg.toolCalls} isLive={false} />
              )}

              <div className={`flex gap-3 animate-fadeInUp ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                {/* Avatar */}
                <div
                  className="flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center text-[11px] font-bold"
                  style={{
                    background: msg.role === 'assistant' ? 'var(--accent-soft)' : 'var(--blue-soft)',
                    color: msg.role === 'assistant' ? 'var(--accent)' : 'var(--blue-ink)',
                    border: `1px solid ${msg.role === 'assistant' ? 'var(--accent)' : 'var(--blue)'}`,
                  }}
                >
                  {msg.role === 'assistant' ? 'J' : 'Y'}
                </div>

                {/* Bubble */}
                <div
                  className="max-w-[75%] px-4 py-3 text-[13px] leading-relaxed"
                  style={{
                    borderRadius: msg.role === 'user' ? '16px 4px 16px 16px' : '4px 16px 16px 16px',
                    background: msg.role === 'user'
                      ? 'linear-gradient(135deg, var(--accent) 0%, #D4864E 100%)'
                      : 'var(--surface)',
                    color: msg.role === 'user' ? 'white' : 'var(--ink)',
                    border: msg.role === 'user' ? 'none' : '1px solid var(--border)',
                    boxShadow: 'var(--shadow-xs)',
                  }}
                >
                  <p className="whitespace-pre-wrap">{msg.role === 'assistant' ? renderMarkdown(msg.content) : msg.content}</p>
                </div>
              </div>
            </div>
          ))}

          {/* Streaming area */}
          {isLoading && (
            <div className="animate-fadeIn">
              {/* Live thinking block */}
              {activeTools.length > 0 && (
                <ThinkingBlock steps={activeTools} isLive={true} />
              )}

              {/* Streaming content bubble */}
              {streamingContent ? (
                <div className="flex gap-3">
                  <div
                    className="flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center text-[11px] font-bold"
                    style={{ background: 'var(--accent-soft)', border: '1px solid var(--accent)', color: 'var(--accent)' }}
                  >
                    J
                  </div>
                  <div
                    className="max-w-[75%] px-4 py-3 text-[13px] leading-relaxed"
                    style={{
                      borderRadius: '4px 16px 16px 16px',
                      background: 'var(--surface)',
                      color: 'var(--ink)',
                      border: '1px solid var(--border)',
                      boxShadow: 'var(--shadow-xs)',
                    }}
                  >
                    <p className="whitespace-pre-wrap">{renderMarkdown(streamingContent)}<span className="inline-block w-1.5 h-4 ml-0.5 rounded-sm animate-pulse" style={{ background: 'var(--accent)', verticalAlign: 'text-bottom' }} /></p>
                  </div>
                </div>
              ) : (
                /* Thinking indicator when no content yet */
                <div className="flex gap-3">
                  <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: 'var(--accent-soft)', border: '1px solid var(--accent)' }}>
                    <span className="font-bold text-[11px]" style={{ color: 'var(--accent)' }}>J</span>
                  </div>
                  <div className="card-warm rounded-2xl rounded-tl px-4 py-3">
                    <div className="flex items-center gap-2 text-[13px]" style={{ color: 'var(--ink-3)' }}>
                      <Loader2 size={13} className="animate-spin" />
                      {statusText || 'Thinking...'}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Suggestions */}
          {showSuggestions && (
            <div className="grid grid-cols-2 gap-2 mt-2 stagger-children">
              {SUGGESTIONS.map((s, i) => (
                <button
                  key={i}
                  onClick={() => { setDraft(s); inputRef.current?.focus(); }}
                  className="lift card-warm text-left px-3 py-2.5 rounded-lg text-[12px] animate-fadeInUp"
                  style={{ color: 'var(--ink-2)' }}
                >
                  <Sparkles size={11} className="inline mr-1.5" style={{ color: 'var(--accent)' }} />
                  {s}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Input */}
      <div className="flex-shrink-0 px-4 py-3" style={{ borderTop: '1px solid var(--border)', background: 'var(--surface)' }}>
        <div className="max-w-2xl mx-auto flex items-end gap-3">
          <textarea
            ref={inputRef}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            placeholder="Ask Jobby anything..."
            className="input-warm flex-1 resize-none"
            style={{ minHeight: 44, maxHeight: 120, borderRadius: 12 }}
            onInput={(e) => {
              const t = e.target as HTMLTextAreaElement;
              t.style.height = 'auto';
              t.style.height = Math.min(t.scrollHeight, 120) + 'px';
            }}
          />
          <button
            onClick={sendMessage}
            disabled={!draft.trim() || isLoading}
            className="flex items-center justify-center w-10 h-10 rounded-xl transition-all disabled:opacity-30 flex-shrink-0"
            style={{ background: 'var(--accent)', color: 'white', boxShadow: 'var(--shadow-sm)' }}
          >
            <Send size={15} />
          </button>
        </div>
      </div>
    </div>
  );
}
