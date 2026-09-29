import React from 'react';
import { ArrowRight, ShieldCheck, FileText, CheckCircle2, ChevronRight, Scale, Info } from 'lucide-react';

export default function HeroSection({ onAnalyzeClick, onHowItWorksClick }) {
  return (
    <section className="pt-12 pb-16 bg-white overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          
          {/* Left Hero Text Column */}
          <div className="lg:col-span-7 space-y-6">
            <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-[rgba(57,171,173,0.1)] border border-[#39ABAD]/40 text-xs font-semibold text-[#006668]">
              <ShieldCheck className="w-4 h-4 text-[#006668]" />
              <span>Evidence-Grounded Health Insurance Intelligence</span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-[#003339] leading-[1.12] tracking-tight">
              Know What Your Insurance <span className="text-[#006668]">Will Actually Cover.</span>
            </h1>

            <p className="text-lg sm:text-xl text-[#4A5859] leading-relaxed font-normal max-w-2xl">
              Upload your policy, describe your treatment, and get a cited estimate of your potential out-of-pocket cost.
            </p>

            <div className="pt-2 flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
              <button
                onClick={onAnalyzeClick}
                className="btn-primary px-7 py-3.5 text-base font-semibold flex items-center justify-center space-x-2 cursor-pointer shadow-md"
              >
                <span>Analyze My Policy</span>
                <ArrowRight className="w-5 h-5" />
              </button>

              <button
                onClick={onHowItWorksClick}
                className="btn-secondary px-7 py-3.5 text-base font-semibold flex items-center justify-center space-x-2 cursor-pointer"
              >
                <span>See How It Works</span>
              </button>
            </div>
          </div>

          {/* Right Hero Product Preview Card (Mockup UI) */}
          <div className="lg:col-span-5 relative">
            {/* Soft background tint */}
            <div className="absolute -inset-2 bg-[rgba(57,171,173,0.15)] rounded-3xl blur-2xl -z-10"></div>

            <div className="card-white p-6 sm:p-7 space-y-5 border-[#E2E8E8] shadow-xl relative">
              {/* Card Header Tag */}
              <div className="flex items-center justify-between pb-4 border-b border-[#F7F7F8]">
                <div className="flex items-center space-x-2">
                  <div className="w-8 h-8 rounded-lg bg-[rgba(57,171,173,0.12)] border border-[#39ABAD]/40 flex items-center justify-center text-[#006668]">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-[#003339]">Appendectomy Coverage</h3>
                    <p className="text-[11px] text-[#4A5859] font-mono">Pune • Standard Room</p>
                  </div>
                </div>

                <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-[rgba(57,171,173,0.12)] text-[#006668] border border-[#39ABAD]/40">
                  <CheckCircle2 className="w-3 h-3 mr-1 text-[#006668]" />
                  HIGH CONFIDENCE
                </span>
              </div>

              {/* 3 Metric Rows */}
              <div className="space-y-3">
                <div className="p-3.5 rounded-xl bg-[#F7F7F8] border border-[#E2E8E8] flex justify-between items-center">
                  <span className="text-xs font-semibold text-[#4A5859]">Estimated Treatment Cost</span>
                  <span className="text-sm font-bold text-[#003339] font-mono">₹75,000 – ₹95,000</span>
                </div>

                <div className="p-3.5 rounded-xl bg-[#F7F7F8] border border-[#E2E8E8] flex justify-between items-center">
                  <span className="text-xs font-semibold text-[#4A5859]">Estimated Coverage</span>
                  <span className="text-sm font-bold text-[#006668] font-mono">₹67,500 – ₹72,000</span>
                </div>

                {/* Highlighted Direct Out-of-Pocket Card with Crimson Red Accent (#D51B1D) */}
                <div className="p-4 rounded-xl bg-[rgba(213,27,29,0.06)] border-2 border-[#D51B1D]/60 flex justify-between items-center shadow-sm">
                  <div>
                    <span className="text-xs font-bold text-[#D51B1D] uppercase tracking-wider block">Estimated Out-of-Pocket</span>
                    <span className="text-[11px] text-[#D51B1D]/80 font-medium">Patient Direct Liability</span>
                  </div>
                  <span className="text-xl font-black text-[#D51B1D] font-mono">₹7,500 – ₹23,000</span>
                </div>
              </div>

              {/* Evidence Citation Snippet Preview */}
              <div className="p-3 rounded-xl bg-white border border-[#E2E8E8] flex items-center justify-between text-xs">
                <div className="flex items-center space-x-2">
                  <Scale className="w-4 h-4 text-[#006668] flex-shrink-0" />
                  <div>
                    <span className="text-[#4A5859] font-medium">Policy Evidence: </span>
                    <strong className="text-[#003339] font-semibold">Page 15 · Clause 4.2</strong>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-[#39ABAD]" />
              </div>

              {/* Mandatory Illustrative Example Tag */}
              <div className="text-center pt-1">
                <span className="text-[11px] text-[#4A5859] font-medium">
                  • Illustrative product preview • Real calculation uses your policy PDF
                </span>
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
