import React from 'react';
import { FileText, ExternalLink, CheckCircle2 } from 'lucide-react';

export default function EvidenceSection({ onInspectClick }) {
  const sampleEvidences = [
    {
      rule: "Mandatory Co-Payment",
      value: "10% Deduction",
      page: 2,
      clause: "Clause 2.1",
      snippet: "A mandatory co-payment of 10% applies to all eligible claims."
    },
    {
      rule: "Room Rent Limit",
      value: "₹5,000 / day",
      page: 1,
      clause: "Clause 1.2",
      snippet: "Room Rent Limit: Capped at 1% of Sum Insured per day (INR 5,000/day)."
    },
    {
      rule: "Appendectomy Sub-Limit",
      value: "₹90,000 Cap",
      page: 2,
      clause: "Clause 2.3",
      snippet: "Appendectomy & Hernia Procedure Cap: INR 90,000 maximum eligible claim."
    }
  ];

  return (
    <section id="evidence" className="py-16 bg-white border-t border-slate-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        <div className="text-center max-w-2xl mx-auto space-y-3">
          <h2 className="text-3xl font-black text-slate-900 tracking-tight">
            Every Estimate Has Evidence
          </h2>
          <p className="text-sm text-slate-600">
            Important policy rules are linked back to the source document so you can see why they were applied.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {sampleEvidences.map((item, idx) => (
            <div key={idx} className="card-white p-6 space-y-4 flex flex-col justify-between hover:border-emerald-500 transition-all">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-900">{item.rule}</span>
                  <span className="text-xs font-semibold text-emerald-800 bg-emerald-50 px-2.5 py-0.5 rounded border border-emerald-200">
                    Page {item.page} · {item.clause}
                  </span>
                </div>
                <p className="text-sm font-bold text-slate-900 font-mono">{item.value}</p>
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs font-mono text-slate-600 leading-relaxed">
                  "{item.snippet}"
                </div>
              </div>

              <button
                onClick={onInspectClick}
                className="w-full btn-secondary text-xs py-2 flex items-center justify-center space-x-1.5 cursor-pointer"
              >
                <span>Inspect Document Evidence</span>
                <ExternalLink className="w-3.5 h-3.5 text-slate-500" />
              </button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
