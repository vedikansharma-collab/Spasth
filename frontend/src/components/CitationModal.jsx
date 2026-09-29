import React from 'react';
import { X, FileText, CheckCircle2 } from 'lucide-react';

export default function CitationModal({ citation, isOpen, onClose }) {
  if (!isOpen || !citation) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs animate-fade-in">
      <div 
        className="card-white max-w-lg w-full p-6 space-y-4 shadow-2xl relative border-slate-200"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 text-base">Policy Evidence Citation</h3>
              <p className="text-xs text-slate-500">Verified document grounding</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-slate-100 text-slate-500 hover:text-slate-900 hover:bg-slate-200 transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Citation Metadata Badges */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
            <span className="text-[11px] text-slate-500 uppercase tracking-wider block font-semibold">Page Location</span>
            <span className="text-sm font-bold text-slate-900 font-mono">Page {citation.page}</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
            <span className="text-[11px] text-slate-500 uppercase tracking-wider block font-semibold">Section / Clause</span>
            <span className="text-sm font-bold text-emerald-800 font-mono">{citation.clause}</span>
          </div>
        </div>

        {/* Applied Rule Detail */}
        <div className="space-y-1.5">
          <span className="text-xs font-semibold text-slate-700">Policy Parameter:</span>
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs font-bold text-slate-900 flex justify-between items-center">
            <span>{citation.rule}</span>
            <span className="text-emerald-800 font-mono text-[11px]">{citation.details}</span>
          </div>
        </div>

        {/* Source Text Snippet */}
        <div className="space-y-1.5">
          <span className="text-xs font-semibold text-slate-700">Exact Extracted Source Text:</span>
          <div className="p-3.5 rounded-xl bg-slate-900 text-slate-200 font-mono text-xs leading-relaxed max-h-44 overflow-y-auto whitespace-pre-wrap select-text">
            "{citation.source_text}"
          </div>
        </div>

        {/* Footer Audit Guarantee */}
        <div className="pt-2 flex items-center justify-between text-[11px] text-slate-500 border-t border-slate-100">
          <span className="flex items-center space-x-1 text-emerald-700 font-medium">
            <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
            100% Page Citation Grounding
          </span>
          <button
            onClick={onClose}
            className="btn-primary px-4 py-1.5 text-xs cursor-pointer"
          >
            Close Citation
          </button>
        </div>
      </div>
    </div>
  );
}
