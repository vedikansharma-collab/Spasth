import React, { useState } from 'react';
import { DollarSign, ShieldCheck, AlertCircle, FileText, CheckCircle2, ChevronRight, Layers, Scale, Info, ExternalLink, ArrowRight, Ban, Clock } from 'lucide-react';
import CitationModal from './CitationModal';

export default function EstimationResultDashboard({ estimate, onRecalculate, loading }) {
  const [selectedCitation, setSelectedCitation] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [showCalculationFlow, setShowCalculationFlow] = useState(true);

  if (!estimate) return null;

  const formatINR = (amount) => {
    if (amount === undefined || amount === null || isNaN(amount)) return '₹0';
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(amount);
  };

  const handleOpenCitation = (cite) => {
    setSelectedCitation(cite);
    setIsModalOpen(true);
  };

  // 1. Handle EXCLUDED Status (Phase 6)
  if (estimate.status === 'EXCLUDED') {
    return (
      <div id="results" className="space-y-6">
        <CitationModal citation={selectedCitation} isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
        <div className="card-white p-6 sm:p-7 border-[#D51B1D] bg-[rgba(213,27,29,0.04)] text-[#003339] space-y-5">
          <div className="flex items-start space-x-3.5">
            <div className="p-3 rounded-2xl bg-[rgba(213,27,29,0.12)] border border-[#D51B1D]/40 text-[#D51B1D] flex-shrink-0">
              <Ban className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-[#D51B1D] text-white uppercase tracking-wider">
                  Policy Exclusion
                </span>
                <span className="text-xs font-mono text-[#D51B1D] font-bold">Zero Insurance Coverage</span>
              </div>
              <h3 className="text-xl font-black text-[#003339]">Treatment Explicitly Excluded from Coverage</h3>
              <p className="text-xs text-[#4A5859] leading-relaxed">
                {estimate.confidence_reason || 'This medical procedure is explicitly excluded under policy contract clauses.'}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
            <div className="p-4 rounded-xl bg-white border border-[#E2E8E8] space-y-1">
              <span className="text-[10px] uppercase font-bold text-[#4A5859]">Estimated Treatment Cost</span>
              <p className="text-base font-black text-[#003339] font-mono">
                {formatINR(estimate.treatment_cost?.min ?? estimate.treatment_cost_range?.min)} – {formatINR(estimate.treatment_cost?.max ?? estimate.treatment_cost_range?.max)}
              </p>
              <span className="text-[11px] text-[#4A5859]">Source benchmark ({estimate.data_type || 'synthetic'})</span>
            </div>

            <div className="p-4 rounded-xl bg-[rgba(213,27,29,0.06)] border border-[#D51B1D]/30 space-y-1">
              <span className="text-[10px] uppercase font-bold text-[#D51B1D]">Patient Direct Liability</span>
              <p className="text-base font-black text-[#D51B1D] font-mono">
                100% Out-of-Pocket
              </p>
              <span className="text-[11px] text-[#D51B1D]/90">No insurance reimbursement payable</span>
            </div>
          </div>

          {estimate.citations && estimate.citations.length > 0 && (
            <div className="pt-2">
              <span className="text-xs font-bold text-[#003339] block mb-2">Exclusion Policy Citation:</span>
              <div
                onClick={() => handleOpenCitation(estimate.citations[0])}
                className="p-3 rounded-xl bg-white border border-[#E2E8E8] hover:border-[#D51B1D] transition-all cursor-pointer flex items-center justify-between"
              >
                <div>
                  <span className="text-xs font-bold text-[#003339]">{estimate.citations[0].rule}</span>
                  <p className="text-[11px] text-[#4A5859] font-mono mt-0.5">"{estimate.citations[0].source_text}"</p>
                </div>
                <span className="text-[10px] font-bold text-[#D51B1D] bg-[rgba(213,27,29,0.08)] px-2.5 py-1 rounded border border-[#D51B1D]/20 shrink-0">
                  Page {estimate.citations[0].page} · Clause {estimate.citations[0].clause}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // 2. Handle WAITING PERIOD Status (Phase 5)
  if (estimate.status === 'WAITING_PERIOD') {
    return (
      <div id="results" className="space-y-6">
        <CitationModal citation={selectedCitation} isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
        <div className="card-white p-6 sm:p-7 border-amber-300 bg-amber-50/40 text-[#003339] space-y-5">
          <div className="flex items-start space-x-3.5">
            <div className="p-3 rounded-2xl bg-amber-100 border border-amber-300 text-amber-800 flex-shrink-0">
              <Clock className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-amber-600 text-white uppercase tracking-wider">
                  Waiting Period Active
                </span>
                <span className="text-xs font-mono text-amber-900 font-bold">Claim Ineligible at Present</span>
              </div>
              <h3 className="text-xl font-black text-[#003339]">Mandatory Waiting Period Has Not Elapsed</h3>
              <p className="text-xs text-[#4A5859] leading-relaxed">
                {estimate.confidence_reason || 'Policy requires continuous coverage before this condition or procedure becomes claimable.'}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
            <div className="p-4 rounded-xl bg-white border border-[#E2E8E8] space-y-1">
              <span className="text-[10px] uppercase font-bold text-[#4A5859]">Estimated Treatment Cost</span>
              <p className="text-base font-black text-[#003339] font-mono">
                {formatINR(estimate.treatment_cost?.min ?? estimate.treatment_cost_range?.min)} – {formatINR(estimate.treatment_cost?.max ?? estimate.treatment_cost_range?.max)}
              </p>
            </div>
            <div className="p-4 rounded-xl bg-white border border-[#E2E8E8] space-y-1">
              <span className="text-[10px] uppercase font-bold text-amber-800">Current Coverage Eligibility</span>
              <p className="text-base font-black text-amber-800 font-mono">0% (In Waiting Period)</p>
            </div>
          </div>

          {estimate.citations && estimate.citations.length > 0 && (
            <div className="pt-2">
              <span className="text-xs font-bold text-[#003339] block mb-2">Waiting Period Policy Evidence:</span>
              <div
                onClick={() => handleOpenCitation(estimate.citations[0])}
                className="p-3 rounded-xl bg-white border border-[#E2E8E8] hover:border-amber-400 transition-all cursor-pointer flex items-center justify-between"
              >
                <div>
                  <span className="text-xs font-bold text-[#003339]">{estimate.citations[0].rule}</span>
                  <p className="text-[11px] text-[#4A5859] font-mono mt-0.5">"{estimate.citations[0].source_text}"</p>
                </div>
                <span className="text-[10px] font-bold text-amber-800 bg-amber-100 px-2.5 py-1 rounded border border-amber-300 shrink-0">
                  Page {estimate.citations[0].page} · Clause {estimate.citations[0].clause}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // 3. Handle UNABLE TO ESTIMATE / INSUFFICIENT INFORMATION / BENCHMARK MISSING (Phase 4, 7, 8 & 10)
  if (
    estimate.status === 'UNABLE_TO_ESTIMATE' || 
    estimate.status === 'INSUFFICIENT_INFORMATION' || 
    estimate.status === 'TREATMENT_COST_NOT_AVAILABLE' || 
    estimate.status === 'INVALID_INPUT'
  ) {
    return (
      <div id="results" className="card-white p-6 border-[#D51B1D]/40 bg-[rgba(213,27,29,0.04)] text-[#003339] space-y-4">
        <div className="flex items-start space-x-3">
          <div className="p-2.5 rounded-xl bg-[rgba(213,27,29,0.1)] border border-[#D51B1D]/30 text-[#D51B1D] flex-shrink-0">
            <AlertCircle className="w-5 h-5" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-bold text-[#003339]">
              {estimate.status === 'TREATMENT_COST_NOT_AVAILABLE' 
                ? 'Treatment Cost Benchmark Not Available' 
                : 'Unable to Confidently Estimate Out-of-Pocket Expenses'}
            </h3>
            <p className="text-xs text-[#4A5859] leading-relaxed">
              {estimate.message || estimate.confidence_reason || estimate.error || 'Critical policy parameters or baseline pricing benchmarks are missing.'}
            </p>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-white border border-[#E2E8E8] space-y-2 text-xs">
          <span className="font-semibold text-[#003339] block">Missing Information Required for Deterministic Audit:</span>
          <ul className="list-disc list-inside space-y-1 text-[#4A5859] font-mono">
            <li>Verified healthcare procedure benchmark cost for '{estimate.procedure || estimate.treatment?.procedure_name || 'selected procedure'}' in '{estimate.city || estimate.treatment?.city || 'selected city'}'.</li>
            <li>Explicit policy coverage schedule or grounded Sum Insured parameters with page evidence.</li>
          </ul>
        </div>
      </div>
    );
  }

  // 4. Normal Calculated State (Phases 7, 8, 9, 10)
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
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-800 border border-amber-300">
            <AlertCircle className="w-3.5 h-3.5 mr-1 text-amber-700" />
            MEDIUM CONFIDENCE (ROOM / SCENARIO AMBIGUITY)
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

  const costMin = estimate.treatment_cost?.min ?? estimate.treatment_cost_range?.min ?? 0;
  const costMax = estimate.treatment_cost?.max ?? estimate.treatment_cost_range?.max ?? 0;
  const covMin = estimate.insurance_contribution?.min ?? estimate.estimated_coverage_range?.min ?? 0;
  const covMax = estimate.insurance_contribution?.max ?? estimate.estimated_coverage_range?.max ?? 0;
  const oopMin = estimate.patient_payable?.min ?? estimate.estimated_oop_range?.min ?? 0;
  const oopMax = estimate.patient_payable?.max ?? estimate.estimated_oop_range?.max ?? 0;

  const isRangeMode = (estimate.is_range === true || (costMin > 0 && costMax > 0 && costMin !== costMax)) && estimate.treatment_cost_source !== 'USER_PROVIDED';

  const totalCostDisplay = isRangeMode 
    ? (costMin === costMax ? formatINR(costMin) : `${formatINR(costMin)} – ${formatINR(costMax)}`)
    : formatINR(estimate.total_expense ?? costMin);

  const covDisplay = isRangeMode 
    ? (covMin === covMax ? formatINR(covMin) : `${formatINR(covMin)} – ${formatINR(covMax)}`)
    : formatINR(estimate.insurer_payable ?? covMin);

  const oopDisplay = isRangeMode 
    ? (oopMin === oopMax ? formatINR(oopMin) : `${formatINR(oopMin)} – ${formatINR(oopMax)}`)
    : formatINR(estimate.customer_payable ?? oopMin);

  const sublimitVal = estimate.sublimit ?? estimate.applicable_sublimit ?? estimate.sub_limit;
  const copayVal = estimate.co_payment_percentage ?? estimate.copay_percent ?? 0;
  const breakdown = estimate.customer_payable_breakdown;
  const trace = estimate.calculation_trace || [];
  const appliedRulesList = estimate.rules_applied ?? estimate.applied_rules ?? [];
  const citationsList = estimate.evidence ?? estimate.citations ?? [];

  return (
    <div id="results" className="space-y-6">
      <CitationModal citation={selectedCitation} isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />

      {/* Main Result Banner */}
      <div className="card-white p-6 sm:p-7 space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#F7F7F8]">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-[#F7F7F8] text-[#003339] border border-[#E2E8E8] uppercase tracking-wide">
                Scenario: {estimate.procedure || estimate.treatment?.procedure_name || estimate.treatment} • {estimate.city || estimate.treatment?.city}
              </span>
              {getConfidenceBadge(estimate.confidence)}
              {estimate.validation?.status === 'CALCULATION_VALIDATED' && (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-300">
                  <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-emerald-600" />
                  CALCULATION VALIDATED
                </span>
              )}
              {estimate.validation?.status === 'CALCULATION_MISMATCH' && (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-red-50 text-red-800 border border-red-300">
                  <AlertCircle className="w-3.5 h-3.5 mr-1 text-red-600" />
                  CALCULATION MISMATCH
                </span>
              )}
            </div>
            <h2 className="text-2xl sm:text-3xl font-black text-[#003339] tracking-tight">
              Coverage &amp; Financial Estimation Result
            </h2>
            <p className="text-xs text-[#4A5859] mt-1">
              Calculated using authoritative deterministic Python Math Engine. Policy evidence verified with line-level page citations.
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

        {/* 3 Key Financial Cards */}
        <div className="space-y-3">
          {/* Card 1: Base Treatment Cost */}
          <div className="p-4 rounded-xl bg-[#F7F7F8] border border-[#E2E8E8] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-[rgba(57,171,173,0.12)] border border-[#39ABAD]/30 flex items-center justify-center text-[#39ABAD] shrink-0">
                <DollarSign className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-[#003339]">
                  {isRangeMode ? "Total Treatment Cost (Estimated Range)" : "Total Treatment Cost"}
                </h4>
                <p className="text-[11px] text-[#4A5859] font-mono">
                  {isRangeMode ? "State Benchmark Package Rate (Min – Max)" : (estimate.data_source ? `Source: ${estimate.data_source}` : 'Billed Hospital Treatment')}
                </p>
              </div>
            </div>
            <div className="sm:text-right">
              <p className="text-lg font-black text-[#003339] tracking-tight font-mono whitespace-nowrap">
                {totalCostDisplay}
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
                <h4 className="text-xs font-bold text-[#003339]">
                  {isRangeMode ? "Estimated Policy Coverage (Range)" : "Estimated Policy Coverage"}
                </h4>
                <p className="text-[11px] text-[#4A5859] font-mono">
                  {isRangeMode ? "Insurance Net Contribution Range" : "Insurance Net Contribution"}
                </p>
              </div>
            </div>
            <div className="sm:text-right">
              <p className="text-lg font-black text-[#006668] tracking-tight font-mono whitespace-nowrap">
                {covDisplay}
              </p>
            </div>
          </div>

          {/* Card 3: Out-of-Pocket Estimate Card */}
          {oopMax === 0 && (estimate.customer_payable === 0 || !estimate.customer_payable) ? (
            <div className="p-4 sm:p-5 rounded-xl bg-[rgba(0,102,104,0.06)] border-2 border-[#006668] flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-[rgba(0,102,104,0.15)] border border-[#006668]/30 flex items-center justify-center text-[#006668] shrink-0">
                  <CheckCircle2 className="w-5 h-5 text-[#006668]" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h4 className="text-xs font-bold text-[#006668] uppercase tracking-wider">
                      Estimated Out-of-Pocket
                    </h4>
                    <span className="text-[10px] font-extrabold bg-[#006668] text-white px-2 py-0.5 rounded-full uppercase">
                      100% Policy Covered
                    </span>
                  </div>
                  <p className="text-xs text-[#006668]/90 font-medium mt-0.5">
                    Zero Patient Liability — Admissible cost is 100% covered by insurance (0% Co-Pay, ₹0 Deductible, No Sublimit Cap).
                  </p>
                </div>
              </div>
              <div className="sm:text-right">
                <p className="text-xl sm:text-2xl font-black text-[#006668] tracking-tight font-mono whitespace-nowrap">
                  ₹0
                </p>
              </div>
            </div>
          ) : (
            <div className="p-4 sm:p-5 rounded-xl bg-[rgba(213,27,29,0.06)] border-2 border-[#D51B1D] flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-[rgba(213,27,29,0.12)] border border-[#D51B1D]/30 flex items-center justify-center text-[#D51B1D] shrink-0">
                  <Scale className="w-5 h-5 text-[#D51B1D]" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-[#D51B1D] uppercase tracking-wider">
                    {isRangeMode ? "Estimated Out-of-Pocket (Range)" : "Estimated Out-of-Pocket"}
                  </h4>
                  <p className="text-xs text-[#D51B1D]/80 font-medium">
                    {isRangeMode ? "Patient Direct Liability Range" : "Patient Direct Liability"}
                  </p>
                </div>
              </div>
              <div className="sm:text-right">
                <p className="text-xl sm:text-2xl font-black text-[#D51B1D] tracking-tight font-mono whitespace-nowrap">
                  {oopDisplay}
                </p>
              </div>
            </div>
          )}

          {/* Explanation note when Out-of-Pocket is zero */}
          {oopMax === 0 && (estimate.customer_payable === 0 || !estimate.customer_payable) && (
            <div className="p-3.5 rounded-xl bg-[rgba(0,102,104,0.04)] border border-[#006668]/20 flex items-start space-x-3 text-xs">
              <CheckCircle2 className="w-4 h-4 text-[#006668] shrink-0 mt-0.5" />
              <div className="space-y-1">
                <span className="font-bold text-[#003339]">Why is Out-of-Pocket ₹0 for this scenario?</span>
                <p className="text-[#4A5859] leading-relaxed">
                  Your active policy provides <strong>100% full coverage</strong> for this procedure because:
                  (1) <strong>Sum Insured</strong> is ₹10,00,000 (claim is well within your available limit),
                  (2) <strong>Co-Payment</strong> is 0% (Nil co-pay),
                  (3) <strong>Deductible</strong> is ₹0,
                  (4) <strong>Room Category</strong> is Standard (0% room upgrade penalty), and
                  (5) There is <strong>no sublimit cap</strong> on {estimate.procedure || 'this procedure'}.
                </p>
                <p className="text-[11px] text-[#006668] font-medium pt-0.5">
                  💡 <strong>To test scenarios with deductions:</strong> Select a procedure with a sublimit cap (such as <strong>Cataract Surgery</strong> capped at ₹40,000), an excluded procedure (such as <strong>C-Section</strong> under Excl18), or enter non-covered expenses.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Section 8: Transparent Line-by-Line Itemized Accounting Statement */}
        <div className="p-5 rounded-xl bg-white border border-[#E2E8E8] space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#F7F7F8] pb-3">
            <div>
              <h4 className="text-sm font-black text-[#003339] flex items-center space-x-2">
                <Scale className="w-4 h-4 text-[#006668]" />
                <span>Itemized Statement of Benefits &amp; Deductions</span>
              </h4>
              <p className="text-xs text-[#4A5859] mt-0.5">Authoritative calculation by Deterministic Math Engine · Auditable invariant reconciliation</p>
            </div>
            <span className="text-[10px] font-bold text-[#006668] bg-[rgba(0,102,104,0.08)] px-2.5 py-1 rounded-full uppercase shrink-0">
              {estimate.treatment_cost_source_label || (estimate.treatment_cost_source === 'USER_PROVIDED' ? 'User-Provided Actual Bill' : 'Reference Dataset Cost')}
            </span>
          </div>

          <div className="divide-y divide-[#F7F7F8] text-xs">
            {/* 1. Total Treatment Cost */}
            <div className="py-2.5 flex items-center justify-between">
              <span className="font-semibold text-[#003339]">Total Billed Treatment Cost</span>
              <span className="font-mono font-bold text-[#003339]">{totalCostDisplay}</span>
            </div>

            {/* 2. Non-Covered Items (only if > 0) */}
            {estimate.non_covered_expense > 0 && (
              <div className="py-2.5 flex items-center justify-between text-[#D51B1D]">
                <span>Less: Non-Covered Medical Items / Exclusions</span>
                <span className="font-mono font-bold">- {formatINR(estimate.non_covered_expense)}</span>
              </div>
            )}

            {/* 3. Eligible Claim Base */}
            <div className="py-2.5 flex items-center justify-between bg-[#F7F7F8]/60 px-2 rounded">
              <span className="font-bold text-[#003339]">Admissible Treatment Claim Base</span>
              <span className="font-mono font-bold text-[#006668]">{formatINR(estimate.eligible_amount ?? estimate.eligible_expense)}</span>
            </div>

            {/* 4. Sub-Limit (if applicable) */}
            {estimate.sublimit != null && (
              <div className="py-2.5 flex items-center justify-between">
                <span>
                  Procedure Sub-Limit Cap ({formatINR(estimate.sublimit)})
                  {breakdown?.sublimit_excess > 0 && <span className="text-[#D51B1D] ml-1">(Excess Patient Direct Liability)</span>}
                </span>
                <span className="font-mono font-semibold text-[#4A5859]">
                  {breakdown?.sublimit_excess > 0 ? `- ${formatINR(breakdown.sublimit_excess)} excess` : 'Cap Not Exceeded'}
                </span>
              </div>
            )}

            {/* 5. Room Rent Upgrade Penalty (if applicable) */}
            {breakdown?.room_upgrade_excess > 0 && (
              <div className="py-2.5 flex items-center justify-between text-[#D51B1D]">
                <span>Room Category Upgrade Proportionate Penalty</span>
                <span className="font-mono font-bold">- {formatINR(breakdown.room_upgrade_excess)}</span>
              </div>
            )}

            {/* 6. Deductible */}
            <div className="py-2.5 flex items-center justify-between">
              <span>Policy Deductible Applied</span>
              <span className="font-mono font-semibold text-[#4A5859]">
                {breakdown?.deductible > 0 ? `- ${formatINR(breakdown.deductible)}` : '₹0 (Nil Deductible)'}
              </span>
            </div>

            {/* 7. Co-Payment */}
            <div className="py-2.5 flex items-center justify-between">
              <span>Co-Payment Applied ({copayVal > 0 ? `${copayVal}%` : '0% Nil'})</span>
              <span className="font-mono font-semibold text-[#4A5859]">
                {breakdown?.co_payment > 0 ? `- ${formatINR(breakdown.co_payment)}` : '₹0 (Nil Co-Payment)'}
              </span>
            </div>

            {/* 8. Sum Insured Applied */}
            {breakdown?.sum_insured_excess > 0 && (
              <div className="py-2.5 flex items-center justify-between text-[#D51B1D]">
                <span>Sum Insured Exhaustion Excess</span>
                <span className="font-mono font-bold">- {formatINR(breakdown.sum_insured_excess)}</span>
              </div>
            )}

            {/* 9. Final Reconciliation Cards */}
            <div className="pt-3 pb-1 grid grid-cols-1 sm:grid-cols-3 gap-2.5">
              <div className="p-3 rounded-xl bg-[rgba(0,102,104,0.06)] border border-[#006668]/30">
                <span className="text-[10px] uppercase font-bold text-[#006668] block">Insurance Pays</span>
                <span className="text-base font-black text-[#006668] font-mono">{covDisplay}</span>
              </div>

              <div className="p-3 rounded-xl bg-[rgba(213,27,29,0.06)] border border-[#D51B1D]/40">
                <span className="text-[10px] uppercase font-bold text-[#D51B1D] block">You Pay (Out-of-Pocket)</span>
                <span className="text-base font-black text-[#D51B1D] font-mono">{oopDisplay}</span>
              </div>

              <div className="p-3 rounded-xl bg-[#F7F7F8] border border-[#E2E8E8]">
                <span className="text-[10px] uppercase font-bold text-[#4A5859] block">Remaining Sum Insured</span>
                <span className="text-base font-black text-[#003339] font-mono">
                  {formatINR(estimate.remaining_sum_insured ?? estimate.new_remaining_sum_insured)}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Section 10: Reference Cost vs Actual Bill Clear Notice */}
        <div className="p-3.5 rounded-xl bg-[#F7F7F8] border border-[#E2E8E8] flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs text-[#4A5859]">
          <span className="flex items-center space-x-2">
            <Info className="w-4 h-4 text-[#006668] shrink-0" />
            <span>
              {estimate.treatment_cost_source === 'USER_PROVIDED' ? (
                <>This calculation is based on the <strong>user-provided actual treatment cost</strong>.</>
              ) : (
                <>
                  This estimate uses the <strong>reference treatment cost</strong> available in the SPASTH treatment dataset ({totalCostDisplay}). <em>Actual hospital billing may differ. Reference dataset does not represent an official insurer tariff.</em>
                </>
              )}
            </span>
          </span>
          <span className="text-[11px] font-mono text-[#4A5859] shrink-0">
            Source: {estimate.data_source || 'State Healthcare Package Benchmark 2025'}
          </span>
        </div>

        {/* Step-by-Step Breakdown */}
        <div className="pt-2 border-t border-[#E2E8E8]">
          <button
            onClick={() => setShowCalculationFlow(!showCalculationFlow)}
            className="w-full flex items-center justify-between p-3 rounded-xl bg-[#F7F7F8] hover:bg-[#E2E8E8]/60 border border-[#E2E8E8] text-xs font-bold text-[#003339] transition-all cursor-pointer"
          >
            <span className="flex items-center space-x-2">
              <Scale className="w-4 h-4 text-[#006668]" />
              <span>How this estimate was calculated (Deterministic Math Engine Pipeline)</span>
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
                <span>Deterministic Calculation Trace (Authoritative Math Engine):</span>
              </div>

              {trace.length > 0 ? (
                <div className="space-y-2">
                  {trace.map((step) => (
                    <div key={step.step} className="p-3 rounded-lg bg-white border border-[#E2E8E8] flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="space-y-0.5">
                        <div className="flex items-center space-x-2">
                          <span className="w-5 h-5 rounded-full bg-[#006668] text-white text-[10px] font-bold flex items-center justify-center shrink-0">
                            {step.step}
                          </span>
                          <span className="text-xs font-bold text-[#003339] font-sans">{step.rule.replace(/_/g, ' ')}</span>
                        </div>
                        <p className="text-[11px] text-[#4A5859] font-sans pl-7">{step.description}</p>
                      </div>
                      <div className="flex items-center space-x-4 pl-7 sm:pl-0 font-mono text-xs text-right shrink-0">
                        {step.deduction > 0 && (
                          <div className="text-[#D51B1D]">
                            <span className="text-[10px] text-[#4A5859] uppercase block font-sans">Deduction</span>
                            <span>- {formatINR(step.deduction)}</span>
                          </div>
                        )}
                        <div>
                          <span className="text-[10px] text-[#4A5859] uppercase block font-sans">Output Balance</span>
                          <span className="font-bold text-[#006668]">{formatINR(step.output)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-3 bg-white rounded-lg border border-[#E2E8E8] text-center text-[#4A5859]">
                  Deterministic calculation completed.
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Applied Policy Rules */}
      <div className="card-white p-5 space-y-3">
        <div className="flex items-center justify-between pb-2.5 border-b border-[#F7F7F8]">
          <h3 className="font-bold text-[#003339] text-sm flex items-center space-x-2">
            <Layers className="w-4 h-4 text-[#006668]" />
            <span>Applied Calculation Rules</span>
          </h3>
          <span className="text-xs text-[#4A5859] font-mono">
            {appliedRulesList.length} {appliedRulesList.length === 1 ? 'Rule' : 'Rules'} Applied
          </span>
        </div>

        {appliedRulesList.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {appliedRulesList.map((rule, idx) => (
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

      {/* Evidence & Page Citations */}
      <div className="card-white p-5 space-y-3">
        <div className="flex items-center justify-between pb-2.5 border-b border-[#F7F7F8]">
          <h3 className="font-bold text-[#003339] text-sm flex items-center space-x-2">
            <FileText className="w-4 h-4 text-[#006668]" />
            <span>Policy Citations &amp; Evidence</span>
          </h3>
          <span className="text-xs text-[#006668] font-mono font-semibold">Click to Inspect Source</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {citationsList.map((cite, idx) => (
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
