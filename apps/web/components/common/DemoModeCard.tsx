'use client';

import { Sparkles, Play, ArrowRight } from 'lucide-react';

interface DemoModeCardProps {
  hasSamplePolicy: boolean;
  samplePolicyId: string | null;
  onLoadDemo: (policyId: string) => void;
}

export function DemoModeCard({ hasSamplePolicy, samplePolicyId, onLoadDemo }: DemoModeCardProps) {
  return (
    <div className="relative overflow-hidden bg-gradient-to-br from-indigo-950/80 to-violet-950/80 border border-indigo-700/50 rounded-2xl p-6 backdrop-blur-sm">
      {/* Background glow */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-600/10 rounded-full blur-2xl pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-24 h-24 bg-violet-600/10 rounded-full blur-2xl pointer-events-none" />

      <div className="relative">
        <div className="flex items-center gap-2 mb-3">
          <div className="p-1.5 bg-indigo-600/80 rounded-lg">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <h3 className="text-base font-bold text-white">Zero-Key Demo</h3>
          <span className="ml-auto px-2 py-0.5 bg-emerald-600/30 border border-emerald-600/40 rounded-full text-xs text-emerald-300 font-medium">
            Ready Now
          </span>
        </div>

        <p className="text-sm text-slate-300 mb-4 leading-relaxed">
          Try the full system with a pre-loaded{' '}
          <strong className="text-white">Star Health MediClassic</strong> policy — no API keys required. 
          Includes real room rent caps, co-payment, and procedure sub-limits.
        </p>

        <div className="space-y-2 mb-5">
          {[
            'Sum Insured: ₹5,00,000',
            'Room Rent: 1% of SI per day (₹5,000)',
            'Co-payment: 10% on admissible amount',
            'Appendectomy Sub-limit: ₹40,000',
          ].map((item) => (
            <div key={item} className="flex items-center gap-2 text-xs text-slate-300">
              <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 shrink-0" />
              {item}
            </div>
          ))}
        </div>

        {hasSamplePolicy && samplePolicyId ? (
          <button
            onClick={() => onLoadDemo(samplePolicyId)}
            className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold rounded-xl transition-all duration-150 shadow-lg shadow-indigo-900/50 hover:shadow-indigo-800/50 group"
          >
            <Play className="w-4 h-4" />
            Load Sample Policy
            <ArrowRight className="w-4 h-4 ml-auto group-hover:translate-x-0.5 transition-transform" />
          </button>
        ) : (
          <div className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-slate-700/60 border border-slate-600/50 text-slate-400 text-sm rounded-xl">
            <div className="w-4 h-4 border-2 border-slate-500/40 border-t-slate-400 rounded-full animate-spin" />
            Checking demo data...
          </div>
        )}
      </div>
    </div>
  );
}
