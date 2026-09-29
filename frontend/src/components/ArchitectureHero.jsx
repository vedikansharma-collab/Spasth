import React from 'react';
import { Shield, FileText, Stethoscope, Calculator, CheckCircle2, ArrowRight, Sparkles, Scale, Lock } from 'lucide-react';

export default function ArchitectureHero() {
  return (
    <div className="glass-card rounded-3xl p-6 sm:p-10 border border-slate-700/60 relative overflow-hidden bg-gradient-to-br from-slate-900/95 via-slate-900/85 to-slate-950 shadow-2xl">
      {/* Background Glow Accents */}
      <div className="absolute top-0 right-1/4 w-96 h-40 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-0 left-1/3 w-80 h-32 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none"></div>

      <div className="max-w-4xl space-y-5">
        <div className="inline-flex items-center space-x-2 px-3.5 py-1 rounded-full bg-cyan-950/90 border border-cyan-700/80 text-cyan-300 text-xs font-bold uppercase tracking-widest shadow-md">
          <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
          <span>AI Policy Intelligence Platform</span>
        </div>

        <h1 className="text-3xl sm:text-5xl font-heading font-black text-white tracking-tight leading-tight">
          From Policy Language to <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-sky-300 to-indigo-400">Treatment Cost</span>
        </h1>

        <p className="text-sm sm:text-base text-slate-300 leading-relaxed max-w-2xl font-normal">
          Predict out-of-pocket medical expenses by fusing complex health insurance policies with localized healthcare pricing benchmarks using LLM document intelligence and deterministic financial engines.
        </p>

        {/* 4-Step Interactive Progress Pipeline */}
        <div className="pt-4 grid grid-cols-1 sm:grid-cols-4 gap-3.5">
          <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800 hover:border-cyan-500/50 transition-all space-y-1.5 group">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-cyan-400">Step 1</span>
              <FileText className="w-4 h-4 text-slate-400 group-hover:text-cyan-400 transition-colors" />
            </div>
            <p className="text-sm font-heading font-bold text-white">Upload Policy</p>
            <p className="text-[11px] text-slate-400">PyMuPDF 1-indexed page parser</p>
          </div>

          <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800 hover:border-sky-500/50 transition-all space-y-1.5 group">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-sky-400">Step 2</span>
              <Stethoscope className="w-4 h-4 text-slate-400 group-hover:text-sky-400 transition-colors" />
            </div>
            <p className="text-sm font-heading font-bold text-white">Coverage Rules</p>
            <p className="text-[11px] text-slate-400">Gemini RAG rule extraction</p>
          </div>

          <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800 hover:border-indigo-500/50 transition-all space-y-1.5 group">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-indigo-400">Step 3</span>
              <Calculator className="w-4 h-4 text-slate-400 group-hover:text-indigo-400 transition-colors" />
            </div>
            <p className="text-sm font-heading font-bold text-white">Treatment Scenario</p>
            <p className="text-[11px] text-slate-400">Procedure, City, Room Cap</p>
          </div>

          <div className="p-4 rounded-2xl bg-gradient-to-br from-emerald-950/60 to-slate-900 border border-emerald-500/50 hover:border-emerald-400 transition-all space-y-1.5 group shadow-lg shadow-emerald-950/30">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-emerald-400">Step 4</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            </div>
            <p className="text-sm font-heading font-bold text-white">Out-of-Pocket</p>
            <p className="text-[11px] text-emerald-300/80 font-medium">Page Citations + Confidence</p>
          </div>
        </div>
      </div>
    </div>
  );
}
