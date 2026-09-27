'use client';

import { useState } from 'react';
import { FileText, ChevronDown, ChevronRight, Tag, AlertCircle, Clock, MinusCircle } from 'lucide-react';

interface PolicyRulesPanelProps {
  rules?: any[];
  citations?: any[];
}

const RULE_TYPE_CONFIG: Record<string, { label: string; color: string; bgColor: string; icon: typeof Tag }> = {
  SUM_INSURED: { label: 'Sum Insured', color: 'text-blue-400', bgColor: 'bg-blue-950/40 border-blue-800/40', icon: Tag },
  ROOM_RENT_CAP: { label: 'Room Rent Cap', color: 'text-yellow-400', bgColor: 'bg-yellow-950/40 border-yellow-800/40', icon: Tag },
  COPAY: { label: 'Co-payment', color: 'text-orange-400', bgColor: 'bg-orange-950/40 border-orange-800/40', icon: Tag },
  PROCEDURE_SUBLIMIT: { label: 'Sub-limit', color: 'text-violet-400', bgColor: 'bg-violet-950/40 border-violet-800/40', icon: Tag },
  DEDUCTIBLE: { label: 'Deductible', color: 'text-pink-400', bgColor: 'bg-pink-950/40 border-pink-800/40', icon: Tag },
  EXCLUSION: { label: 'Exclusion', color: 'text-red-400', bgColor: 'bg-red-950/40 border-red-800/40', icon: MinusCircle },
  WAITING_PERIOD: { label: 'Waiting Period', color: 'text-slate-400', bgColor: 'bg-slate-800/60 border-slate-700/40', icon: Clock },
  OTHER: { label: 'Other', color: 'text-slate-400', bgColor: 'bg-slate-800/60 border-slate-700/40', icon: Tag },
};

const RULE_ORDER = ['SUM_INSURED', 'ROOM_RENT_CAP', 'COPAY', 'PROCEDURE_SUBLIMIT', 'DEDUCTIBLE', 'WAITING_PERIOD', 'EXCLUSION', 'OTHER'];

export function PolicyRulesPanel({ rules, citations }: PolicyRulesPanelProps) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  if (!rules || rules.length === 0) {
    return (
      <div className="bg-slate-900/60 border border-slate-700/50 rounded-2xl p-8 text-center">
        <FileText className="w-10 h-10 text-slate-700 mx-auto mb-3" />
        <p className="text-slate-400 text-sm">Policy rules will appear after processing</p>
      </div>
    );
  }

  const toggle = (id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  // Group rules by type
  const grouped: Record<string, any[]> = {};
  for (const rule of rules) {
    if (!grouped[rule.ruleType]) grouped[rule.ruleType] = [];
    grouped[rule.ruleType].push(rule);
  }

  const formatValue = (rule: any) => {
    if (!rule.value && rule.value !== 0) return 'N/A';
    if (rule.unit === '%') return `${rule.value}%`;
    if (rule.unit === 'INR') return `₹${rule.value.toLocaleString('en-IN')}`;
    if (rule.unit === 'MONTHS') return `${rule.value} months`;
    return `${rule.value} ${rule.unit || ''}`;
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 mb-3">
        <FileText className="w-4 h-4 text-indigo-400" />
        <h3 className="text-sm font-bold text-white">Extracted Policy Rules</h3>
        <span className="ml-auto text-xs text-slate-500">{rules.length} rules</span>
      </div>

      {RULE_ORDER.filter((type) => grouped[type]).map((type) => {
        const config = RULE_TYPE_CONFIG[type] || RULE_TYPE_CONFIG.OTHER;
        const Icon = config.icon;
        const typeRules = grouped[type];

        return (
          <div key={type} className={`border rounded-2xl overflow-hidden ${config.bgColor}`}>
            <div className="px-4 py-3 flex items-center gap-2">
              <Icon className={`w-4 h-4 ${config.color}`} />
              <span className={`text-xs font-bold uppercase tracking-wide ${config.color}`}>{config.label}</span>
              <span className="ml-auto text-xs text-slate-500">{typeRules.length} {typeRules.length === 1 ? 'rule' : 'rules'}</span>
            </div>

            <div className="divide-y divide-white/5">
              {typeRules.map((rule) => {
                const isOpen = expanded.has(rule.id);
                const ruleCitations = citations?.filter((c) => c.policyRuleId === rule.id) || [];

                return (
                  <div key={rule.id}>
                    <button
                      onClick={() => toggle(rule.id)}
                      className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-white/5 transition-colors"
                    >
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-white truncate">{rule.ruleName}</p>
                        <p className="text-xs text-slate-500 mt-0.5">{rule.description?.slice(0, 80)}</p>
                      </div>
                      <div className="text-right shrink-0">
                        <p className="text-sm font-bold text-white">{formatValue(rule)}</p>
                        {rule.sourcePage && (
                          <p className="text-xs text-slate-500">Pg. {rule.sourcePage}</p>
                        )}
                      </div>
                      {isOpen ? (
                        <ChevronDown className="w-4 h-4 text-slate-500 shrink-0" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-slate-500 shrink-0" />
                      )}
                    </button>

                    {isOpen && (
                      <div className="px-4 pb-4 space-y-3 border-t border-white/5">
                        {/* Full description */}
                        {rule.description && (
                          <div className="mt-3 text-xs text-slate-300 leading-relaxed">{rule.description}</div>
                        )}

                        {/* Source Text (Citation) */}
                        {rule.sourceText && (
                          <div>
                            <p className="text-xs font-medium text-slate-500 mb-1.5">
                              Source Text — Page {rule.sourcePage}
                            </p>
                            <blockquote className="text-xs text-slate-300 italic bg-slate-950/60 border-l-2 border-indigo-500 pl-3 py-2 rounded-r-lg">
                              "{rule.sourceText}"
                            </blockquote>
                          </div>
                        )}

                        {/* Confidence */}
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-slate-500">Extraction Confidence:</span>
                          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                            rule.confidenceLevel === 'HIGH'
                              ? 'bg-emerald-900/60 text-emerald-300'
                              : rule.confidenceLevel === 'MEDIUM'
                              ? 'bg-yellow-900/60 text-yellow-300'
                              : 'bg-red-900/60 text-red-300'
                          }`}>
                            {rule.confidenceLevel}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}
