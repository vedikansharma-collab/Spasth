'use client';

import type { CalculationResponse } from '@policy-estimator/types';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts';
import { TrendingDown, TrendingUp, AlertTriangle, CheckCircle2, Info } from 'lucide-react';

interface ResultsDashboardProps {
  calculation: CalculationResponse | null;
  isLoading: boolean;
}

const PIE_COLORS = ['#6366f1', '#ef4444'];
const BAR_COLORS = {
  ROOM: '#818cf8',
  PROPORTIONATE: '#a78bfa',
  NON_PROPORTIONATE: '#c4b5fd',
  OTHER: '#ddd6fe',
  ADJUSTMENT: '#f87171',
};

function fmt(n: number) {
  return `₹${Math.round(n).toLocaleString('en-IN')}`;
}

export function ResultsDashboard({ calculation, isLoading }: ResultsDashboardProps) {
  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-24 bg-slate-800/40 rounded-2xl animate-pulse" />
        ))}
      </div>
    );
  }

  if (!calculation) {
    return (
      <div className="bg-slate-900/60 border border-slate-700/50 rounded-2xl p-8 text-center">
        <div className="w-14 h-14 bg-slate-800 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <Info className="w-7 h-7 text-slate-600" />
        </div>
        <p className="text-slate-400">Configure your scenario and click Calculate to see results</p>
      </div>
    );
  }

  const { result, breakdown, hospital, scenario, status, confidence, warnings, unknowns } = calculation;
  const isIncomplete = status !== 'CALCULATED';

  const pieData = [
    { name: 'Insurer Pays', value: result.finalInsurerPay },
    { name: 'You Pay', value: result.outOfPocket },
  ];

  const barData = breakdown
    .filter((b) => b.hospitalBilled > 0 || b.category === 'ADJUSTMENT')
    .map((b) => ({
      name: b.name.length > 20 ? b.name.slice(0, 18) + '…' : b.name,
      Billed: b.hospitalBilled,
      'Insurer Covers': b.insurerCovered,
      'You Pay': b.patientLiability,
      category: b.category,
    }));

  return (
    <div className="space-y-4">
      {/* Status Banner */}
      {isIncomplete && (
        <div className="flex items-center gap-3 p-4 bg-yellow-950/60 border border-yellow-800/50 rounded-xl">
          <AlertTriangle className="w-5 h-5 text-yellow-400 shrink-0" />
          <div>
            <p className="text-sm font-semibold text-yellow-300">Incomplete Calculation</p>
            <p className="text-xs text-yellow-400/80">
              Some policy rules could not be determined. Please verify room rent clause with your insurer.
            </p>
          </div>
        </div>
      )}

      {/* Warnings */}
      {warnings.length > 0 && (
        <div className="space-y-1.5">
          {warnings.map((w, i) => (
            <div key={i} className="flex items-center gap-2 text-xs text-orange-300 bg-orange-950/40 border border-orange-800/30 rounded-lg px-3 py-2">
              <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
              {w}
            </div>
          ))}
        </div>
      )}

      {/* Main KPI Cards */}
      <div className="grid grid-cols-2 gap-3">
        {/* Insurer Pays */}
        <div className="bg-gradient-to-br from-indigo-950/80 to-blue-950/80 border border-indigo-700/50 rounded-2xl p-5">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="w-4 h-4 text-indigo-400" />
            <p className="text-xs text-indigo-300 font-medium">Insurer Pays</p>
          </div>
          <p className="text-3xl font-black text-white tracking-tight">{fmt(result.finalInsurerPay)}</p>
          <p className="text-xs text-slate-400 mt-1">
            {hospital.totalBill > 0
              ? `${Math.round((result.finalInsurerPay / hospital.totalBill) * 100)}% of total bill`
              : 'of total bill'}
          </p>
        </div>

        {/* You Pay */}
        <div className="bg-gradient-to-br from-red-950/80 to-rose-950/80 border border-red-800/50 rounded-2xl p-5">
          <div className="flex items-center gap-2 mb-3">
            <TrendingDown className="w-4 h-4 text-red-400" />
            <p className="text-xs text-red-300 font-medium">You Pay (OOP)</p>
          </div>
          <p className="text-3xl font-black text-white tracking-tight">{fmt(result.outOfPocket)}</p>
          <p className="text-xs text-slate-400 mt-1">Out-of-pocket expense</p>
        </div>
      </div>

      {/* Confidence Indicators */}
      <div className="grid grid-cols-3 gap-2">
        {(
          [
            { key: 'policyExtraction', label: 'Policy Extraction' },
            { key: 'costMatching', label: 'Cost Matching' },
            { key: 'calculation', label: 'Calculation' },
          ] as const
        ).map(({ key, label }) => {
          const level = confidence[key];
          return (
            <div
              key={key}
              className={`p-2.5 rounded-xl border text-center ${
                level === 'HIGH'
                  ? 'bg-emerald-950/40 border-emerald-800/40'
                  : level === 'MEDIUM'
                  ? 'bg-yellow-950/40 border-yellow-800/40'
                  : 'bg-red-950/40 border-red-800/40'
              }`}
            >
              <p className={`text-xs font-bold ${level === 'HIGH' ? 'text-emerald-400' : level === 'MEDIUM' ? 'text-yellow-400' : 'text-red-400'}`}>
                {level}
              </p>
              <p className="text-xs text-slate-500">{label}</p>
            </div>
          );
        })}
      </div>

      {/* Scenario Details */}
      <div className="bg-slate-900/60 border border-slate-700/50 rounded-2xl p-4">
        <p className="text-xs font-medium text-slate-400 mb-3">Scenario — {scenario.procedureName}</p>
        <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-xs">
          {[
            { label: 'Total Hospital Bill', value: fmt(hospital.totalBill), highlight: true },
            { label: 'Room Category', value: scenario.roomCategory.replace(/_/g, ' ') },
            { label: 'Room Rate', value: `${fmt(hospital.roomRate)}/day` },
            { label: 'Stay Duration', value: `${scenario.stayDays} days` },
            { label: 'Allowed Room Rent', value: fmt(result.allowedRoomRent) },
            { label: 'Room Factor', value: result.roomFactor.toFixed(3) },
            { label: 'Co-pay Applied', value: `${result.copayPercentage}% (${fmt(result.copayAmount)})` },
            {
              label: 'Sub-limit Cap',
              value: result.procedureSubLimit ? fmt(result.procedureSubLimit) : 'None',
            },
          ].map(({ label, value, highlight }) => (
            <div key={label} className="flex justify-between py-1 border-b border-slate-800/40 last:border-0">
              <span className="text-slate-500">{label}</span>
              <span className={highlight ? 'text-white font-semibold' : 'text-slate-300'}>{value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Pie Chart */}
      <div className="bg-slate-900/60 border border-slate-700/50 rounded-2xl p-4">
        <p className="text-xs font-medium text-slate-400 mb-3">Payment Distribution</p>
        <ResponsiveContainer width="100%" height={200}>
          <PieChart>
            <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={80} paddingAngle={3} dataKey="value">
              {pieData.map((_, i) => (
                <Cell key={i} fill={PIE_COLORS[i]} />
              ))}
            </Pie>
            <Tooltip formatter={(val: number) => fmt(val)} contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#fff' }} />
            <Legend formatter={(val) => <span style={{ color: '#94a3b8', fontSize: '12px' }}>{val}</span>} />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Breakdown Bar Chart */}
      {barData.length > 0 && (
        <div className="bg-slate-900/60 border border-slate-700/50 rounded-2xl p-4">
          <p className="text-xs font-medium text-slate-400 mb-3">Cost Component Breakdown</p>
          <div className="space-y-2">
            {breakdown
              .filter((b) => b.hospitalBilled > 0)
              .map((b) => (
                <div key={b.name}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-400 truncate max-w-[200px]">{b.name}</span>
                    <span className="text-slate-300">{fmt(b.hospitalBilled)} billed</span>
                  </div>
                  <div className="h-5 bg-slate-800 rounded-lg overflow-hidden relative">
                    {/* Insurer covered portion */}
                    <div
                      className="absolute left-0 top-0 h-full bg-indigo-500 flex items-center"
                      style={{ width: `${Math.min(100, (b.insurerCovered / b.hospitalBilled) * 100)}%` }}
                    >
                      {b.insurerCovered / b.hospitalBilled > 0.2 && (
                        <span className="text-xs text-white pl-2 font-medium">{fmt(b.insurerCovered)}</span>
                      )}
                    </div>
                    {/* Patient portion */}
                    <div
                      className="absolute right-0 top-0 h-full bg-red-700/60 flex items-center justify-end"
                      style={{ width: `${Math.min(100, (b.patientLiability / b.hospitalBilled) * 100)}%` }}
                    >
                      {b.patientLiability / b.hospitalBilled > 0.15 && (
                        <span className="text-xs text-white pr-2">{fmt(b.patientLiability)}</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
          </div>

          {/* Legend */}
          <div className="flex gap-4 mt-3">
            <div className="flex items-center gap-1.5 text-xs text-slate-400">
              <div className="w-3 h-3 rounded-sm bg-indigo-500" />
              Insurer covers
            </div>
            <div className="flex items-center gap-1.5 text-xs text-slate-400">
              <div className="w-3 h-3 rounded-sm bg-red-700/60" />
              Patient pays
            </div>
          </div>
        </div>
      )}

      {/* Unknowns */}
      {unknowns.length > 0 && (
        <div className="p-3 bg-slate-900/40 border border-slate-700/30 rounded-xl">
          <p className="text-xs font-medium text-slate-400 mb-2">Could Not Determine</p>
          {unknowns.map((u, i) => (
            <div key={i} className="flex items-center gap-2 text-xs text-slate-500">
              <span>•</span> {u}
            </div>
          ))}
        </div>
      )}

      {/* Advisory */}
      <div className="flex items-start gap-2 text-xs text-slate-500 p-3 bg-slate-900/30 rounded-xl border border-slate-800/30">
        <CheckCircle2 className="w-3.5 h-3.5 text-slate-600 shrink-0 mt-0.5" />
        <span>
          This estimate is generated by a deterministic calculation engine. All figures are advisory — confirm with
          your insurer before admission. Engine v{calculation.engineVersion}.
        </span>
      </div>
    </div>
  );
}
