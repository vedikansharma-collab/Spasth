import React from 'react';
import { Sliders, ArrowRight, AlertCircle, Bed, MapPin } from 'lucide-react';

export default function ScenarioSensitivitySection({ currentEstimate, onToggleRoom, onSelectCity, loading }) {
  const isDeluxe = currentEstimate?.room_category === 'Deluxe';

  return (
    <section className="py-16 bg-offwhite border-t border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        <div className="text-center max-w-2xl mx-auto space-y-3">
          <h2 className="text-3xl font-black text-slate-900 tracking-tight">
            See What Changes Your Estimate
          </h2>
          <p className="text-sm text-slate-600">
            Changing a scenario input can change the applicable policy rules and estimated patient liability.
          </p>
        </div>

        {/* Scenario Comparison Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Card A: Standard Room Scenario */}
          <div className={`card-white p-6 space-y-4 border-2 transition-all ${!isDeluxe ? 'border-emerald-600 bg-white shadow-md' : 'border-slate-200 bg-slate-50/50'}`}>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-2">
                <Bed className="w-5 h-5 text-emerald-700" />
                <h3 className="font-bold text-slate-900 text-base">Scenario A: Standard Room</h3>
              </div>
              <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
                100% Eligible Coverage
              </span>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              Standard single room stays within policy daily room cap (₹5,000/day). No proportionate deduction penalty applied.
            </p>

            <button
              disabled={loading || !isDeluxe}
              onClick={() => onToggleRoom('Standard')}
              className={`w-full py-2.5 rounded-xl text-xs font-bold cursor-pointer transition-all ${
                !isDeluxe ? 'bg-emerald-700 text-white shadow-2xs' : 'btn-secondary'
              }`}
            >
              {!isDeluxe ? 'Active Scenario Result' : 'Switch to Standard Room Scenario'}
            </button>
          </div>

          {/* Card B: Deluxe Room Upgrade Scenario */}
          <div className={`card-white p-6 space-y-4 border-2 transition-all ${isDeluxe ? 'border-amber-500 bg-white shadow-md' : 'border-slate-200 bg-slate-50/50'}`}>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-2">
                <Bed className="w-5 h-5 text-amber-600" />
                <h3 className="font-bold text-slate-900 text-base">Scenario B: Deluxe Room Upgrade</h3>
              </div>
              <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-amber-50 text-amber-800 border border-amber-200">
                30% Proportionate Penalty
              </span>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              Upgrading to Deluxe Room exceeds daily cap, triggering a mandatory 30% proportionate deduction penalty across associated hospital charges.
            </p>

            <button
              disabled={loading || isDeluxe}
              onClick={() => onToggleRoom('Deluxe')}
              className={`w-full py-2.5 rounded-xl text-xs font-bold cursor-pointer transition-all ${
                isDeluxe ? 'bg-amber-600 text-white shadow-2xs' : 'btn-secondary'
              }`}
            >
              {isDeluxe ? 'Active Scenario Result' : 'Switch to Deluxe Room Scenario'}
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
