import React from 'react';
import { Shield, Mail, Users, FileText, Activity, ChevronRight, Sparkles } from 'lucide-react';

export default function Footer() {
  const scrollToSection = (id) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const contacts = [
    { name: "Tanishq Suryawanshi", email: "tanishq.suryawanshi25@pccoepune.org" },
    { name: "Krushna Bagul", email: "krushna.bagul25@pccoepune.org" },
    { name: "Vedika Sharma", email: "vedika.sharma25@pccoepune.org" },
    { name: "Tanishqa Khare", email: "tanishqa.khare@pccoepune.org" }
  ];

  return (
    <footer className="bg-slate-950 text-slate-300 pt-16 pb-12 relative overflow-hidden">
      {/* Background glow effects for premium aesthetic without explicit top borders */}
      <div className="absolute top-0 left-1/4 w-96 h-32 bg-emerald-500/5 blur-[100px] pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-96 h-32 bg-cyan-500/5 blur-[100px] pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12 relative z-10">
        
        {/* Main 4 Vertical Columns Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-10 lg:gap-12">
          
          {/* Vertical Column 1: Brand & Platform Intelligence */}
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-xl bg-emerald-600/90 flex items-center justify-center text-white shadow-lg shadow-emerald-900/30">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <div className="flex items-center space-x-2">
                <span className="font-heading font-black text-2xl text-white tracking-tight">Spasth</span>
                <span className="px-2 py-0.5 text-[9px] font-bold tracking-wider uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full">
                  v1.0 AI
                </span>
              </div>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed">
              <strong>Spasth</strong> bridges the gap between complex health insurance contracts and actual hospital bill totals. We combine intelligent document extraction, clause rule parsing, and an audited financial calculation engine to deliver evidence-backed out-of-pocket estimates.
            </p>

            <div className="pt-2 flex items-center space-x-2 text-[11px] font-semibold text-emerald-400/90">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Grounded Policy Intelligence</span>
            </div>
          </div>

          {/* Vertical Column 2: Platform Capabilities (Briefly Explained) */}
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
                <Activity className="w-4 h-4 text-emerald-400" />
                <span>Capabilities</span>
              </h3>
              <p className="text-[11px] text-slate-400 mt-1">
                Deterministic calculation grounded in contract clauses.
              </p>
            </div>

            <ul className="space-y-3 text-xs text-slate-400">
              <li className="space-y-0.5">
                <div className="font-semibold text-slate-200 flex items-center space-x-1.5">
                  <ChevronRight className="w-3 h-3 text-emerald-400 shrink-0" />
                  <span>Clause Rule Extraction</span>
                </div>
                <p className="text-[11px] text-slate-400 pl-4">
                  Extracts sum insured, co-pay, room rent limits, and sub-limits.
                </p>
              </li>

              <li className="space-y-0.5">
                <div className="font-semibold text-slate-200 flex items-center space-x-1.5">
                  <ChevronRight className="w-3 h-3 text-emerald-400 shrink-0" />
                  <span>Hospital Cost Benchmarking</span>
                </div>
                <p className="text-[11px] text-slate-400 pl-4">
                  Localized pricing datasets across Indian metros and cities.
                </p>
              </li>

              <li className="space-y-0.5">
                <div className="font-semibold text-slate-200 flex items-center space-x-1.5">
                  <ChevronRight className="w-3 h-3 text-emerald-400 shrink-0" />
                  <span>Proportionate Deduction Penalty</span>
                </div>
                <p className="text-[11px] text-slate-400 pl-4">
                  Calculates room upgrade penalties dynamically on associated costs.
                </p>
              </li>
            </ul>
          </div>

          {/* Vertical Column 3: Navigation & Quick Links */}
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
                <FileText className="w-4 h-4 text-emerald-400" />
                <span>Navigation</span>
              </h3>
              <p className="text-[11px] text-slate-400 mt-1">
                Direct access to core dashboard modules.
              </p>
            </div>

            <nav className="flex flex-col space-y-2 text-xs font-medium text-slate-300">
              <button 
                onClick={() => scrollToSection('how-it-works')} 
                className="flex items-center space-x-2 hover:text-emerald-400 transition-colors cursor-pointer text-left py-1"
              >
                <ChevronRight className="w-3 h-3 text-slate-400" />
                <span>How It Works</span>
              </button>

              <button 
                onClick={() => scrollToSection('estimator')} 
                className="flex items-center space-x-2 hover:text-emerald-400 transition-colors cursor-pointer text-left py-1"
              >
                <ChevronRight className="w-3 h-3 text-slate-400" />
                <span>Treatment Cost Estimator</span>
              </button>

              <button 
                onClick={() => scrollToSection('evidence')} 
                className="flex items-center space-x-2 hover:text-emerald-400 transition-colors cursor-pointer text-left py-1"
              >
                <ChevronRight className="w-3 h-3 text-slate-400" />
                <span>Policy Evidence & Citations</span>
              </button>

              <button 
                onClick={() => scrollToSection('why-spasth')} 
                className="flex items-center space-x-2 hover:text-emerald-400 transition-colors cursor-pointer text-left py-1"
              >
                <ChevronRight className="w-3 h-3 text-slate-400" />
                <span>Why Spasth Architecture</span>
              </button>
            </nav>
          </div>

          {/* Vertical Column 4 (LAST SECTION): Contacts */}
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
                <Users className="w-4 h-4 text-emerald-400" />
                <span>Contacts</span>
              </h3>
              <p className="text-[11px] text-slate-400 mt-1">
                Direct contact details for inquiries.
              </p>
            </div>

            <div className="space-y-2.5">
              {contacts.map((contact, idx) => (
                <a
                  key={idx}
                  href={`mailto:${contact.email}`}
                  className="group block p-2.5 rounded-xl bg-slate-900/90 border border-slate-800/80 hover:border-emerald-500/50 hover:bg-slate-900 transition-all duration-200"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-200 group-hover:text-emerald-300 transition-colors">
                      {contact.name}
                    </span>
                  </div>
                  <div className="flex items-center space-x-1.5 mt-1 text-[11px] text-slate-400 group-hover:text-slate-300">
                    <Mail className="w-3 h-3 shrink-0 text-emerald-400" />
                    <span className="truncate">{contact.email}</span>
                  </div>
                </a>
              ))}
            </div>
          </div>

        </div>

        {/* Seamless Bottom Legal Sub-Footer (No dividing horizontal line) */}
        <div className="pt-8 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-slate-400 bg-slate-900/40 p-4 rounded-2xl">
          <p className="text-center md:text-left text-[11px] leading-relaxed max-w-3xl">
            <strong className="text-slate-300">Legal Disclaimer:</strong> Out-of-pocket cost calculations are evidence-grounded estimate ranges based on uploaded policy clauses and pricing benchmarks. This tool does not guarantee final hospital claim settlement.
          </p>

          <p className="shrink-0 font-mono text-[11px] text-slate-400">
            © {new Date().getFullYear()} Spasth. All rights reserved.
          </p>
        </div>

      </div>
    </footer>
  );
}



