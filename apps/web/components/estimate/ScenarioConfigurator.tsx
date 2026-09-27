'use client';

import { useState, useEffect } from 'react';
import { getProcedureCosts } from '@/lib/api';
import { useScenarioStore } from '@/store/scenarioStore';
import type { Procedure, RoomCategory, HospitalCostScenario } from '@policy-estimator/types';
import { RefreshCw, Settings2, IndianRupee, Clock, MapPin, Bed } from 'lucide-react';

interface ScenarioConfiguratorProps {
  procedures: Procedure[];
  policyId: string;
  isReady: boolean;
  isCalculating: boolean;
  onRecalculate: (procCode: string, room: RoomCategory, days: number, city: string) => void;
}

const ROOM_CATEGORIES: { value: RoomCategory; label: string; desc: string }[] = [
  { value: 'GENERAL', label: 'General Ward', desc: 'Shared ward, lowest cost' },
  { value: 'TWIN_SHARING', label: 'Twin Sharing', desc: '2-bed room' },
  { value: 'SINGLE_PRIVATE', label: 'Single Private', desc: 'Private room' },
  { value: 'DELUXE', label: 'Deluxe/Suite', desc: 'Premium room' },
];

const CITIES = [
  'National Average',
  'Mumbai',
  'Delhi',
  'Bangalore',
  'Chennai',
  'Hyderabad',
  'Kolkata',
  'Pune',
];

