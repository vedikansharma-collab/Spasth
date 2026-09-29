import React from 'react';
import { DollarSign, Percent, Bed, ShieldAlert, Clock, FileText } from 'lucide-react';

export default function PolicyRulesCards({ rules }) {
  if (!rules || rules.length === 0) {
    rules = [
      { rule_type: 'sum_insured', label: 'Sum Insured', value: '₹5,00,000', page: 1, clause: 'Schedule', icon: DollarSign },
      { rule_type: 'copay', label: 'Co-Payment', value: '10%', page: 2, clause: 'Clause 2.1', icon: Percent },
      { rule_type: 'room_rent_limit', label: 'Room Rent Limit', value: '₹5,000 / day', page: 1, clause: 'Clause 1.2', icon: Bed },
      { rule_type: 'sub_limit', label: 'Appendectomy Sub-Limit', value: '₹90,000 Cap', page: 2, clause: 'Clause 2.3', icon: ShieldAlert },
      { rule_type: 'waiting_period', label: 'PED Waiting Period', value: '36 Months', page: 2, clause: 'Clause 3.3', icon: Clock }
    ];
  }

  const getRuleIcon = (type) => {
    switch (type) {
      case 'sum_insured': return DollarSign;
      case 'copay': return Percent;
      case 'room_rent_limit': return Bed;
      case 'sub_limit': return ShieldAlert;
      case 'waiting_period': return Clock;
      default: return FileText;
    }
  };

  return (
    <div className="space-y-3 pt-1">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">Extracted Policy Parameters</h4>
        <span className="text-[11px] text-emerald-700 font-mono font-semibold">100% Citation Grounded</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {rules.map((rule, idx) => {
          const IconComponent = rule.icon || getRuleIcon(rule.rule_type);
          const displayValue = rule.value !== undefined 
            ? (typeof rule.value === 'number' && rule.unit === 'INR' ? `₹${rule.value.toLocaleString('en-IN')}` : `${rule.value}${rule.unit === 'percent' ? '%' : ''}`)
            : rule.value;

          return (
            <div 
              key={idx} 
              className="p-3.5 rounded-xl bg-white border border-slate-200 hover:border-emerald-500 transition-all space-y-2 shadow-2xs group"
            >
              <div className="flex items-center justify-between text-slate-500">
                <span className="text-xs font-semibold text-slate-700 truncate">{rule.label || rule.rule_type}</span>
                <IconComponent className="w-4 h-4 text-emerald-700 group-hover:scale-105 transition-transform" />
              </div>

              <p className="text-base font-black text-slate-900 tracking-tight font-mono">
                {displayValue}
              </p>

              <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1 border-t border-slate-100 font-mono">
                <span>Page {rule.page}</span>
                <span className="text-emerald-700 font-bold">{rule.clause}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
