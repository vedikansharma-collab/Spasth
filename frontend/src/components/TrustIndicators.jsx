import React from 'react';
import { FileCheck, Stethoscope, Eye, Cpu } from 'lucide-react';

export default function TrustIndicators() {
  const pillars = [
    {
      icon: FileCheck,
      title: "Policy-Grounded",
      description: "Page-level citations for every rule"
    },
    {
      icon: Stethoscope,
      title: "Scenario-Based",
      description: "Localized procedure & city benchmarks"
    },
    {
      icon: Eye,
      title: "Transparent",
      description: "Explicit confidence & uncertainty bounds"
    },
    {
      icon: Cpu,
      title: "Deterministic",
      description: "100% Audited rule-based financial engine"
    }
  ];

  return (
    <section className="py-8 bg-slate-50/60 border-y border-slate-200/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {pillars.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div key={idx} className="flex items-center space-x-3.5 p-3.5 rounded-xl bg-white border border-slate-200/90 shadow-2xs">
                <div className="w-10 h-10 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700 flex-shrink-0">
                  <Icon className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900">{item.title}</h4>
                  <p className="text-xs text-slate-500 font-medium">{item.description}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
