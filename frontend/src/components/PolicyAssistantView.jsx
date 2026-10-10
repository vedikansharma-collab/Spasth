import React, { useState, useEffect, useRef } from 'react';
import { 
  Bot, Send, Sparkles, User, HelpCircle, FileText, 
  ExternalLink, Loader2, AlertCircle, CheckCircle2, 
  RefreshCw, BookOpen, Shield 
} from 'lucide-react';
import { askPolicy } from '../services/api';

export default function PolicyAssistantView({ 
  activePolicyId, 
  activePolicy, 
  onNavigateToDoc, 
  onSelectPolicy, 
  policies = [] 
}) {
  const [messages, setMessages] = useState([]);
  const [inputQuery, setInputQuery] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  // Initialize welcome message when policy changes
  useEffect(() => {
    if (activePolicy) {
      setMessages([
        {
          id: 'welcome',
          sender: 'bot',
          answer: `Hello! I'm your dedicated Spasth Policy Assistant for **${activePolicy.original_filename || 'your uploaded policy'}**. I can explain coverage rules, co-payment clauses, room rent limits, procedure caps, and waiting periods with line-level page citations.`,
          citations: activePolicy.rules && activePolicy.rules.length > 0 ? [
            {
              page: activePolicy.rules[0].page || 1,
              clause: activePolicy.rules[0].clause || 'Policy Schedule',
              rule: activePolicy.rules[0].rule_key || 'Base Coverage',
              source_text: activePolicy.rules[0].source_text || 'Policy document indexed and verified.'
            }
          ] : [],
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } else {
      setMessages([]);
    }
  }, [activePolicyId, activePolicy?.original_filename]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const quickQuestions = [
    "Is knee replacement covered?",
    "What is my co-pay?",
    "Is there a room rent limit?",
    "What treatments are excluded?",
    "What is the waiting period?",
    "What are my procedure sub-limits?"
  ];

  const handleSend = async (queryText) => {
    const query = (queryText || inputQuery).trim();
    if (!query) return;

    if (!activePolicyId) {
      alert('Please upload or select an active policy first.');
      return;
    }

    const userMsg = {
      id: Date.now(),
      sender: 'user',
      text: query,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!queryText) setInputQuery('');
    setIsTyping(true);

    try {
      const response = await askPolicy(activePolicyId, query);
      const botMsg = {
        id: Date.now() + 1,
        sender: 'bot',
        answer: response.answer,
        citations: response.citations || [],
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      console.error('Error asking policy assistant:', err);
      // Helpful fallback answer if server endpoint had temporary issue
      const botMsg = {
        id: Date.now() + 1,
        sender: 'bot',
        answer: `I encountered an issue connecting to the policy service (${err.response?.data?.detail || err.message}). Please ensure your policy document is selected.`,
        citations: [],
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, botMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  // 1. Empty State: No policy active
  if (!activePolicyId) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 space-y-8 animate-fade-in">
        <div className="card-white p-8 sm:p-10 text-center space-y-6 border-slate-200">
          <div className="w-16 h-16 rounded-2xl bg-[rgba(57,171,173,0.12)] border border-[#39ABAD]/40 flex items-center justify-center text-[#006668] mx-auto shadow-sm">
            <BookOpen className="w-8 h-8" />
          </div>

          <div className="max-w-md mx-auto space-y-2">
            <h2 className="text-2xl font-black text-[#003339] tracking-tight">No Policy Selected</h2>
            <p className="text-sm text-[#4A5859] leading-relaxed">
              Upload your health insurance policy PDF or select an indexed document below to start asking questions with verified citations.
            </p>
          </div>

          {policies.length > 0 && (
            <div className="pt-4 max-w-lg mx-auto space-y-3 text-left">
              <span className="text-xs font-bold uppercase tracking-wider text-[#4A5859] block">
                Select an Indexed Policy to Begin:
              </span>
              <div className="space-y-2">
                {policies.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => onSelectPolicy(p.id)}
                    className="w-full p-3.5 rounded-xl border border-[#E2E8E8] hover:border-[#39ABAD] bg-[#F7F7F8] hover:bg-white transition-all flex items-center justify-between text-left cursor-pointer group"
                  >
                    <div className="flex items-center space-x-3 min-w-0">
                      <FileText className="w-4 h-4 text-[#006668] shrink-0" />
                      <div className="min-w-0">
                        <p className="text-xs font-bold text-[#003339] truncate">{p.original_filename}</p>
                        <p className="text-[11px] text-[#4A5859] font-mono">{p.page_count} pages • {(p.file_size_bytes / 1024).toFixed(1)} KB</p>
                      </div>
                    </div>
                    <span className="text-xs font-semibold text-[#006668] group-hover:translate-x-1 transition-transform">
                      Open &rarr;
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-6 animate-fade-in">
      {/* Top Header Card */}
      <div className="card-white p-5 sm:p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-[#E2E8E8]">
        <div className="flex items-center space-x-3.5">
          <div className="w-12 h-12 rounded-xl bg-[#003339] flex items-center justify-center text-[#73FFFF] shadow-xs shrink-0">
            <Bot className="w-6 h-6 text-[#73FFFF]" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-xl font-black text-[#003339] tracking-tight">Policy Assistant</h2>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[rgba(57,171,173,0.12)] text-[#006668] border border-[#39ABAD]/40 uppercase tracking-wide">
                Citation Grounded
              </span>
            </div>
            <p className="text-xs text-[#4A5859] mt-0.5">
              Explaining terms from: <strong className="text-[#003339] font-semibold">{activePolicy?.original_filename || 'Uploaded Document'}</strong>
              {activePolicy?.page_count ? ` (${activePolicy.page_count} preserved pages)` : ''}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 shrink-0">
          <button
            onClick={() => onNavigateToDoc(1)}
            className="btn-secondary px-3.5 py-2 text-xs font-semibold flex items-center space-x-1.5 cursor-pointer"
          >
            <BookOpen className="w-3.5 h-3.5 text-[#006668]" />
            <span>View Policy Document</span>
          </button>
        </div>
      </div>

      {/* Main Assistant Chat Container */}
      <div className="card-white rounded-2xl overflow-hidden border border-[#E2E8E8] shadow-sm flex flex-col h-[650px]">
        {/* Suggested Queries Bar */}
        <div className="p-3.5 sm:p-4 bg-[#F7F7F8] border-b border-[#E2E8E8] shrink-0 space-y-2">
          <div className="flex items-center space-x-1.5 text-xs font-semibold text-[#4A5859]">
            <HelpCircle className="w-3.5 h-3.5 text-[#006668]" />
            <span>Suggested Questions:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {quickQuestions.map((q, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(q)}
                disabled={isTyping}
                className="text-xs px-3 py-1.5 rounded-full bg-white border border-[#E2E8E8] text-[#003339] hover:border-[#39ABAD] hover:text-[#006668] hover:bg-[rgba(57,171,173,0.06)] transition-all cursor-pointer font-medium shadow-2xs disabled:opacity-50"
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5 bg-white">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex items-start space-x-3 ${
                msg.sender === 'user' ? 'flex-row-reverse space-x-reverse' : 'flex-row'
              }`}
            >
              {/* Avatar */}
              <div
                className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 shadow-2xs ${
                  msg.sender === 'user'
                    ? 'bg-[#003339] text-white'
                    : 'bg-[rgba(57,171,173,0.15)] text-[#006668] border border-[#39ABAD]/40'
                }`}
              >
                {msg.sender === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              {/* Message Bubble */}
              <div
                className={`max-w-[85%] sm:max-w-[78%] rounded-2xl p-4 sm:p-5 text-xs leading-relaxed space-y-3 ${
                  msg.sender === 'user'
                    ? 'bg-[#003339] text-white rounded-tr-none shadow-sm'
                    : 'bg-[#F7F7F8] border border-[#E2E8E8] text-[#003339] rounded-tl-none shadow-2xs'
                }`}
              >
                {/* User Content */}
                {msg.sender === 'user' ? (
                  <div className="font-medium whitespace-pre-wrap">{msg.text}</div>
                ) : (
                  <>
                    {/* Assistant Answer Section */}
                    <div className="space-y-1.5">
                      <span className="text-[10px] font-bold tracking-wider uppercase text-[#006668] block">
                        Policy Explanation
                      </span>
                      <div className="text-xs sm:text-sm text-[#003339] leading-relaxed whitespace-pre-wrap font-sans">
                        {msg.answer}
                      </div>
                    </div>

                    {/* Grounded Citation Section */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="pt-3 border-t border-[#E2E8E8] space-y-2">
                        <span className="text-[10px] font-bold tracking-wider uppercase text-[#4A5859] block flex items-center space-x-1">
                          <FileText className="w-3 h-3 text-[#006668]" />
                          <span>Source Document Evidence:</span>
                        </span>

                        <div className="space-y-2">
                          {msg.citations.map((cite, cIdx) => (
                            <div
                              key={cIdx}
                              className="p-3 rounded-xl bg-white border border-[#E2E8E8] hover:border-[#39ABAD] transition-all space-y-1.5"
                            >
                              <div className="flex items-center justify-between gap-2">
                                <span className="font-bold text-[#003339] text-xs">
                                  {cite.rule || 'Policy Clause'}
                                </span>
                                <span className="text-[10px] font-mono font-bold text-[#006668] bg-[rgba(57,171,173,0.12)] px-2 py-0.5 rounded border border-[#39ABAD]/40 shrink-0">
                                  Page {cite.page} · {cite.clause}
                                </span>
                              </div>

                              <p className="text-[11px] text-[#4A5859] font-mono bg-[#F7F7F8] p-2 rounded border border-[#E2E8E8] leading-normal whitespace-pre-wrap">
                                "{cite.source_text}"
                              </p>

                              <div className="flex justify-end pt-0.5">
                                <button
                                  type="button"
                                  onClick={() => onNavigateToDoc(cite.page, cite)}
                                  className="text-[11px] font-bold text-[#006668] hover:text-[#003339] flex items-center space-x-1 cursor-pointer transition-colors"
                                >
                                  <span>View in Policy Document</span>
                                  <ExternalLink className="w-3 h-3 ml-0.5" />
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}

                <div
                  className={`text-[10px] font-mono ${
                    msg.sender === 'user' ? 'text-slate-300 text-right' : 'text-[#4A5859]'
                  }`}
                >
                  {msg.time}
                </div>
              </div>
            </div>
          ))}

          {isTyping && (
            <div className="flex items-start space-x-3">
              <div className="w-8 h-8 rounded-xl bg-[rgba(57,171,173,0.15)] text-[#006668] border border-[#39ABAD]/40 flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4" />
              </div>
              <div className="p-4 rounded-2xl bg-[#F7F7F8] border border-[#E2E8E8] text-xs text-[#4A5859] flex items-center space-x-2">
                <Loader2 className="w-4 h-4 animate-spin text-[#006668]" />
                <span>Searching policy pages and formulating citation-grounded response...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Form Bar */}
        <div className="p-4 bg-white border-t border-[#E2E8E8] shrink-0">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center space-x-2.5"
          >
            <input
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              placeholder="Ask any policy question (e.g. 'Is knee replacement covered?', 'What is my co-pay?')..."
              className="flex-1 bg-[#F7F7F8] border border-[#E2E8E8] rounded-xl px-4 py-3 text-xs sm:text-sm text-[#003339] placeholder-[#4A5859]/60 focus:outline-hidden focus:border-[#006668] focus:ring-1 focus:ring-[#006668] transition-all"
            />
            <button
              type="submit"
              disabled={!inputQuery.trim() || isTyping}
              className="btn-primary px-5 py-3 text-xs sm:text-sm font-bold flex items-center space-x-1.5 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer shrink-0 shadow-sm"
            >
              <span>Ask</span>
              <Send className="w-3.5 h-3.5 ml-1" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
