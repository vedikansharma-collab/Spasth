import React, { useState, useEffect, useMemo } from 'react';
import { 
  Stethoscope, MapPin, Bed, Activity, Calculator, Loader2, 
  DollarSign, ShieldAlert, Hash, Info, CheckCircle2, AlertCircle, FileText, Sparkles
} from 'lucide-react';
import { getTreatments } from '../services/api';

export default function TreatmentScenarioForm({ policyId, activePolicy, onCalculate, loading }) {
  const [procedures, setProcedures] = useState([
    'Angioplasty',
    'Appendectomy',
    'Arthroscopy',
    'C-Section',
    'CABG',
    'Cataract Surgery',
    'Chemotherapy',
    'Cholecystectomy',
    'Dialysis',
    'Hemorrhoidectomy',
    'Hernia Repair',
    'Hip Replacement',
    'Hysterectomy',
    'Kidney Stone Removal',
    'Knee Replacement',
    'Normal Delivery',
    'Septoplasty',
    'Thyroidectomy',
    'Tonsillectomy',
    'Tympanoplasty'
  ]);
  const [cities, setCities] = useState(['Pune', 'Mumbai', 'Nagpur']);
  const [roomCategories, setRoomCategories] = useState(['Standard', 'Deluxe']);
  const [benchmarks, setBenchmarks] = useState([]);

  const [selectedProcedure, setSelectedProcedure] = useState('Appendectomy');
  const [selectedCity, setSelectedCity] = useState('Pune');
  const [selectedRoom, setSelectedRoom] = useState('Standard');
  
  // Cost Mode: 'reference' (default from dataset) vs 'actual' (user entered bill)
  const [costMode, setCostMode] = useState('reference');
  const [actualCost, setActualCost] = useState('85000');
  const [quantity, setQuantity] = useState('1');
  const [nonCoveredExpense, setNonCoveredExpense] = useState('0');
  const [hasPED, setHasPED] = useState(false);
  const [policyTenureMonths, setPolicyTenureMonths] = useState('24');

  // Load dataset metadata from backend
  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        const data = await getTreatments();
        if (data.procedures?.length) setProcedures(data.procedures);
        if (data.cities?.length) setCities(data.cities);
        if (data.room_categories?.length) setRoomCategories(data.room_categories);
        if (data.benchmarks?.length) setBenchmarks(data.benchmarks);
      } catch (err) {
        console.error('Error fetching treatment metadata:', err);
      }
    };
    fetchMetadata();
  }, []);

  // Lookup matched benchmark record from dataset
  const activeBenchmark = useMemo(() => {
    if (!benchmarks || benchmarks.length === 0) return null;
    return benchmarks.find(b => {
      const procName = b.canonical_name || b.procedure || '';
      return procName.toLowerCase() === selectedProcedure.toLowerCase() &&
             b.city.toLowerCase() === selectedCity.toLowerCase();
    });
  }, [benchmarks, selectedProcedure, selectedCity]);

  // Derived reference cost from dataset or fallback defaults
  const referenceCost = useMemo(() => {
    if (activeBenchmark?.reference_cost) return activeBenchmark.reference_cost;
    if (activeBenchmark?.cost_min && activeBenchmark?.cost_max) {
      return (activeBenchmark.cost_min + activeBenchmark.cost_max) / 2;
    }
    // Standard repository fallback benchmarks for all 20 procedures
    const fallbacks = {
      'Appendectomy': { 'Pune': 85000, 'Mumbai': 127500, 'Nagpur': 63500 },
      'Cataract Surgery': { 'Pune': 40000, 'Mumbai': 55000, 'Nagpur': 31500 },
      'Knee Replacement': { 'Pune': 210000, 'Mumbai': 305000, 'Nagpur': 165000 },
      'C-Section': { 'Pune': 72500, 'Mumbai': 110000, 'Nagpur': 51000 },
      'Angioplasty': { 'Pune': 190000, 'Mumbai': 265000, 'Nagpur': 150000 },
      'Hernia Repair': { 'Pune': 65000, 'Mumbai': 95000, 'Nagpur': 52000 },
      'Cholecystectomy': { 'Pune': 80000, 'Mumbai': 115000, 'Nagpur': 62000 },
      'Kidney Stone Removal': { 'Pune': 55000, 'Mumbai': 78000, 'Nagpur': 42000 },
      'Hysterectomy': { 'Pune': 95000, 'Mumbai': 135000, 'Nagpur': 75000 },
      'Hip Replacement': { 'Pune': 230000, 'Mumbai': 325000, 'Nagpur': 180000 },
      'CABG': { 'Pune': 295000, 'Mumbai': 420000, 'Nagpur': 235000 },
      'Normal Delivery': { 'Pune': 48000, 'Mumbai': 72000, 'Nagpur': 36000 },
      'Tonsillectomy': { 'Pune': 42000, 'Mumbai': 60000, 'Nagpur': 32000 },
      'Hemorrhoidectomy': { 'Pune': 45000, 'Mumbai': 65000, 'Nagpur': 35000 },
      'Dialysis': { 'Pune': 3200, 'Mumbai': 4500, 'Nagpur': 2600 },
      'Chemotherapy': { 'Pune': 24000, 'Mumbai': 35000, 'Nagpur': 19000 },
      'Tympanoplasty': { 'Pune': 52000, 'Mumbai': 75000, 'Nagpur': 40000 },
      'Septoplasty': { 'Pune': 48000, 'Mumbai': 68000, 'Nagpur': 38000 },
      'Arthroscopy': { 'Pune': 85000, 'Mumbai': 120000, 'Nagpur': 68000 },
      'Thyroidectomy': { 'Pune': 78000, 'Mumbai': 110000, 'Nagpur': 60000 }
    };
    return fallbacks[selectedProcedure]?.[selectedCity] || 85000;
  }, [activeBenchmark, selectedProcedure, selectedCity]);

  // Sync actualCost input placeholder when procedure or city changes
  useEffect(() => {
    if (costMode === 'actual') {
      setActualCost(String(referenceCost));
    }
  }, [referenceCost, costMode]);

  const formatINR = (amt) => {
    if (!amt || isNaN(amt)) return '₹0';
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(amt);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!policyId) return;

    const finalTreatmentCost = costMode === 'actual' ? Number(actualCost) : Number(referenceCost);

    onCalculate({
      policy_id: policyId,
      procedure_name: selectedProcedure,
      procedure: selectedProcedure,
      treatment: selectedProcedure,
      city: selectedCity,
      treatment_cost: finalTreatmentCost,
      quantity: quantity ? Number(quantity) : 1,
      non_covered_expense: nonCoveredExpense ? Number(nonCoveredExpense) : 0,
      room_category: selectedRoom,
      cost_mode: costMode,
      use_actual_cost: costMode === 'actual',
      condition: hasPED ? 'Pre-Existing Condition' : 'None',
      policy_tenure_months: policyTenureMonths ? Number(policyTenureMonths) : 24,
      is_ped: hasPED,
      scenario: {
        is_ped: hasPED,
        policy_tenure_months: policyTenureMonths ? Number(policyTenureMonths) : 24
      }
    });
  };

  return (
    <div className="card-white p-6 sm:p-7 space-y-6">
      {/* 1. Header & Source-of-Truth Policy Banner */}
      <div className="space-y-3 pb-4 border-b border-[#E2E8E8]">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-[rgba(57,171,173,0.12)] border border-[#39ABAD]/40 flex items-center justify-center text-[#006668]">
              <Stethoscope className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-[#003339]">Claim &amp; Treatment Scenario</h3>
              <p className="text-xs text-[#4A5859]">Select treatment and claim details. Policy terms are automatically resolved from your policy.</p>
            </div>
          </div>

          {activePolicy ? (
            <div className="flex items-center space-x-2 bg-[#F7F7F8] px-3 py-1.5 rounded-xl border border-[#E2E8E8]">
              <FileText className="w-4 h-4 text-[#006668]" />
              <div className="text-left">
                <span className="text-[10px] uppercase font-bold text-[#4A5859] block">Source Policy</span>
                <span className="text-xs font-semibold text-[#003339] truncate max-w-[200px] block">
                  {activePolicy.original_filename || 'Uploaded Policy'}
                </span>
              </div>
            </div>
          ) : (
            <div className="flex items-center space-x-2 bg-amber-50 px-3 py-1.5 rounded-xl border border-amber-200 text-amber-800 text-xs font-semibold">
              <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
              <span>No Policy Selected</span>
            </div>
          )}
        </div>

        {/* Notice explaining that policy values come from policy */}
        <div className="p-3 rounded-xl bg-[#F7F7F8] border border-[#E2E8E8] flex items-start space-x-2.5 text-xs text-[#4A5859]">
          <Info className="w-4 h-4 text-[#006668] shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            <strong className="text-[#003339]">Automated Policy Rule Retrieval:</strong> Your uploaded policy is the sole source of truth for <strong>Sum Insured</strong>, <strong>Co-payment (0% or specified)</strong>, <strong>Procedure Sub-limits</strong>, <strong>Room Rent Rules</strong>, and <strong>Deductibles</strong>. You only provide treatment and bill details below.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* 2. Treatment & City Selection from Canonical Dataset */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-[#003339] flex items-center justify-between">
              <span className="flex items-center space-x-1.5">
                <Stethoscope className="w-3.5 h-3.5 text-[#006668]" />
                <span>Select Treatment / Procedure</span>
              </span>
              <span className="text-[10px] text-[#006668] font-bold">SPASTH Dataset</span>
            </label>
            <select
              value={selectedProcedure}
              onChange={(e) => setSelectedProcedure(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-[#E2E8E8] text-xs font-semibold text-[#003339] focus:outline-hidden focus:border-[#006668] focus:ring-1 focus:ring-[#006668] transition-all cursor-pointer"
            >
              {procedures.map((proc) => (
                <option key={proc} value={proc}>{proc}</option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-[#003339] flex items-center justify-between">
              <span className="flex items-center space-x-1.5">
                <MapPin className="w-3.5 h-3.5 text-[#006668]" />
                <span>City / Tier Region</span>
              </span>
              <span className="text-[10px] text-[#4A5859] font-medium font-mono">
                {activeBenchmark?.city_tier || 'Tier-1'}
              </span>
            </label>
            <select
              value={selectedCity}
              onChange={(e) => setSelectedCity(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-[#E2E8E8] text-xs font-semibold text-[#003339] focus:outline-hidden focus:border-[#006668] focus:ring-1 focus:ring-[#006668] transition-all cursor-pointer"
            >
              {cities.map((city) => (
                <option key={city} value={city}>{city}</option>
              ))}
            </select>
          </div>
        </div>

        {/* 3. Treatment Cost Source Mode (Reference vs Actual Bill) */}
        <div className="space-y-3 p-4 rounded-xl bg-[#F7F7F8] border border-[#E2E8E8]">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-[#003339] flex items-center space-x-1.5">
              <DollarSign className="w-3.5 h-3.5 text-[#006668]" />
              <span>Treatment Cost Source</span>
            </span>
            <span className="text-[10px] font-bold text-[#006668] uppercase tracking-wide">
              {costMode === 'reference' ? 'Dataset Baseline' : 'User Provided'}
            </span>
          </div>

          {/* Toggle buttons for Reference vs Actual Cost */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => setCostMode('reference')}
              className={`p-3 rounded-xl text-left border transition-all cursor-pointer ${
                costMode === 'reference'
                  ? 'bg-white border-[#006668] shadow-xs'
                  : 'bg-transparent border-[#E2E8E8] hover:bg-white/60 text-[#4A5859]'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#003339]">Use Reference Treatment Cost</span>
                {costMode === 'reference' && <CheckCircle2 className="w-4 h-4 text-[#006668]" />}
              </div>
              <p className="text-[11px] text-[#4A5859] mt-1 font-mono">
                {activeBenchmark?.cost_min && activeBenchmark?.cost_max 
                  ? `${formatINR(activeBenchmark.cost_min)} – ${formatINR(activeBenchmark.cost_max)}`
                  : formatINR(referenceCost)}
                <span className="text-[10px] font-sans block sm:inline sm:ml-1">
                  ({selectedProcedure} • {selectedCity})
                </span>
              </p>
              <span className="inline-block text-[10px] text-[#006668] font-bold bg-[rgba(0,102,104,0.08)] px-2 py-0.5 rounded mt-1">
                SPASTH Benchmark Dataset
              </span>
            </button>

            <button
              type="button"
              onClick={() => setCostMode('actual')}
              className={`p-3 rounded-xl text-left border transition-all cursor-pointer ${
                costMode === 'actual'
                  ? 'bg-white border-[#006668] shadow-xs'
                  : 'bg-transparent border-[#E2E8E8] hover:bg-white/60 text-[#4A5859]'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#003339]">Enter Actual Hospital Bill</span>
                {costMode === 'actual' && <CheckCircle2 className="w-4 h-4 text-[#006668]" />}
              </div>
              <p className="text-[11px] text-[#4A5859] mt-1">
                Enter your exact medical invoice quotation or final bill amount.
              </p>
              <span className="inline-block text-[10px] text-[#4A5859] font-bold bg-[#E2E8E8]/60 px-2 py-0.5 rounded mt-1">
                Custom Invoice Amount
              </span>
            </button>
          </div>

          {/* Conditional Input for Actual Bill */}
          {costMode === 'actual' ? (
            <div className="pt-2 space-y-1.5 animate-fade-in">
              <label className="text-xs font-semibold text-[#003339] flex items-center justify-between">
                <span>User-Provided Actual Treatment Cost (₹)</span>
                <span className="text-[10px] text-[#006668] font-mono">Editable</span>
              </label>
              <input
                type="number"
                min="1000"
                step="1000"
                value={actualCost}
                onChange={(e) => setActualCost(e.target.value)}
                placeholder="e.g. 85000"
                className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-[#006668] text-sm font-bold text-[#003339] focus:outline-hidden focus:ring-1 focus:ring-[#006668] transition-all font-mono"
              />
              <span className="text-[11px] text-[#4A5859] block">
                Identified as: <strong className="text-[#003339]">User-provided actual treatment cost</strong>.
              </span>
            </div>
          ) : (
            <div className="text-[11px] text-[#4A5859] pt-1">
              <em>This estimate uses the reference treatment cost available in the SPASTH treatment dataset ({formatINR(referenceCost)}). Actual hospital billing may differ.</em>
            </div>
          )}
        </div>

        {/* 4. Quantity and Non-Covered Medical Expenses */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-[#003339] flex items-center space-x-1.5">
              <Hash className="w-3.5 h-3.5 text-[#006668]" />
              <span>Quantity</span>
            </label>
            <input
              type="number"
              min="1"
              max="10"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-[#E2E8E8] text-xs font-medium text-[#003339] focus:outline-hidden focus:border-[#006668] focus:ring-1 focus:ring-[#006668] transition-all font-mono"
            />
            <span className="text-[10px] text-[#4A5859]">Number of procedures / units (default: 1)</span>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-[#003339] flex items-center space-x-1.5">
              <ShieldAlert className="w-3.5 h-3.5 text-[#006668]" />
              <span>Non-Covered Medical Items (₹)</span>
            </label>
            <input
              type="number"
              min="0"
              step="500"
              value={nonCoveredExpense}
              onChange={(e) => setNonCoveredExpense(e.target.value)}
              placeholder="0"
              className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-[#E2E8E8] text-xs font-medium text-[#003339] focus:outline-hidden focus:border-[#006668] focus:ring-1 focus:ring-[#006668] transition-all font-mono"
            />
            <span className="text-[10px] text-[#4A5859]">Consumables, administrative fees, or non-payable items (default: ₹0)</span>
          </div>
        </div>

        {/* 5. Hospital Room Category */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-[#003339] flex items-center justify-between">
            <span className="flex items-center space-x-1.5">
              <Bed className="w-3.5 h-3.5 text-[#006668]" />
              <span>Hospital Room Category</span>
            </span>
            <span className="text-[10px] text-[#4A5859]">Standard has no upgrade penalty</span>
          </label>
          <div className="grid grid-cols-2 gap-2">
            {roomCategories.map((room) => (
              <button
                key={room}
                type="button"
                onClick={() => setSelectedRoom(room)}
                className={`py-2 px-3 rounded-xl text-xs font-bold border transition-all cursor-pointer text-center ${
                  selectedRoom === room
                    ? 'bg-[#006668] text-white border-[#006668] shadow-2xs'
                    : 'bg-white text-[#4A5859] border-[#E2E8E8] hover:bg-[#F7F7F8]'
                }`}
              >
                {room} Room
              </button>
            ))}
          </div>
        </div>

        {/* 6. Submit Button */}
        <div className="pt-2">
          <button
            type="submit"
            disabled={loading || !policyId}
            className={`w-full py-3.5 rounded-xl font-bold text-sm flex items-center justify-center space-x-2 transition-all cursor-pointer ${
              loading || !policyId
                ? 'bg-slate-100 text-slate-400 border border-slate-200 cursor-not-allowed'
                : 'btn-primary'
            }`}
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-white" />
                <span>Running Deterministic Math Engine...</span>
              </>
            ) : (
              <>
                <Calculator className="w-4 h-4" />
                <span>Estimate Out-of-Pocket Cost</span>
              </>
            )}
          </button>

          {!policyId && (
            <p className="text-center text-xs text-[#D51B1D] font-medium mt-2">
              Please upload or select an insurance policy before calculating an estimate.
            </p>
          )}
        </div>
      </form>
    </div>
  );
}
