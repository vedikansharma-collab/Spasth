import React from 'react';
import { FileText, Stethoscope, Calculator, ShieldCheck } from 'lucide-react';

export default function WhyFin01Section() {
  const pillars = [
    {
      icon: FileText,
      title: "Policy Understanding",
      description: "Extract structured coverage rules, caps, room rent limits, and co-payment clauses with page-level source citations."
    },
    {
      icon: Stethoscope,
      title: "Treatment Context",
      description: "Apply policy coverage rules to a specific treatment scenario considering hospital procedure, city tier, and room type."
    },
    {
      icon: Calculator,
      title: "Cost Estimation",
      description: "Combine policy rules with localized healthcare package pricing benchmarks using a deterministic calculation engine."
    }
  ];

  return (
    <section id="why-spasth" className="py-20 bg-offwhite border-t border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        <div className="text-center max-w-3xl mx-auto space-y-3">
          <h2 className="text-3xl sm:text-4xl font-black text-slate-900 tracking-tight">
            More Than a Policy Chatbot
          </h2>
          <p className="text-base text-slate-600">
            Spasth goes beyond conversational QA by providing audited, citation-backed financial calculations.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {pillars.map((col, idx) => {
            const Icon = col.icon;
            return (
              <div key={idx} className="card-white p-7 space-y-4 flex flex-col justify-between hover:border-emerald-600 transition-all">
                <div className="space-y-3">
                  <div className="w-12 h-12 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700">
                    <Icon className="w-6 h-6" />
                  </div>
                  <h3 className="text-lg font-bold text-slate-900">{col.title}</h3>
                  <p className="text-xs text-slate-600 leading-relaxed">{col.description}</p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Bottom Statement Callout */}
        <div className="card-accent p-6 text-center max-w-3xl mx-auto border-emerald-300">
          <p className="text-base font-bold text-emerald-950 flex items-center justify-center space-x-2">
            <ShieldCheck className="w-5 h-5 text-emerald-700 flex-shrink-0" />
            <span>Spasth connects policy language with the real-world treatment scenario.</span>
          </p>
        </div>
      </div>
    </section>
  );
}
