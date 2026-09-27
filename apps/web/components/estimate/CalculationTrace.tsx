'use client';

import type { CalculationTraceStep } from '@policy-estimator/types';
import { useState } from 'react';
import { ChevronDown, ChevronRight, Terminal } from 'lucide-react';

interface CalculationTraceProps {
  trace?: CalculationTraceStep[];
  isLoading: boolean;
}

const STEP_COLORS: Record<string, string> = {
  ALLOWED_ROOM_RENT: 'border-blue-600/40 bg-blue-950/30',
  ROOM_FACTOR: 'border-indigo-600/40 bg-indigo-950/30',
  PROPORTIONATE_COSTS: 'border-violet-600/40 bg-violet-950/30',
  COVERED_ROOM_RENT: 'border-purple-600/40 bg-purple-950/30',
  BASE_LIABILITY: 'border-pink-600/40 bg-pink-950/30',
  DEDUCTIBLE: 'border-orange-600/40 bg-orange-950/30',
  COPAY: 'border-yellow-600/40 bg-yellow-950/30',
  PROCEDURE_SUBLIMIT: 'border-red-600/40 bg-red-950/30',
  FINAL_OOP: 'border-emerald-600/40 bg-emerald-950/30',
};

export function CalculationTrace({ trace, isLoading }: CalculationTraceProps) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set(['FINAL_OOP']));

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-16 bg-slate-800/40 rounded-xl animate-pulse" />
        ))}
      </div>
    );
  }

  if (!trace || trace.length === 0) {
    return (
      <div className="bg-slate-900/60 border border-slate-700/50 rounded-2xl p-8 text-center">
        <Terminal className="w-10 h-10 text-slate-700 mx-auto mb-3" />
        <p className="text-slate-400 text-sm">Run a calculation to see the full 9-step audit trace</p>
      </div>
    );
  }

  const toggle = (step: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(step)) next.delete(step);
      else next.add(step);
      return next;
    });
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 mb-3">
        <Terminal className="w-4 h-4 text-indigo-400" />
        <h3 className="text-sm font-bold text-white">9-Step Calculation Audit Trail</h3>
        <span className="ml-auto text-xs text-slate-500">{trace.length} steps</span>
      </div>

      {trace.map((step, idx) => {
        const isOpen = expanded.has(step.step);
        const colorClass = STEP_COLORS[step.step] || 'border-slate-700/40 bg-slate-900/40';

        return (
          <div
            key={step.step}
            className={`border rounded-xl overflow-hidden transition-all ${colorClass}`}
          >
            <button
              onClick={() => toggle(step.step)}
              className="w-full flex items-center gap-3 p-3.5 text-left hover:bg-white/5 transition-colors"
            >
              <div className="w-6 h-6 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center shrink-0">
                <span className="text-xs font-bold text-slate-400">{idx + 1}</span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-white truncate">{step.title}</p>
                <p className="text-xs text-slate-500 font-mono truncate">{step.formula}</p>
              </div>
              <div className="text-right shrink-0">
                <p className="text-sm font-bold text-indigo-300">
                  {typeof step.result === 'number'
                    ? step.result <= 1 && step.result >= 0 && step.step === 'ROOM_FACTOR'
                      ? step.result.toFixed(4)
                      : `₹${Math.round(step.result).toLocaleString('en-IN')}`
                    : String(step.result)}
                </p>
              </div>
              {isOpen ? (
                <ChevronDown className="w-4 h-4 text-slate-500 shrink-0" />
              ) : (
                <ChevronRight className="w-4 h-4 text-slate-500 shrink-0" />
              )}
            </button>

            {isOpen && (
              <div className="px-4 pb-4 border-t border-white/5">
                {/* Formula */}
                <div className="mt-3 p-3 bg-slate-950/60 rounded-lg font-mono text-xs text-indigo-300 border border-slate-800/60 overflow-x-auto whitespace-pre-wrap">
                  {step.formula}
                </div>

                {/* Inputs */}
                <div className="mt-3">
                  <p className="text-xs font-medium text-slate-500 mb-2">Inputs</p>
                  <div className="grid grid-cols-2 gap-1.5">
                    {Object.entries(step.inputs).map(([key, val]) => (
                      <div key={key} className="flex justify-between text-xs py-1 px-2 bg-slate-800/40 rounded-lg">
                        <span className="text-slate-400 capitalize">{key.replace(/([A-Z])/g, ' $1').trim()}</span>
                        <span className="text-slate-200 font-medium">
                          {typeof val === 'number'
                            ? val <= 1 && val > 0 && key.toLowerCase().includes('factor')
                              ? val.toFixed(4)
                              : `₹${Math.round(val as number).toLocaleString('en-IN')}`
                            : String(val)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Notes */}
                {step.notes && (
                  <div className="mt-3 text-xs text-slate-400 bg-slate-800/30 rounded-lg p-3 leading-relaxed">
                    {step.notes}
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
