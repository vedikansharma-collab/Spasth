import React from 'react';
import { CheckCircle2, AlertCircle, AlertTriangle, ShieldCheck } from 'lucide-react';

export default function ConfidenceSection() {
  const levels = [
    {
      level: "HIGH",
      badgeClass: "bg-emerald-50 text-emerald-800 border-emerald-300",
      dotColor: "bg-emerald-600",
      icon: CheckCircle2,
      description: "Required policy rules were found with page citations and matched to the verified procedure benchmark."
    },
    {
      level: "MEDIUM",
      badgeClass: "bg-amber-50 text-amber-800 border-amber-300",
      dotColor: "bg-amber-600",
      icon: AlertCircle,
      description: "Some information is approximate or room upgrade penalties apply, requiring verification."
    },
    {
      level: "LOW",
      badgeClass: "bg-rose-50 text-rose-800 border-rose-300",
      dotColor: "bg-rose-600",
      icon: AlertTriangle,
      description: "Important policy rules or hospital benchmark cost data are missing or ambiguous."
    }
  ];

  return (
    <section className="py-16 bg-white border-t border-slate-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        <div className="text-center max-w-2xl mx-auto space-y-3">
          <h2 className="text-3xl font-black text-slate-900 tracking-tight">
            Know What We Know — And What We Don't
          </h2>
          <p className="text-sm text-slate-600">
            Spasth provides deterministic confidence scoring based on document grounding and pricing benchmarks.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {levels.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div key={idx} className="card-white p-6 space-y-3 flex flex-col justify-between">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold border ${item.badgeClass}`}>
                      <span className={`w-2 h-2 rounded-full ${item.dotColor}`}></span>
                      <span>{item.level} CONFIDENCE</span>
                    </span>
                    <Icon className="w-4 h-4 text-slate-400" />
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed font-normal">{item.description}</p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Structured Uncertainty State Callout */}
        <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-2 text-xs">
          <div className="flex items-center space-x-2 text-slate-900 font-bold text-sm">
            <AlertCircle className="w-4 h-4 text-amber-600" />
            <span>Structured Uncertainty Handling</span>
          </div>
          <p className="text-slate-600 leading-relaxed">
            If required policy clauses or benchmark cost datasets are missing, Spasth displays <strong>"Unable to confidently estimate"</strong> rather than returning misleading numbers or guessing values.
          </p>
        </div>
      </div>
    </section>
  );
}
