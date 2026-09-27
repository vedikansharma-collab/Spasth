'use client';

import { Loader2, Brain, FileSearch, CheckCircle } from 'lucide-react';

interface ProcessingStatusProps {
  status: string;
}

const STEPS = [
  { key: 'UPLOADING', label: 'Uploading', icon: FileSearch, desc: 'Receiving PDF document' },
  { key: 'PARSING', label: 'Parsing', icon: FileSearch, desc: 'Extracting text from pages' },
  { key: 'EXTRACTING', label: 'AI Extraction', icon: Brain, desc: 'LLM analyzing policy clauses' },
  { key: 'VALIDATING', label: 'Validating', icon: CheckCircle, desc: 'Verifying extracted rules' },
];

export function ProcessingStatus({ status }: ProcessingStatusProps) {
  const currentIndex = STEPS.findIndex((s) => s.key === status);

  return (
    <div className="bg-slate-900/60 border border-indigo-700/40 rounded-2xl p-6 backdrop-blur-sm">
      <div className="flex items-center gap-3 mb-5">
        <div className="w-10 h-10 bg-indigo-600/80 rounded-xl flex items-center justify-center">
          <Loader2 className="w-5 h-5 text-white animate-spin" />
        </div>
        <div>
          <h3 className="text-base font-bold text-white">Processing Policy</h3>
          <p className="text-sm text-slate-400">Running AI extraction pipeline...</p>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-3">
        {STEPS.map((step, idx) => {
          const Icon = step.icon;
          const completed = idx < currentIndex;
          const active = idx === currentIndex;
          return (
            <div key={step.key} className="text-center">
              <div
                className={`w-10 h-10 rounded-xl flex items-center justify-center mx-auto mb-2 transition-all ${
                  completed
                    ? 'bg-emerald-600'
                    : active
                    ? 'bg-indigo-600 ring-4 ring-indigo-500/30 animate-pulse'
                    : 'bg-slate-800 border border-slate-700'
                }`}
              >
                {completed ? (
                  <CheckCircle className="w-5 h-5 text-white" />
                ) : active ? (
                  <Loader2 className="w-5 h-5 text-white animate-spin" />
                ) : (
                  <Icon className="w-5 h-5 text-slate-600" />
                )}
              </div>
              <p className={`text-xs font-medium ${active ? 'text-white' : completed ? 'text-emerald-400' : 'text-slate-600'}`}>
                {step.label}
              </p>
              <p className="text-xs text-slate-500 mt-0.5 hidden sm:block">{step.desc}</p>
            </div>
          );
        })}
      </div>

      <div className="mt-5 h-1.5 bg-slate-800 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-indigo-600 to-violet-500 rounded-full transition-all duration-700"
          style={{ width: `${Math.max(10, ((currentIndex + 1) / STEPS.length) * 100)}%` }}
        />
      </div>
    </div>
  );
}
