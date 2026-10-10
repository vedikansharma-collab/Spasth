import React, { useState, useEffect } from 'react';
import { 
  FileText, Search, BookOpen, Eye, ArrowLeft, 
  Layers, CheckCircle2, ShieldCheck 
} from 'lucide-react';

export default function PolicyDocumentView({ 
  activePolicyId, 
  activePolicy, 
  targetPage = 1, 
  targetCitation = null, 
  onReturnToAssistant, 
  onReturnToEstimator,
  onSelectPolicy,
  policies = []
}) {
  const [selectedPageNum, setSelectedPageNum] = useState(targetPage || 1);
  const [searchTerm, setSearchTerm] = useState('');

  // Update selected page when targetPage changes from citation navigation
  useEffect(() => {
    if (targetPage) {
      setSelectedPageNum(targetPage);
    }
  }, [targetPage]);

  // 1. Empty State: No policy active
  if (!activePolicyId || !activePolicy) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 space-y-8 animate-fade-in">
        <div className="card-white p-8 sm:p-10 text-center space-y-6 border-slate-200">
          <div className="w-16 h-16 rounded-2xl bg-[rgba(57,171,173,0.12)] border border-[#39ABAD]/40 flex items-center justify-center text-[#006668] mx-auto shadow-sm">
            <BookOpen className="w-8 h-8" />
          </div>

          <div className="max-w-md mx-auto space-y-2">
            <h2 className="text-2xl font-black text-[#003339] tracking-tight">No Policy Document Open</h2>
            <p className="text-sm text-[#4A5859] leading-relaxed">
              Upload a policy PDF or choose an indexed document to view preserved page text, clauses, and citation evidence.
            </p>
          </div>

          {policies.length > 0 && (
            <div className="pt-4 max-w-lg mx-auto space-y-3 text-left">
              <span className="text-xs font-bold uppercase tracking-wider text-[#4A5859] block">
                Select an Indexed Policy:
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
                      Inspect &rarr;
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

  const pages = activePolicy.pages || [];
  const rules = activePolicy.rules || [];
  const activePage = pages.find((p) => p.page_number === selectedPageNum) || pages[0];

  // Rules matching the current page
  const pageRules = rules.filter((r) => r.page === selectedPageNum);

  const filteredLines = activePage?.content
    ? activePage.content.split('\n').filter((line) => {
        if (!searchTerm) return true;
        return line.toLowerCase().includes(searchTerm.toLowerCase());
      })
    : [];

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-6 animate-fade-in">
      {/* Target Citation Return Banner (if arrived from citation link) */}
      {targetCitation && (
        <div className="p-4 rounded-2xl bg-[rgba(57,171,173,0.12)] border border-[#39ABAD] flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
          <div className="flex items-start space-x-3">
            <div className="p-2 rounded-xl bg-white border border-[#39ABAD]/40 text-[#006668] shrink-0">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-bold text-[#003339]">Inspecting Cited Evidence:</span>
                <span className="text-[10px] font-mono font-bold bg-[#006668] text-white px-2 py-0.5 rounded">
                  Page {targetCitation.page} · {targetCitation.clause}
                </span>
              </div>
              <p className="text-xs text-[#4A5859] mt-0.5 font-mono">
                "{targetCitation.source_text || targetCitation.rule}"
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2 shrink-0">
            {onReturnToAssistant && (
              <button
                onClick={onReturnToAssistant}
                className="btn-secondary px-3 py-1.5 text-xs font-bold flex items-center space-x-1 cursor-pointer"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Return to Assistant</span>
              </button>
            )}
            {onReturnToEstimator && (
              <button
                onClick={onReturnToEstimator}
                className="btn-secondary px-3 py-1.5 text-xs font-bold flex items-center space-x-1 cursor-pointer"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Return to Estimator</span>
              </button>
            )}
          </div>
        </div>
      )}

      {/* Document Overview Header */}
      <div className="card-white p-5 sm:p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 border-[#E2E8E8]">
        <div className="flex items-center space-x-3.5">
          <div className="w-12 h-12 rounded-xl bg-[#003339] flex items-center justify-center text-[#73FFFF] shadow-xs shrink-0">
            <FileText className="w-6 h-6 text-[#73FFFF]" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-xl font-black text-[#003339] tracking-tight">{activePolicy.original_filename}</h2>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 uppercase tracking-wide">
                1-Indexed Pages
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-3 text-xs text-[#4A5859] mt-1 font-mono">
              <span>{pages.length} Pages Preserved</span>
              <span>•</span>
              <span>{(activePolicy.file_size_bytes / 1024).toFixed(1)} KB</span>
              <span>•</span>
              <span>Uploaded {new Date(activePolicy.uploaded_at).toLocaleDateString()}</span>
            </div>
          </div>
        </div>

        {/* Search Input */}
        <div className="relative w-full md:w-64">
          <Search className="w-4 h-4 text-[#4A5859] absolute left-3.5 top-3" />
          <input
            type="text"
            placeholder="Search page content..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-[#F7F7F8] border border-[#E2E8E8] text-xs text-[#003339] placeholder-[#4A5859]/60 focus:outline-hidden focus:border-[#006668] transition-all"
          />
        </div>
      </div>

      {/* Main Document Viewer Container */}
      <div className="card-white rounded-2xl overflow-hidden border border-[#E2E8E8] shadow-sm flex flex-col md:flex-row">
        {/* Left Sidebar: 1-Indexed Page Tabs */}
        <div className="w-full md:w-64 bg-[#F7F7F8] border-b md:border-b-0 md:border-r border-[#E2E8E8] p-4 space-y-3 shrink-0">
          <div className="flex items-center justify-between pb-2 border-b border-[#E2E8E8]">
            <span className="text-xs font-bold uppercase tracking-wider text-[#003339] flex items-center space-x-1.5">
              <Layers className="w-3.5 h-3.5 text-[#006668]" />
              <span>Document Pages</span>
            </span>
            <span className="text-[10px] font-mono text-[#4A5859] font-bold">
              {pages.length} Total
            </span>
          </div>

          <div className="flex md:flex-col gap-2 overflow-x-auto md:overflow-y-auto max-h-[600px] pb-2 md:pb-0">
            {pages.map((p) => {
              const hasRule = rules.some((r) => r.page === p.page_number);
              const isSelected = selectedPageNum === p.page_number;

              return (
                <button
                  key={p.page_number}
                  onClick={() => setSelectedPageNum(p.page_number)}
                  className={`p-3 rounded-xl text-left transition-all cursor-pointer flex items-center justify-between shrink-0 md:shrink md:w-full border ${
                    isSelected
                      ? 'bg-[#006668] text-white border-[#006668] shadow-2xs'
                      : 'bg-white hover:bg-slate-100 text-[#003339] border-[#E2E8E8]'
                  }`}
                >
                  <div className="flex items-center space-x-2.5">
                    <span className={`w-6 h-6 rounded-lg text-xs font-mono font-bold flex items-center justify-center ${
                      isSelected ? 'bg-white/20 text-white' : 'bg-[#F7F7F8] text-[#006668]'
                    }`}>
                      {p.page_number}
                    </span>
                    <div>
                      <p className={`text-xs font-bold ${isSelected ? 'text-white' : 'text-[#003339]'}`}>
                        Page {p.page_number}
                      </p>
                      <p className={`text-[10px] font-mono ${isSelected ? 'text-white/80' : 'text-[#4A5859]'}`}>
                        {p.word_count} words
                      </p>
                    </div>
                  </div>

                  {hasRule && (
                    <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider ${
                      isSelected ? 'bg-white text-[#006668]' : 'bg-[rgba(57,171,173,0.15)] text-[#006668]'
                    }`}>
                      Grounded
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Right Content Area: Page Content & Grounded Clauses */}
        <div className="flex-1 p-5 sm:p-6 space-y-5 bg-white overflow-y-auto max-h-[700px]">
          {/* Active Page Header Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-[#E2E8E8]">
            <div className="flex items-center space-x-2">
              <Eye className="w-4 h-4 text-[#006668]" />
              <h3 className="font-bold text-[#003339] text-sm">
                Viewing Page {activePage?.page_number} Text
              </h3>
              <span className="text-[11px] font-mono text-[#4A5859]">
                ({activePage?.word_count || 0} words • {activePage?.char_count || 0} characters)
              </span>
            </div>

            {pageRules.length > 0 && (
              <div className="flex items-center space-x-2">
                <span className="text-xs font-semibold text-[#006668]">
                  {pageRules.length} Grounded {pageRules.length === 1 ? 'Clause' : 'Clauses'} on this page
                </span>
              </div>
            )}
          </div>

          {/* Clauses Extracted on this Page */}
          {pageRules.length > 0 && (
            <div className="p-4 rounded-xl bg-[rgba(57,171,173,0.08)] border border-[#39ABAD]/40 space-y-2.5">
              <span className="text-xs font-bold text-[#003339] flex items-center space-x-1.5">
                <CheckCircle2 className="w-4 h-4 text-[#006668]" />
                <span>Extracted Policy Rules on Page {selectedPageNum}:</span>
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {pageRules.map((r, rIdx) => (
                  <div key={rIdx} className="p-2.5 rounded-lg bg-white border border-[#E2E8E8] text-xs space-y-1">
                    <div className="flex items-center justify-between">
                      <strong className="text-[#003339]">{r.rule_key || r.rule_type}</strong>
                      <span className="font-mono text-[10px] text-[#006668] font-bold">Clause {r.clause || 'N/A'}</span>
                    </div>
                    <p className="font-mono text-[11px] text-[#4A5859] truncate">"{r.source_text}"</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Page Text Reader (Preserved text with 1-indexed line numbers) */}
          <div className="rounded-xl border border-[#E2E8E8] bg-[#F7F7F8] p-4 sm:p-5 font-mono text-xs text-[#003339] leading-relaxed select-text space-y-1">
            {filteredLines.length > 0 ? (
              filteredLines.map((line, lIdx) => (
                <div key={lIdx} className="flex items-start space-x-3 py-0.5 hover:bg-white/80 px-1.5 rounded">
                  <span className="text-[10px] text-[#4A5859]/50 select-none w-8 text-right shrink-0">
                    {lIdx + 1}
                  </span>
                  <span className="whitespace-pre-wrap break-words flex-1">
                    {line || <span className="opacity-0">empty line</span>}
                  </span>
                </div>
              ))
            ) : (
              <div className="py-8 text-center text-[#4A5859] italic">
                No matching lines found on Page {selectedPageNum} for "{searchTerm}".
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
