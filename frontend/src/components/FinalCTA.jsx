import React from 'react';
import { ArrowRight, ShieldCheck } from 'lucide-react';

export default function FinalCTA({ onAnalyzeClick }) {
  return (
    <section className="py-20 bg-white border-t border-slate-200">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
        <div className="w-14 h-14 rounded-2xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700 mx-auto">
          <ShieldCheck className="w-7 h-7" />
        </div>

        <h2 className="text-3xl sm:text-4xl font-black text-slate-900 tracking-tight max-w-2xl mx-auto">
          Understand Your Coverage Before the Bill Arrives.
        </h2>

        <p className="text-base text-slate-600 max-w-xl mx-auto">
          Turn complex policy language into a transparent treatment-cost estimate grounded with exact document citations.
        </p>

        <div className="pt-2 flex justify-center">
          <button
            onClick={onAnalyzeClick}
            className="btn-primary px-8 py-3.5 text-base font-semibold flex items-center space-x-2 cursor-pointer shadow-md"
          >
            <span>Analyze My Policy</span>
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </div>
    </section>
  );
}
