import React, { useState, useEffect } from 'react';
import { Stethoscope, MapPin, Bed, Activity, Calculator, Loader2, Calendar } from 'lucide-react';
import { getTreatments } from '../services/api';

export default function TreatmentScenarioForm({ policyId, onCalculate, loading }) {
  const [procedures, setProcedures] = useState(['Appendectomy', 'Cataract Surgery', 'Knee Replacement', 'C-Section', 'Angioplasty']);
  const [cities, setCities] = useState(['Pune', 'Mumbai', 'Nagpur']);
  const [roomCategories, setRoomCategories] = useState(['Standard', 'Deluxe']);

  const [selectedProcedure, setSelectedProcedure] = useState('Appendectomy');
  const [selectedCity, setSelectedCity] = useState('Pune');
  const [selectedRoom, setSelectedRoom] = useState('Standard');
  const [hasPED, setHasPED] = useState(false);
  const [policyTenureMonths, setPolicyTenureMonths] = useState('24');

  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        const data = await getTreatments();
        if (data.procedures?.length) setProcedures(data.procedures);
        if (data.cities?.length) setCities(data.cities);
        if (data.room_categories?.length) setRoomCategories(data.room_categories);
      } catch (err) {
        console.error('Error fetching treatment metadata:', err);
      }
    };
    fetchMetadata();
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!policyId) return;

    onCalculate({
      policy_id: policyId,
      procedure: selectedProcedure,
      treatment: selectedProcedure,
      city: selectedCity,
      room_category: selectedRoom,
      condition: hasPED ? 'Pre-Existing Condition' : 'None',
      scenario: {
        is_ped: hasPED,
        policy_tenure_months: policyTenureMonths ? Number(policyTenureMonths) : 24
      }
    });
  };

  return (
    <div className="card-white p-6 sm:p-7 space-y-5">
      <div className="flex items-center space-x-3 pb-4 border-b border-[#E2E8E8]">
        <div className="w-10 h-10 rounded-xl bg-[rgba(57,171,173,0.12)] border border-[#39ABAD]/40 flex items-center justify-center text-[#006668]">
          <Stethoscope className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-base font-bold text-[#003339]">Treatment Scenario Builder</h3>
          <p className="text-xs text-[#4A5859]">Specify hospital procedure, city, room category, and policy tenure for validated cost estimation.</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Procedure Selection */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-[#003339] flex items-center space-x-1.5">
              <Stethoscope className="w-3.5 h-3.5 text-[#006668]" />
              <span>Medical Procedure</span>
            </label>
            <select
              value={selectedProcedure}
              onChange={(e) => setSelectedProcedure(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-[#E2E8E8] text-xs font-medium text-[#003339] focus:outline-hidden focus:border-[#006668] focus:ring-1 focus:ring-[#006668] transition-all"
            >
              {procedures.map((proc) => (
                <option key={proc} value={proc}>{proc}</option>
              ))}
            </select>
          </div>

          {/* City Selection */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-[#003339] flex items-center space-x-1.5">
              <MapPin className="w-3.5 h-3.5 text-[#006668]" />
              <span>City / Region</span>
            </label>
            <select
              value={selectedCity}
              onChange={(e) => setSelectedCity(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-[#E2E8E8] text-xs font-medium text-[#003339] focus:outline-hidden focus:border-[#006668] focus:ring-1 focus:ring-[#006668] transition-all"
            >
              {cities.map((city) => (
                <option key={city} value={city}>{city}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-1">
          {/* Room Category Selection */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-[#003339] flex items-center space-x-1.5">
              <Bed className="w-3.5 h-3.5 text-[#006668]" />
              <span>Hospital Room</span>
            </label>
            <div className="grid grid-cols-2 gap-2">
              {roomCategories.map((room) => (
                <button
                  key={room}
                  type="button"
                  onClick={() => setSelectedRoom(room)}
                  className={`py-2 px-2.5 rounded-xl text-xs font-semibold border transition-all cursor-pointer text-center ${
                    selectedRoom === room
                      ? 'bg-[#006668] text-white border-[#006668] shadow-2xs'
                      : 'bg-white text-[#4A5859] border-[#E2E8E8] hover:bg-[#F7F7F8]'
                  }`}
                >
                  {room}
                </button>
              ))}
            </div>
          </div>

          {/* Policy Active Tenure (Months) */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-[#003339] flex items-center space-x-1.5">
              <Calendar className="w-3.5 h-3.5 text-[#006668]" />
              <span>Policy Tenure</span>
            </label>
            <select
              value={policyTenureMonths}
              onChange={(e) => setPolicyTenureMonths(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-white border border-[#E2E8E8] text-xs font-medium text-[#003339] focus:outline-hidden focus:border-[#006668] transition-all"
            >
              <option value="6">6 Months (Initial / New)</option>
              <option value="12">12 Months (1 Year)</option>
              <option value="24">24 Months (2 Years)</option>
              <option value="36">36 Months (3 Years)</option>
              <option value="48">48+ Months (Fully Matured)</option>
            </select>
          </div>

          {/* Pre-existing Condition Toggle */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700 flex items-center space-x-1.5">
              <Activity className="w-3.5 h-3.5 text-emerald-700" />
              <span>Condition Type</span>
            </label>
            <button
              type="button"
              onClick={() => setHasPED(!hasPED)}
              className={`w-full py-2 px-3 rounded-xl text-xs font-semibold border transition-all flex items-center justify-between cursor-pointer ${
                hasPED
                  ? 'bg-amber-50 border-amber-300 text-amber-900'
                  : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
              }`}
            >
              <span>{hasPED ? 'Pre-Existing (PED)' : 'Standard'}</span>
              <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${hasPED ? 'bg-amber-200 text-amber-900' : 'bg-slate-100 text-slate-500'}`}>
                {hasPED ? 'PED Active' : 'None'}
              </span>
            </button>
          </div>
        </div>

        {/* Submit Button */}
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
                <span>Validating &amp; Calculating Estimate...</span>
              </>
            ) : (
              <>
                <Calculator className="w-4 h-4" />
                <span>Calculate Out-of-Pocket Cost</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
