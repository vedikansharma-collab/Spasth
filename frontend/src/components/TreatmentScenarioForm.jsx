import React, { useState, useEffect } from 'react';
import { Stethoscope, MapPin, Bed, Activity, Calculator, Loader2 } from 'lucide-react';
import { getTreatments } from '../services/api';

export default function TreatmentScenarioForm({ policyId, onCalculate, loading }) {
  const [procedures, setProcedures] = useState(['Appendectomy', 'Cataract Surgery', 'Knee Replacement', 'C-Section', 'Angioplasty']);
  const [cities, setCities] = useState(['Pune', 'Mumbai', 'Nagpur']);
  const [roomCategories, setRoomCategories] = useState(['Standard', 'Deluxe']);

  const [selectedProcedure, setSelectedProcedure] = useState('Appendectomy');
  const [selectedCity, setSelectedCity] = useState('Pune');
  const [selectedRoom, setSelectedRoom] = useState('Standard');
  const [hasPED, setHasPED] = useState(false);

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
      city: selectedCity,
      room_category: selectedRoom,
      condition: hasPED ? 'Pre-Existing Condition' : 'None'
    });
  };

  return (
    <div className="card-white p-6 sm:p-7 space-y-5">
      <div className="flex items-center space-x-3 pb-4 border-b border-slate-100">
        <div className="w-10 h-10 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700">
          <Stethoscope className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-base font-bold text-slate-900">Treatment Scenario Builder</h3>
          <p className="text-xs text-slate-500">Specify hospital procedure, city, and room category for cost calculation.</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Procedure Selection */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700 flex items-center space-x-1.5">
              <Stethoscope className="w-3.5 h-3.5 text-emerald-700" />
              <span>Medical Procedure</span>
            </label>
            <select
              value={selectedProcedure}
              onChange={(e) => setSelectedProcedure(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-slate-200 text-xs font-medium text-slate-900 focus:outline-none focus:border-emerald-600 focus:ring-1 focus:ring-emerald-600 transition-all"
            >
              {procedures.map((proc) => (
                <option key={proc} value={proc}>{proc}</option>
              ))}
            </select>
          </div>

          {/* City Selection */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700 flex items-center space-x-1.5">
              <MapPin className="w-3.5 h-3.5 text-emerald-700" />
              <span>City / Region</span>
            </label>
            <select
              value={selectedCity}
              onChange={(e) => setSelectedCity(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-slate-200 text-xs font-medium text-slate-900 focus:outline-none focus:border-emerald-600 focus:ring-1 focus:ring-emerald-600 transition-all"
            >
              {cities.map((city) => (
                <option key={city} value={city}>{city}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
          {/* Room Category Selection */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700 flex items-center space-x-1.5">
              <Bed className="w-3.5 h-3.5 text-emerald-700" />
              <span>Hospital Room Category</span>
            </label>
            <div className="grid grid-cols-2 gap-2">
              {roomCategories.map((room) => (
                <button
                  key={room}
                  type="button"
                  onClick={() => setSelectedRoom(room)}
                  className={`py-2 px-3 rounded-xl text-xs font-semibold border transition-all cursor-pointer ${
                    selectedRoom === room
                      ? 'bg-emerald-700 text-white border-emerald-700 shadow-2xs'
                      : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  {room} Room
                </button>
              ))}
            </div>
          </div>

          {/* Pre-existing Condition Toggle */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700 flex items-center space-x-1.5">
              <Activity className="w-3.5 h-3.5 text-emerald-700" />
              <span>Pre-Existing Disease (PED)</span>
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
              <span>{hasPED ? 'PED Declared' : 'No Prior Condition'}</span>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${hasPED ? 'bg-amber-200 text-amber-900' : 'bg-slate-100 text-slate-500'}`}>
                {hasPED ? 'Waiting Rules' : 'Standard'}
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
                <span>Calculating Estimate...</span>
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
