import React from 'react';
import { 
  Calculator, Stethoscope, Scale, DollarSign, 
  ShieldCheck, AlertCircle, ArrowRight, Layers, FileText, 
  ExternalLink, Sparkles 
} from 'lucide-react';
import TreatmentScenarioForm from './TreatmentScenarioForm';
import EstimationResultDashboard from './EstimationResultDashboard';
import ScenarioSensitivitySection from './ScenarioSensitivitySection';
import ConfidenceSection from './ConfidenceSection';

export default function CostEstimatorView({ 
  activePolicyId, 
  activePolicy, 
  onCalculate, 
  estimateResult, 
  estimating, 
  onRecalculateRoom, 
  onNavigateToDoc,
  onSelectPolicy,
  policies = []
}) {
  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8 animate-fade-in">
      {/* Top Header Card */}
      <div className="card-white p-5 sm:p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-[#E2E8E8]">
        <div className="flex items-center space-x-3.5">
          <div className="w-12 h-12 rounded-xl bg-[#006668] flex items-center justify-center text-white shadow-xs shrink-0">
            <Calculator className="w-6 h-6" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-xl font-black text-[#003339] tracking-tight">Treatment Cost Estimator</h2>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[rgba(0,102,104,0.1)] text-[#006668] border border-[#006668]/30 uppercase tracking-wide">
                Deterministic Math Engine
              </span>
            </div>
            <p className="text-xs text-[#4A5859] mt-0.5">
              Calculating against: <strong className="text-[#003339] font-semibold">{activePolicy?.original_filename || 'No policy selected'}</strong>
            </p>
          </div>
        </div>

        {activePolicy && (
          <div className="flex items-center space-x-2 shrink-0">
            <span className="text-xs font-mono font-semibold text-[#006668] bg-[#F7F7F8] px-3 py-1.5 rounded-xl border border-[#E2E8E8]">
              Sum Insured: ₹{activePolicy.rules?.find(r => r.rule_type === 'sum_insured')?.value?.toLocaleString('en-IN') || '5,00,000'}
            </span>
          </div>
        )}
      </div>

      {/* No Policy Banner / Prompt */}
      {!activePolicyId && (
        <div className="card-white p-6 sm:p-8 text-center space-y-4 border-dashed border-[#39ABAD]">
          <div className="w-12 h-12 rounded-xl bg-[rgba(57,171,173,0.12)] border border-[#39ABAD]/40 flex items-center justify-center text-[#006668] mx-auto">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div className="max-w-md mx-auto space-y-1">
            <h3 className="text-base font-bold text-[#003339]">Step 1: Select or Upload a Policy</h3>
            <p className="text-xs text-[#4A5859]">
              To compute deterministic coverage and deductibles, a health insurance policy must be loaded.
            </p>
          </div>

          {policies.length > 0 && (
            <div className="pt-2 max-w-sm mx-auto flex flex-wrap gap-2 justify-center">
              {policies.slice(0, 3).map((p) => (
                <button
                  key={p.id}
                  onClick={() => onSelectPolicy(p.id)}
                  className="btn-secondary px-3 py-1.5 text-xs font-semibold cursor-pointer truncate max-w-xs"
                >
                  Load {p.original_filename}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* SECTION 1: Treatment Scenario Builder */}
      <div className="space-y-4">
        <div className="flex items-center space-x-2 pb-1">
          <span className="w-6 h-6 rounded-full bg-[#003339] text-white text-xs font-bold flex items-center justify-center">
            1
          </span>
          <h3 className="text-base font-bold text-[#003339]">Configure Treatment & Hospital Scenario</h3>
        </div>

        <TreatmentScenarioForm
          policyId={activePolicyId}
          onCalculate={onCalculate}
          loading={estimating}
        />
      </div>

      {/* SECTION 2: Calculation Results & Breakdown */}
      {estimateResult ? (
        <div className="space-y-8 pt-4">
          <div className="flex items-center space-x-2 pb-1">
            <span className="w-6 h-6 rounded-full bg-[#006668] text-white text-xs font-bold flex items-center justify-center">
              2
            </span>
            <h3 className="text-base font-bold text-[#003339]">Audit & Financial Breakdown</h3>
          </div>

          <EstimationResultDashboard
            estimate={estimateResult}
            onRecalculate={onRecalculateRoom}
            loading={estimating}
          />

          {/* Scenario Sensitivity Section */}
          <ScenarioSensitivitySection
            currentEstimate={estimateResult}
            onToggleRoom={onRecalculateRoom}
            loading={estimating}
          />

          {/* Confidence & Uncertainty Section */}
          <ConfidenceSection />
        </div>
      ) : (
        <div className="card-white p-8 sm:p-10 text-center space-y-3 border-dashed border-[#E2E8E8]">
          <div className="w-12 h-12 rounded-xl bg-[#F7F7F8] border border-[#E2E8E8] flex items-center justify-center text-[#4A5859] mx-auto">
            <Scale className="w-6 h-6" />
          </div>
          <h4 className="text-sm font-bold text-[#003339]">Awaiting Treatment Scenario</h4>
          <p className="text-xs text-[#4A5859] max-w-md mx-auto">
            Select a medical procedure, city, and room category above, then click <strong>Calculate Out-of-Pocket Cost</strong> to view the transparent mathematical breakdown.
          </p>
        </div>
      )}
    </div>
  );
}
