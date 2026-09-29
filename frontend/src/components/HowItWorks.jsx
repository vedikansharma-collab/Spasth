import React from 'react';
import { UploadCloud, Search, Sliders, Calculator } from 'lucide-react';

export default function HowItWorks() {
  const steps = [
    {
      num: "01",
      icon: UploadCloud,
      title: "Upload Policy",
      description: "Upload your health insurance policy PDF document."
    },
    {
      num: "02",
      icon: Search,
      title: "Understand Coverage",
      description: "Relevant coverage rules are extracted and linked to their exact source page."
    },
    {
      num: "03",
      icon: Sliders,
      title: "Add Treatment Scenario",
      description: "Choose your medical procedure, city location, and hospital room category."
    },
    {
      num: "04",
      icon: Calculator,
      title: "Estimate Your Cost",
      description: "Policy rules and treatment-cost benchmarks combine to calculate your out-of-pocket liability."
    }
  ];

  return (
    <section id="how-it-works" className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        <div className="text-center max-w-3xl mx-auto space-y-3">
          <h2 className="text-3xl sm:text-4xl font-black text-slate-900 tracking-tight">
            From Policy Language to Treatment Cost
          </h2>
          <p className="text-base text-slate-600 font-normal">
            Spasth converts dense legal contracts into deterministic financial estimates grounded with document citations.
          </p>
        </div>

        {/* 4 Cards Grid with Desktop Connecting Line */}
        <div className="relative">
          {/* Subtle connecting line for desktop */}
          <div className="hidden lg:block absolute top-1/2 left-12 right-12 h-0.5 bg-slate-200 -translate-y-6 z-0"></div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 relative z-10">
            {steps.map((step, idx) => {
              const Icon = step.icon;
              return (
                <div key={idx} className="card-white p-6 space-y-4 relative flex flex-col justify-between">
                  <div className="flex items-center justify-between">
                    <span className="text-2xl font-black font-mono text-emerald-600/40">{step.num}</span>
                    <div className="w-10 h-10 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700">
                      <Icon className="w-5 h-5" />
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <h3 className="text-lg font-bold text-slate-900">{step.title}</h3>
                    <p className="text-xs text-slate-600 leading-relaxed font-normal">{step.description}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
