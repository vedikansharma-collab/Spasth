import React from 'react';
import { 
  Bot, Calculator, FileText, ArrowRight, UploadCloud, 
  CheckCircle2, AlertCircle, Shield, Sparkles, BookOpen, 
  Clock, DollarSign, Percent, Bed, ShieldAlert 
} from 'lucide-react';
import PolicyUpload from './PolicyUpload';
import PolicyRulesCards from './PolicyRulesCards';
import PolicyList from './PolicyList';
import HeroSection from './HeroSection';
import TrustIndicators from './TrustIndicators';
import HowItWorks from './HowItWorks';
import EvidenceSection from './EvidenceSection';
import WhyFin01Section from './WhyFin01Section';
import FinalCTA from './FinalCTA';

export default function DashboardHomeView({
  activePolicyId,
  activePolicy,
  onUploadSuccess,
  onSelectPolicy,
  onOpenAssistant,
  onOpenEstimator,
  onOpenDocument,
  onResetPolicy,
  policies = []
}) {
  return (
    <div className="space-y-12 animate-fade-in">
      {/* 1. Hero / Executive Welcome */}
      <div className="bg-linear-to-b from-white to-[#F7F7F8] border-b border-[#E2E8E8] py-10 sm:py-14">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
          
          {/* Header Title */}
          <div className="text-center max-w-3xl mx-auto space-y-3">
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-[rgba(57,171,173,0.12)] text-[#006668] border border-[#39ABAD]/40 uppercase tracking-wider inline-block">
              Policy-to-Patient Intelligence
            </span>
            <h1 className="text-3xl sm:text-5xl font-black text-[#003339] tracking-tight">
              SPASTH Policy Intelligence Dashboard
            </h1>
            <p className="text-sm sm:text-base text-[#4A5859] leading-relaxed">
              Transparent health insurance comprehension paired with deterministic treatment out-of-pocket cost estimation.
            </p>
          </div>

          {/* Current Policy Executive Card */}
          <div className="max-w-4xl mx-auto">
            <div className="card-white p-6 sm:p-7 border-2 border-[#39ABAD]/40 bg-white shadow-md space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-[#E2E8E8]">
                <div className="flex items-start space-x-3.5">
                  <div className="w-12 h-12 rounded-xl bg-[#003339] flex items-center justify-center text-[#73FFFF] shadow-xs shrink-0">
                    <FileText className="w-6 h-6 text-[#73FFFF]" />
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-bold uppercase tracking-wider text-[#4A5859]">
                        Current Uploaded Policy
                      </span>
                      {activePolicy ? (
                        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
                          Processed &amp; Ready
                        </span>
                      ) : (
                        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">
                          No Policy Active
                        </span>
                      )}
                    </div>
                    <h3 className="text-lg font-black text-[#003339] mt-0.5">
                      {activePolicy?.original_filename || 'No policy document loaded'}
                    </h3>
                    <p className="text-xs text-[#4A5859]">
                      {activePolicy 
                        ? `${activePolicy.page_count} preserved pages with 100% citation grounding`
                        : 'Upload a PDF policy or choose an indexed document to begin.'}
                    </p>
                  </div>
                </div>

                {activePolicy && (
                  <div className="flex items-center space-x-2 shrink-0">
                    <button
                      onClick={onResetPolicy}
                      className="text-xs font-semibold text-[#D51B1D] hover:underline cursor-pointer"
                    >
                      Change Document
                    </button>
                  </div>
                )}
              </div>

              {/* Primary Dual Actions */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <button
                  onClick={onOpenAssistant}
                  className="p-4 rounded-xl bg-[rgba(57,171,173,0.08)] hover:bg-[rgba(57,171,173,0.16)] border border-[#39ABAD]/50 text-left transition-all cursor-pointer group flex items-start justify-between"
                >
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2 text-[#006668] font-bold text-sm">
                      <Bot className="w-4 h-4" />
                      <span>Ask About My Policy</span>
                    </div>
                    <p className="text-xs text-[#4A5859]">
                      Inquire about coverage, exclusions, waiting periods, and room limits with citations.
                    </p>
                  </div>
                  <ArrowRight className="w-4 h-4 text-[#006668] group-hover:translate-x-1 transition-transform shrink-0 ml-2 mt-1" />
                </button>

                <button
                  onClick={onOpenEstimator}
                  className="p-4 rounded-xl bg-[rgba(0,102,104,0.08)] hover:bg-[rgba(0,102,104,0.16)] border border-[#006668]/50 text-left transition-all cursor-pointer group flex items-start justify-between"
                >
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2 text-[#006668] font-bold text-sm">
                      <Calculator className="w-4 h-4" />
                      <span>Calculate Treatment Cost</span>
                    </div>
                    <p className="text-xs text-[#4A5859]">
                      Estimate patient out-of-pocket liabilities and insurance contribution deterministically.
                    </p>
                  </div>
                  <ArrowRight className="w-4 h-4 text-[#006668] group-hover:translate-x-1 transition-transform shrink-0 ml-2 mt-1" />
                </button>
              </div>

              {/* Extracted Policy Parameters Summary (Only real data!) */}
              {activePolicy && activePolicy.rules && activePolicy.rules.length > 0 && (
                <div className="pt-2 border-t border-[#E2E8E8] space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-[#4A5859]">
                      Extracted Policy Rules
                    </h4>
                    <button
                      onClick={() => onOpenDocument(1)}
                      className="text-xs font-bold text-[#006668] hover:underline flex items-center space-x-1 cursor-pointer"
                    >
                      <span>View in Policy Document</span>
                      <ArrowRight className="w-3 h-3 ml-0.5" />
                    </button>
                  </div>
                  <PolicyRulesCards rules={activePolicy.rules} onCitationClick={(c) => onOpenDocument(c.page, c)} />
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        {/* 2. Two Distinct Core Pillars */}
        <div className="space-y-4">
          <div className="text-center max-w-2xl mx-auto space-y-1">
            <h2 className="text-2xl font-black text-[#003339] tracking-tight">Two Distinct Intelligence Experiences</h2>
            <p className="text-xs sm:text-sm text-[#4A5859]">
              Policy comprehension is powered by grounded AI; cost estimation is executed by a deterministic math engine.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Pillar 1: Policy Assistant */}
            <div className="card-white p-7 space-y-5 flex flex-col justify-between border-[#E2E8E8] hover:border-[#39ABAD]">
              <div className="space-y-3">
                <div className="w-12 h-12 rounded-xl bg-[rgba(57,171,173,0.12)] border border-[#39ABAD]/40 flex items-center justify-center text-[#006668]">
                  <Bot className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-black text-[#003339]">Policy Assistant</h3>
                <p className="text-xs text-[#4A5859] leading-relaxed">
                  Understand your health insurance policy in simple language. Ask questions about specific treatments, mandatory co-payment rules, room rent ceilings, and waiting periods. Every answer provides exact page citations from your document.
                </p>

                <div className="pt-2 space-y-1.5">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[#006668] block">Sample Queries:</span>
                  <div className="flex flex-wrap gap-1.5">
                    <span className="text-[11px] px-2.5 py-1 rounded-md bg-[#F7F7F8] border border-[#E2E8E8] text-[#003339]">
                      "Is knee replacement covered?"
                    </span>
                    <span className="text-[11px] px-2.5 py-1 rounded-md bg-[#F7F7F8] border border-[#E2E8E8] text-[#003339]">
                      "What is my co-pay percentage?"
                    </span>
                  </div>
                </div>
              </div>

              <button
                onClick={onOpenAssistant}
                className="btn-primary w-full py-3 text-xs sm:text-sm font-bold flex items-center justify-center space-x-2 cursor-pointer shadow-xs"
              >
                <span>Open Policy Assistant</span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </button>
            </div>

            {/* Pillar 2: Cost Estimator */}
            <div className="card-white p-7 space-y-5 flex flex-col justify-between border-[#E2E8E8] hover:border-[#006668]">
              <div className="space-y-3">
                <div className="w-12 h-12 rounded-xl bg-[rgba(0,102,104,0.1)] border border-[#006668]/30 flex items-center justify-center text-[#006668]">
                  <Calculator className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-black text-[#003339]">Treatment Cost Estimator</h3>
                <p className="text-xs text-[#4A5859] leading-relaxed">
                  Deterministic mathematical engine that calculates your estimated insurance coverage and patient out-of-pocket liabilities. Models procedure benchmarks across cities, room categories, and policy sub-limits without guessing or hallucinating numbers.
                </p>

                <div className="pt-2 space-y-1.5">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[#006668] block">Key Outputs:</span>
                  <div className="flex flex-wrap gap-1.5">
                    <span className="text-[11px] px-2.5 py-1 rounded-md bg-[#F7F7F8] border border-[#E2E8E8] text-[#003339]">
                      Patient Out-of-Pocket Liability
                    </span>
                    <span className="text-[11px] px-2.5 py-1 rounded-md bg-[#F7F7F8] border border-[#E2E8E8] text-[#003339]">
                      Room Upgrade Penalty Model
                    </span>
                  </div>
                </div>
              </div>

              <button
                onClick={onOpenEstimator}
                className="btn-primary w-full py-3 text-xs sm:text-sm font-bold flex items-center justify-center space-x-2 cursor-pointer shadow-xs"
              >
                <span>Calculate Treatment Cost</span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </button>
            </div>
          </div>
        </div>

        {/* 3. Upload & Document Selection Section */}
        <div className="space-y-6">
          <div className="text-center max-w-xl mx-auto space-y-1">
            <h3 className="text-xl font-black text-[#003339]">Manage Policy Documents</h3>
            <p className="text-xs text-[#4A5859]">
              Upload a new policy PDF or select an existing indexed document from the library.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
            {/* Upload Zone */}
            <PolicyUpload onUploadSuccess={onUploadSuccess} />

            {/* Indexed Policy Library */}
            <PolicyList
              onSelectPolicy={onSelectPolicy}
              activePolicyId={activePolicyId}
            />
          </div>
        </div>

        {/* 4. Trust Indicators */}
        <TrustIndicators />

        {/* 5. How It Works */}
        <HowItWorks />

        {/* 6. Evidence Section */}
        <EvidenceSection onInspectClick={onOpenEstimator} />

        {/* 7. Why Spasth */}
        <WhyFin01Section />

        {/* 8. Final CTA */}
        <FinalCTA onAnalyzeClick={onOpenEstimator} />
      </div>
    </div>
  );
}
