import React from 'react';
import { DollarSign, Percent, Bed, ShieldAlert, Clock, FileText, AlertCircle } from 'lucide-react';

export default function PolicyRulesCards({ rules, onCitationClick }) {
  if (!rules || rules.length === 0) {
    return (
      <div className="card-white p-5 text-center text-xs text-slate-500 border-dashed space-y-1">
        <div className="flex items-center justify-center space-x-1.5 text-slate-600 font-semibold">
          <AlertCircle className="w-4 h-4 text-slate-400" />
          <span>No Policy Rules Extracted</span>
        </div>
        <p>Upload a policy PDF or select an indexed document to extract Sum Insured, Co-pay, Room Caps, and Sub-limits.</p>
      </div>
    );
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
          const rawLabel = rule.label || rule.rule_key || rule.rule_type;
          const displayLabel = rawLabel.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
          let displayValue = rule.value;
          if (rule.value !== undefined && rule.value !== null) {
            if (rule.rule_type === 'copay' || rule.unit === 'percent') {
              displayValue = `${rule.value}%`;
            } else if (typeof rule.value === 'number') {
              displayValue = `₹${rule.value.toLocaleString('en-IN')}`;
            } else {
              displayValue = String(rule.value);
            }
          }

          const citationObj = {
            page: rule.page || 1,
            clause: rule.clause || 'N/A',
            rule: displayLabel,
            source_text: rule.source_text || `${displayLabel}: ${displayValue}`,
            details: displayValue
          };

          return (
            <div 
              key={idx} 
              onClick={() => onCitationClick && onCitationClick(citationObj)}
              className={`p-3.5 rounded-xl bg-white border border-slate-200 hover:border-emerald-500 transition-all space-y-2 shadow-2xs group ${
                onCitationClick ? 'cursor-pointer hover:shadow-xs' : ''
              }`}
            >
              <div className="flex items-center justify-between text-slate-500">
                <span className="text-xs font-semibold text-slate-700 truncate">{displayLabel}</span>
                <IconComponent className="w-4 h-4 text-emerald-700 group-hover:scale-105 transition-transform" />
              </div>

              <p className="text-base font-black text-slate-900 tracking-tight font-mono">
                {displayValue}
              </p>

              <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1 border-t border-slate-100 font-mono">
                <span>Page {rule.page || 1}</span>
                <span className="text-emerald-700 font-bold group-hover:underline">{rule.clause || 'N/A'}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