export function ScenarioConfigurator({
  procedures,
  policyId,
  isReady,
  isCalculating,
  onRecalculate,
}: ScenarioConfiguratorProps) {
  const { selectedProcedureCode, selectedRoomCategory, stayDays, city, setScenario } = useScenarioStore();

  const [costs, setCosts] = useState<HospitalCostScenario[]>([]);
  const [localProc, setLocalProc] = useState(selectedProcedureCode);
  const [localRoom, setLocalRoom] = useState<RoomCategory>(selectedRoomCategory);
  const [localDays, setLocalDays] = useState(stayDays);
  const [localCity, setLocalCity] = useState(city);
  const [isDirty, setIsDirty] = useState(false);
  const [selectedCost, setSelectedCost] = useState<HospitalCostScenario | null>(null);

  // Load costs when procedure changes
  useEffect(() => {
    if (!localProc) return;
    getProcedureCosts(localProc)
      .then((c) => {
        setCosts(c);
        const match = c.find((x) => x.roomCategory === localRoom);
        setSelectedCost(match || c[0] || null);
      })
      .catch(() => {});
  }, [localProc, localRoom]);

  const handleChange = (updates: Partial<{ proc: string; room: RoomCategory; days: number; city: string }>) => {
    if (updates.proc !== undefined) setLocalProc(updates.proc);
    if (updates.room !== undefined) setLocalRoom(updates.room);
    if (updates.days !== undefined) setLocalDays(updates.days);
    if (updates.city !== undefined) setLocalCity(updates.city);
    setIsDirty(true);
  };

  const handleApply = () => {
    setScenario({
      procedureCode: localProc,
      roomCategory: localRoom,
      stayDays: localDays,
      city: localCity,
    });
    onRecalculate(localProc, localRoom, localDays, localCity);
    setIsDirty(false);
  };

  const currentProcedure = procedures.find((p) => p.code === localProc);

  return (
    <div className="bg-slate-900/60 border border-slate-700/50 rounded-2xl backdrop-blur-sm overflow-hidden">
      <div className="p-4 border-b border-slate-800/60 flex items-center gap-2">
        <Settings2 className="w-4 h-4 text-indigo-400" />
        <h3 className="text-sm font-bold text-white">Treatment Scenario</h3>
      </div>

      <div className="p-4 space-y-5">
        {/* Procedure Selection */}
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-2">Medical Procedure</label>
          <select
            value={localProc}
            onChange={(e) => handleChange({ proc: e.target.value })}
            disabled={!isReady}
            className="w-full bg-slate-800/80 border border-slate-700/60 text-white text-sm rounded-xl px-3 py-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {procedures.map((p) => (
              <option key={p.code} value={p.code}>
                {p.name}
              </option>
            ))}
          </select>
          {currentProcedure && (
            <p className="text-xs text-slate-500 mt-1.5">{currentProcedure.description}</p>
          )}
        </div>

        {/* Room Category */}
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-2">
            <Bed className="w-3.5 h-3.5 inline mr-1" />
            Room Category
          </label>
          <div className="grid grid-cols-2 gap-2">
            {ROOM_CATEGORIES.map(({ value, label, desc }) => {
              const costData = costs.find((c) => c.roomCategory === value);
              return (
                <button
                  key={value}
                  onClick={() => handleChange({ room: value })}
                  disabled={!isReady}
                  className={`text-left p-3 rounded-xl border text-xs transition-all disabled:opacity-50 disabled:cursor-not-allowed ${
                    localRoom === value
                      ? 'bg-indigo-900/60 border-indigo-600/60 text-white'
                      : 'bg-slate-800/40 border-slate-700/40 text-slate-400 hover:border-slate-600'
                  }`}
                >
                  <div className="font-medium mb-0.5 text-white">{label}</div>
                  <div className="text-slate-500">{desc}</div>
                  {costData && (
                    <div className="text-indigo-400 font-medium mt-1">₹{costData.roomRate.toLocaleString('en-IN')}/day</div>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Stay Duration */}
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-2">
            <Clock className="w-3.5 h-3.5 inline mr-1" />
            Stay Duration: <span className="text-white">{localDays} {localDays === 1 ? 'day' : 'days'}</span>
          </label>
          <input
            type="range"
            min={1}
            max={30}
            value={localDays}
            onChange={(e) => handleChange({ days: parseInt(e.target.value) })}
            disabled={!isReady}
            className="w-full accent-indigo-500 disabled:opacity-50"
          />
          <div className="flex justify-between text-xs text-slate-600 mt-0.5">
            <span>1 day</span>
            <span>30 days</span>
          </div>
        </div>

        {/* City */}
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-2">
            <MapPin className="w-3.5 h-3.5 inline mr-1" />
            City
          </label>
          <select
            value={localCity}
            onChange={(e) => handleChange({ city: e.target.value })}
            disabled={!isReady}
            className="w-full bg-slate-800/80 border border-slate-700/60 text-white text-sm rounded-xl px-3 py-2.5 focus:ring-2 focus:ring-indigo-500 outline-none disabled:opacity-50"
          >
            {CITIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        {/* Cost Preview */}
        {selectedCost && (
          <div className="p-3 bg-slate-800/60 rounded-xl border border-slate-700/40">
            <p className="text-xs font-medium text-slate-400 mb-2 flex items-center gap-1">
              <IndianRupee className="w-3.5 h-3.5" />
              Benchmark Hospital Cost
            </p>
            <div className="space-y-1.5">
              {[
                { label: 'Room cost', value: selectedCost.roomRate * localDays },
                { label: 'Proportionate costs', value: selectedCost.proportionateCosts },
                { label: 'Non-proportionate', value: selectedCost.nonProportionateCosts },
                { label: 'Other charges', value: selectedCost.otherCosts },
              ].map(({ label, value }) => (
                <div key={label} className="flex justify-between text-xs">
                  <span className="text-slate-500">{label}</span>
                  <span className="text-slate-300">₹{value.toLocaleString('en-IN')}</span>
                </div>
              ))}
              <div className="border-t border-slate-700 pt-1.5 flex justify-between text-sm font-semibold">
                <span className="text-slate-300">Total Bill</span>
                <span className="text-white">
                  ₹{(selectedCost.roomRate * localDays + selectedCost.proportionateCosts + selectedCost.nonProportionateCosts + selectedCost.otherCosts).toLocaleString('en-IN')}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Recalculate Button */}
        <button
          onClick={handleApply}
          disabled={!isReady || isCalculating}
          className={`w-full flex items-center justify-center gap-2 py-3 rounded-xl font-semibold text-sm transition-all ${
            isDirty && isReady && !isCalculating
              ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-900/50'
              : 'bg-slate-800/60 text-slate-400 border border-slate-700/40'
          } disabled:cursor-not-allowed`}
        >
          {isCalculating ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              Calculating...
            </>
          ) : (
            <>
              <RefreshCw className="w-4 h-4" />
              {isDirty ? 'Apply & Recalculate' : 'Recalculate'}
            </>
          )}
        </button>
      </div>
    </div>
  );
}
