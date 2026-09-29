import React, { useState, useEffect, useRef } from 'react';
import { Bot, X, Send, Sparkles, User, RefreshCw, HelpCircle } from 'lucide-react';

export default function ChatbotModal({ isOpen, onClose }) {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'bot',
      text: "Hello! I'm your Spasth Policy & Treatment Assistant. Ask me any question about health insurance clauses, out-of-pocket estimation, room rent capping, or co-payments!",
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  if (!isOpen) return null;

  const quickQuestions = [
    "What is a co-payment clause?",
    "How does room rent proportionate deduction work?",
    "How does Spasth estimate out-of-pocket expense?",
    "What documents should I upload for analysis?"
  ];

  const getKnowledgeResponse = (query) => {
    const q = query.toLowerCase();
    
    if (q.includes('co-pay') || q.includes('copay') || q.includes('co-payment')) {
      return "A mandatory **Co-payment** (Co-pay) is a fixed percentage of total admissible medical claims that the insured policyholder must pay out of pocket before insurance pays the remaining balance. For example, a 10% co-pay on a ₹1,00,000 admissible claim means you pay ₹10,000 and the insurer covers ₹90,000.";
    }

    if (q.includes('room rent') || q.includes('proportionate') || q.includes('deluxe') || q.includes('cap')) {
      return "If you select a room category higher than your policy limit (e.g. Deluxe Room when your policy caps room rent at ₹5,000/day for Standard Room), insurers apply a **Proportionate Deduction Penalty**. This reduces claim coverage for associated hospital fees (nursing, doctor visits, surgery room charges) proportionally by the room tariff difference!";
    }

    if (q.includes('spasth') || q.includes('estimate') || q.includes('calculate') || q.includes('out-of-pocket')) {
      return "**Spasth** combines AI policy contract extraction (Sum Insured, Co-pay, Room Caps, Sub-limits) with localized city-based hospital package cost benchmarks. Our deterministic rule engine calculates the exact range of insurance coverage and patient out-of-pocket liability with exact page citations.";
    }

    if (q.includes('upload') || q.includes('pdf') || q.includes('document') || q.includes('policy')) {
      return "You can drag & drop any health insurance policy schedule or wordings document (PDF format) into the **Policy Analyzer**. Spasth preserves document page indexing so every rule is cited with exact page numbers!";
    }

    if (q.includes('sub-limit') || q.includes('disease limit') || q.includes('capping')) {
      return "**Procedure Sub-limits** specify maximum payout limits set by your insurance policy for specific treatments (e.g. Cataract ₹40,000, Appendectomy ₹60,000). Claims beyond the sub-limit must be paid out-of-pocket.";
    }

    return `Thank you for asking: "${query}". Spasth analyzes your policy documents to extract Sum Insured, Co-payment %, Room Rent caps, and procedure sub-limits, applying them against localized hospital benchmark pricing. You can test your policy by selecting a procedure, city, and room type above!`;
  };

  const handleSend = (textToSend) => {
    const query = textToSend || inputQuery;
    if (!query.trim()) return;

    const userMsg = {
      id: Date.now(),
      sender: 'user',
      text: query.trim(),
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputQuery('');
    setIsTyping(true);

    setTimeout(() => {
      const replyText = getKnowledgeResponse(query);
      const botMsg = {
        id: Date.now() + 1,
        sender: 'bot',
        text: replyText,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, botMsg]);
      setIsTyping(false);
    }, 700);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 sm:p-6 animate-in fade-in duration-200">
      <div className="bg-white w-full max-w-2xl rounded-2xl shadow-2xl border border-slate-200 flex flex-col h-[600px] max-h-[90vh] overflow-hidden">
        
        {/* Header */}
        <div className="bg-[#003339] text-white p-4 sm:p-5 flex items-center justify-between shrink-0">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-[#39ABAD]/20 border border-[#39ABAD]/40 flex items-center justify-center text-[#73FFFF]">
              <Bot className="w-6 h-6 text-[#73FFFF]" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="font-heading font-extrabold text-lg text-white">Spasth Policy Assistant</h3>
                <span className="px-2 py-0.5 text-[9px] font-bold tracking-wider uppercase bg-[#39ABAD]/30 text-[#73FFFF] rounded-full border border-[#39ABAD]/50">
                  AI Grounded
                </span>
              </div>
              <p className="text-xs text-slate-300">Ask any policy query or out-of-pocket question</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-300 hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
            aria-label="Close Assistant"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Chat Messages Body */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-4 bg-slate-50/50">
          
          {/* Quick Question Chips */}
          <div className="space-y-2 pb-2 border-b border-slate-200/60">
            <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-500">
              <HelpCircle className="w-3.5 h-3.5 text-emerald-600" />
              <span>Suggested Queries:</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {quickQuestions.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(q)}
                  className="text-xs px-3 py-1.5 rounded-full bg-white border border-slate-200 text-slate-700 hover:border-emerald-500 hover:text-emerald-700 hover:bg-emerald-50/60 transition-all cursor-pointer font-medium shadow-2xs"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>

          {/* Messages */}
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex items-start space-x-2.5 ${
                msg.sender === 'user' ? 'flex-row-reverse space-x-reverse' : 'flex-row'
              }`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                  msg.sender === 'user'
                    ? 'bg-slate-800 text-white'
                    : 'bg-emerald-600 text-white'
                }`}
              >
                {msg.sender === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              <div
                className={`max-w-[82%] rounded-2xl px-4 py-3 text-xs leading-relaxed ${
                  msg.sender === 'user'
                    ? 'bg-[#003339] text-white rounded-tr-none'
                    : 'bg-white border border-slate-200 text-slate-800 shadow-2xs rounded-tl-none'
                }`}
              >
                <div className="whitespace-pre-wrap">{msg.text}</div>
                <div
                  className={`text-[9px] mt-1.5 font-mono ${
                    msg.sender === 'user' ? 'text-slate-300 text-right' : 'text-slate-400'
                  }`}
                >
                  {msg.time}
                </div>
              </div>
            </div>
          ))}

          {isTyping && (
            <div className="flex items-center space-x-2 text-xs text-slate-500 pt-1">
              <div className="w-7 h-7 rounded-full bg-emerald-600 text-white flex items-center justify-center">
                <Bot className="w-3.5 h-3.5" />
              </div>
              <div className="bg-white border border-slate-200 rounded-2xl px-4 py-2 flex items-center space-x-1.5">
                <RefreshCw className="w-3.5 h-3.5 animate-spin text-emerald-600" />
                <span>Spasth Assistant is formulating reply...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-3 sm:p-4 bg-white border-t border-slate-200 shrink-0">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center space-x-2"
          >
            <input
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              placeholder="Ask any health policy or treatment cost query..."
              className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-900 focus:outline-hidden focus:border-emerald-600 focus:ring-1 focus:ring-emerald-600 transition-all"
            />
            <button
              type="submit"
              disabled={!inputQuery.trim() || isTyping}
              className="btn-primary px-4 py-2.5 text-xs font-bold flex items-center space-x-1.5 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              <span>Send</span>
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>

      </div>
    </div>
  );
}
