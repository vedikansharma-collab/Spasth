import React, { useState } from 'react';
import { DollarSign, ShieldCheck, AlertCircle, FileText, CheckCircle2, ChevronRight, Layers, Scale, Info, ExternalLink, ArrowRight } from 'lucide-react';
import CitationModal from './CitationModal';

export default function EstimationResultDashboard({ estimate, onRecalculate, loading }) {
  const [selectedCitation, setSelectedCitation] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [showCalculationFlow, setShowCalculationFlow] = useState(true);

  if (!estimate) return null;

  const formatINR = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(amount);
  };

  // Handle UNABLE TO ESTIMATE state
  if (estimate.status === 'UNABLE_TO_ESTIMATE') {
    return (
      <div className="card-white p-6 border-[#D51B1D]/40 bg-[rgba(213,27,29,0.04)] text-[#003339] space-y-4">
        <div className="flex items-start space-x-3">
          <div className="p-2 rounded-xl bg-[rgba(213,27,29,0.1)] border border-[#D51B1D]/30 text-[#D51B1D] flex-shrink-0">
            <AlertCircle className="w-5 h-5" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-bold text-[#003339]">Unable to Confidently Estimate Out-of-Pocket Expenses</h3>
            <p className="text-xs text-[#4A5859] leading-relaxed">
              {estimate.confidence_reason || 'Critical policy parameters or baseline pricing benchmarks are missing.'}
            </p>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-white border border-[#E2E8E8] space-y-2 text-xs">
          <span className="font-semibold text-[#003339] block">Missing Information Required for Audit:</span>
          <ul className="list-disc list-inside space-y-1 text-[#4A5859] font-mono">
            <li>Verified healthcare procedure benchmark cost for '{estimate.procedure}' in '{estimate.city}'.</li>
            <li>Explicit policy coverage schedule or sum insured parameters.</li>
          </ul>
        </div>
      </div>
    );
  }

  const getConfidenceBadge = (confidence) => {
    switch (confidence?.toUpperCase()) {
      case 'HIGH':
        return (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-[rgba(57,171,173,0.12)] text-[#006668] border border-[#39ABAD]/40">
            <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-[#006668]" />
            HIGH CONFIDENCE EVIDENCE
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-[rgba(213,27,29,0.08)] text-[#D51B1D] border border-[#D51B1D]/40">
            <AlertCircle className="w-3.5 h-3.5 mr-1 text-[#D51B1D]" />
            MEDIUM CONFIDENCE (SCENARIO PENALTY)
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-[rgba(213,27,29,0.12)] text-[#D51B1D] border border-[#D51B1D]/50">
            <AlertCircle className="w-3.5 h-3.5 mr-1 text-[#D51B1D]" />
            LOW CONFIDENCE EVIDENCE
          </span>
        );
    }
  };

  const handleOpenCitation = (cite) => {
    setSelectedCitation(cite);
    setIsModalOpen(true);
  };

  return (
    <div id="results" className="space-y-6">
      {/* Citation Detail Modal */}
      <CitationModal
        citation={selectedCitation}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />

      {/* Main Result Banner */}
      <div className="card-white p-6 sm:p-7 space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#F7F7F8]">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-[#F7F7F8] text-[#003339] border border-[#E2E8E8] uppercase tracking-wide">
                Scenario: {estimate.procedure} • {estimate.city}
              </span>
              {getConfidenceBadge(estimate.confidence)}
            </div>
            <h2 className="text-2xl sm:text-3xl font-black text-[#003339] tracking-tight">
              Coverage &amp; Financial Estimation Result
            </h2>
            <p className="text-xs text-[#4A5859] mt-1">
              Calculated using a deterministic financial rule engine. Policy rules grounded with exact page citations.
            </p>
          </div>

          {/* Scenario Sensitivity Recalculation Toggle */}
          <div className="flex items-center space-x-2 bg-[#F7F7F8] p-1.5 rounded-xl border border-[#E2E8E8]">
            <span className="text-xs text-[#4A5859] px-2 font-medium">Room Category:</span>
            <button
              disabled={loading}
              onClick={() => onRecalculate('Standard')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                estimate.room_category === 'Standard'
                  ? 'bg-[#006668] text-white shadow-2xs'
                  : 'text-[#4A5859] hover:text-[#003339] hover:bg-[#E2E8E8]/60'
              }`}
            >
              Standard
            </button>
            <button
              disabled={loading}
              onClick={() => onRecalculate('Deluxe')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                estimate.room_category === 'Deluxe'
                  ? 'bg-[#D51B1D] text-white shadow-2xs'
                  : 'text-[#4A5859] hover:text-[#003339] hover:bg-[#E2E8E8]/60'
              }`}
            >
              Deluxe
            </button>
          </div>
        </div>

        {/* 3 Key Financial Cards — SPACIOUS HORIZONTAL ROW CARDS (NO TEXT WRAPPING) */}
        <div className="space-y-3">
          {/* Card 1: Base Treatment Cost Range */}
          <div className="p-4 rounded-xl bg-[#F7F7F8] border border-[#E2E8E8] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-[rgba(57,171,173,0.12)] border border-[#39ABAD]/30 flex items-center justify-center text-[#39ABAD] shrink-0">
                <DollarSign className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-[#003339]">Treatment Cost Range</h4>
                <p className="text-[11px] text-[#4A5859] font-mono">Source: {estimate.data_source}</p>
              </div>
            </div>
            <div className="sm:text-right">
              <p className="text-lg font-black text-[#003339] tracking-tight font-mono whitespace-nowrap">
                {formatINR(estimate.treatment_cost_range.min)} – {formatINR(estimate.treatment_cost_range.max)}
              </p>
            </div>
          </div>

          {/* Card 2: Estimated Insurance Coverage */}
          <div className="p-4 rounded-xl bg-[#F7F7F8] border border-[#E2E8E8] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-[rgba(0,102,104,0.12)] border border-[#006668]/30 flex items-center justify-center text-[#006668] shrink-0">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-[#003339]">Estimated Policy Coverage</h4>
                <p className="text-[11px] text-[#4A5859] font-mono">Net Coverage Amount</p>
              </div>
            </div>
            <div className="sm:text-right">
              <p className="text-lg font-black text-[#006668] tracking-tight font-mono whitespace-nowrap">
                {formatINR(estimate.estimated_coverage_range.min)} – {formatINR(estimate.estimated_coverage_range.max)}
              </p>
            </div>
          </div>

          {/* Card 3: VISUALLY DOMINANT OUT-OF-POCKET ESTIMATE CARD IN CRIMSON RED (#D51B1D) */}
          <div className="p-4 sm:p-5 rounded-xl bg-[rgba(213,27,29,0.06)] border-2 border-[#D51B1D] flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-[rgba(213,27,29,0.12)] border border-[#D51B1D]/30 flex items-center justify-center text-[#D51B1D] shrink-0">
                <Scale className="w-5 h-5 text-[#D51B1D]" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-[#D51B1D] uppercase tracking-wider">Estimated Out-of-Pocket</h4>
                <p className="text-xs text-[#D51B1D]/80 font-medium">Patient Direct Liability</p>
              </div>
            </div>
            <div className="sm:text-right">
              <p className="text-xl sm:text-2xl font-black text-[#D51B1D] tracking-tight font-mono whitespace-nowrap">
                {formatINR(estimate.estimated_oop_range.min)} – {formatINR(estimate.estimated_oop_range.max)}
              </p>
            </div>
          </div>
        </div>

        {/* Demo Disclaimer */}
        <div className="p-3 rounded-xl bg-[#F7F7F8] border border-[#E2E8E8] flex items-center justify-between text-xs text-[#4A5859]">
          <span className="flex items-center space-x-2">
            <Info className="w-4 h-4 text-[#39ABAD] flex-shrink-0" />
            <span><strong>Illustrative demo cost benchmark</strong> — not a final hospital quotation.</span>
          </span>
          <span className="text-[11px] font-mono text-[#4A5859] hidden sm:inline">
            Reason: {estimate.confidence_reason || 'Verified page citations'}
          </span>
        </div>

        {/* Expandable "How this estimate was calculated" section */}
        <div className="pt-2 border-t border-[#E2E8E8]">
          <button
            onClick={() => setShowCalculationFlow(!showCalculationFlow)}
            className="w-full flex items-center justify-between p-3 rounded-xl bg-[#F7F7F8] hover:bg-[#E2E8E8]/60 border border-[#E2E8E8] text-xs font-bold text-[#003339] transition-all cursor-pointer"
          >
            <span className="flex items-center space-x-2">
              <Scale className="w-4 h-4 text-[#006668]" />
              <span>How this estimate was calculated (Step-by-Step Breakdown)</span>
            </span>
            <span className="text-[11px] text-[#4A5859] font-mono flex items-center space-x-1">
              <span>{showCalculationFlow ? 'Hide Breakdown' : 'Show Breakdown'}</span>
              <ChevronRight className={`w-4 h-4 transition-transform ${showCalculationFlow ? 'rotate-90' : ''}`} />
            </span>
          </button>

          {showCalculationFlow && (
            <div className="mt-3 p-4 rounded-xl bg-[#F7F7F8] border border-[#E2E8E8] space-y-3 font-mono text-xs">
              <div className="flex items-center space-x-2 text-[#006668] font-bold text-xs font-sans">
                <ArrowRight className="w-4 h-4" />
                <span>Horizontal Calculation Pipeline:</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                <div className="p-3 rounded-lg bg-white border border-[#E2E8E8] flex flex-col justify-between space-y-1">
                  <span className="text-[10px] text-[#4A5859] uppercase font-sans">1. Treatment Cost</span>
                  <span className="text-xs text-[#003339] font-bold">{formatINR(estimate.treatment_cost_range.min)} – {formatINR(estimate.treatment_cost_range.max)}</span>
                </div>

                <div className="p-3 rounded-lg bg-white border border-[#E2E8E8] flex flex-col justify-between space-y-1">
                  <span className="text-[10px] text-[#4A5859] uppercase font-sans">2. Policy Sub-Limit</span>
                  <span className="text-xs text-[#006668] font-bold">
                    {estimate.sub_limit ? formatINR(estimate.sub_limit) : 'No Sub-Limit Cap'}
                  </span>
                </div>

                <div className="p-3 rounded-lg bg-white border border-[#E2E8E8] flex flex-col justify-between space-y-1">
                  <span className="text-[10px] text-[#4A5859] uppercase font-sans">3. Eligible Claim</span>
                  <span className="text-xs text-[#003339] font-bold">{formatINR(estimate.eligible_amount_range.min)} – {formatINR(estimate.eligible_amount_range.max)}</span>
                </div>

                <div className="p-3 rounded-lg bg-white border border-[#E2E8E8] flex flex-col justify-between space-y-1">
                  <span className="text-[10px] text-[#4A5859] uppercase font-sans">4. Co-Pay Deduction</span>
                  <span className="text-xs text-[#D51B1D] font-bold">{estimate.copay_percent || 0}% Co-Pay</span>
                </div>

                <div className="p-3 rounded-lg bg-[rgba(57,171,173,0.1)] border border-[#39ABAD]/40 flex flex-col justify-between space-y-1">
                  <span className="text-[10px] text-[#006668] uppercase font-sans font-bold">5. Insurance Coverage</span>
                  <span className="text-xs text-[#006668] font-bold">{formatINR(estimate.estimated_coverage_range.min)} – {formatINR(estimate.estimated_coverage_range.max)}</span>
                </div>

                <div className="p-3 rounded-lg bg-[rgba(213,27,29,0.08)] border border-[#D51B1D]/40 flex flex-col justify-between space-y-1">
                  <span className="text-[10px] text-[#D51B1D] uppercase font-sans font-bold">6. Patient Out-of-Pocket</span>
                  <span className="text-xs text-[#D51B1D] font-black">{formatINR(estimate.estimated_oop_range.min)} – {formatINR(estimate.estimated_oop_range.max)}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Applied Policy Rules & Deductions (Horizontal Full Width) */}
      <div className="card-white p-5 space-y-3">
        <div className="flex items-center justify-between pb-2.5 border-b border-[#F7F7F8]">
          <h3 className="font-bold text-[#003339] text-sm flex items-center space-x-2">
            <Layers className="w-4 h-4 text-[#006668]" />
            <span>Applied Calculation Rules</span>
          </h3>
          <span className="text-xs text-[#4A5859] font-mono">
            {estimate.applied_rules.length} {estimate.applied_rules.length === 1 ? 'Rule' : 'Rules'} Applied
          </span>
        </div>

        {estimate.applied_rules.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {estimate.applied_rules.map((rule, idx) => (
              <div key={idx} className="p-3 rounded-xl bg-[#F7F7F8] border border-[#E2E8E8] flex flex-col justify-between space-y-1.5">
                <div className="flex items-start justify-between gap-2">
                  <span className="text-xs font-bold text-[#003339] leading-snug">{rule.rule_name}</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white text-[#4A5859] border border-[#E2E8E8] shrink-0">
                    {rule.impact}
                  </span>
                </div>
                <p className="text-xs text-[#4A5859] leading-relaxed">{rule.description}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-[#4A5859] py-2 text-center">Standard base coverage applied without procedure sub-limit reductions.</p>
        )}
      </div>

      {/* Evidence & Page Citations (Horizontal Full Width) */}
      <div className="card-white p-5 space-y-3">
        <div className="flex items-center justify-between pb-2.5 border-b border-[#F7F7F8]">
          <h3 className="font-bold text-[#003339] text-sm flex items-center space-x-2">
            <FileText className="w-4 h-4 text-[#006668]" />
            <span>Policy Citations &amp; Evidence</span>
          </h3>
          <span className="text-xs text-[#006668] font-mono font-semibold">Click to Inspect Source</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {estimate.citations.map((cite, idx) => (
            <div 
              key={idx} 
              onClick={() => handleOpenCitation(cite)}
              className="p-3 rounded-xl bg-[#F7F7F8] border border-[#E2E8E8] hover:border-[#39ABAD] transition-all cursor-pointer flex flex-col justify-between space-y-2 group"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-bold text-[#003339] group-hover:text-[#006668] transition-colors truncate">{cite.rule}</span>
                <span className="text-[10px] font-semibold text-[#006668] bg-[rgba(57,171,173,0.12)] px-2 py-0.5 rounded border border-[#39ABAD]/40 flex items-center space-x-1 shrink-0">
                  <span>P{cite.page} · Cl {cite.clause}</span>
                  <ExternalLink className="w-3 h-3 ml-0.5" />
                </span>
              </div>
              <p className="text-[11px] text-[#4A5859] font-mono bg-white p-2 rounded border border-[#E2E8E8] truncate">
                "{cite.source_text}"
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
