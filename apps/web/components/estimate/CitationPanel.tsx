'use client';

import type { CitationReference } from '@policy-estimator/types';
import { useScenarioStore } from '@/store/scenarioStore';
import { BookOpen, ExternalLink } from 'lucide-react';

interface CitationPanelProps {
  citations?: CitationReference[];
  policyCitations?: any[];
}

const RULE_TYPE_COLORS: Record<string, string> = {
  SUM_INSURED: 'bg-blue-900/40 border-blue-700/40 text-blue-300',
  ROOM_RENT_CAP: 'bg-yellow-900/40 border-yellow-700/40 text-yellow-300',
  COPAY: 'bg-orange-900/40 border-orange-700/40 text-orange-300',
  PROCEDURE_SUBLIMIT: 'bg-violet-900/40 border-violet-700/40 text-violet-300',
  EXCLUSION: 'bg-red-900/40 border-red-700/40 text-red-300',
  WAITING_PERIOD: 'bg-slate-800/60 border-slate-700/40 text-slate-300',
  DEDUCTIBLE: 'bg-pink-900/40 border-pink-700/40 text-pink-300',
};

export function CitationPanel({ citations, policyCitations }: CitationPanelProps) {
  const { jumpToCitation } = useScenarioStore();

  // Merge calculation citations and policy citations
  const allCitations = citations && citations.length > 0 ? citations : [];

  const dbCitations = policyCitations || [];
  
  // Build a deduplicated list
  const displayCitations = allCitations.length > 0
    ? allCitations
    : dbCitations.map((c: any) => ({
        id: c.id,
        ruleType: c.policyRule?.ruleType || 'OTHER',
        ruleName: c.policyRule?.ruleName || 'Policy Clause',
        page: c.pageNumber,
        sourceText: c.sourceText,
        boundingBox: c.boundingBox,
      }));

  if (displayCitations.length === 0) {
    return (
      <div className="bg-slate-900/60 border border-slate-700/50 rounded-2xl p-8 text-center">
        <BookOpen className="w-10 h-10 text-slate-700 mx-auto mb-3" />
        <p className="text-slate-400 text-sm">Citations will appear after a calculation is run</p>
        <p className="text-xs text-slate-600 mt-1">
          Each citation links a calculation step to the exact page and text in your policy
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 mb-3">
        <BookOpen className="w-4 h-4 text-indigo-400" />
        <h3 className="text-sm font-bold text-white">Policy Citations</h3>
        <span className="ml-auto text-xs text-slate-500">{displayCitations.length} citations</span>
      </div>

      <p className="text-xs text-slate-500 mb-3">
        Every calculation step is linked to the exact clause in your policy document. Click a citation to navigate to that page.
      </p>

      {displayCitations.map((citation, idx) => {
        const colorClass = RULE_TYPE_COLORS[citation.ruleType] || 'bg-slate-800/60 border-slate-700/40 text-slate-300';

        return (
          <div
            key={citation.id || idx}
            className="bg-slate-900/60 border border-slate-700/50 rounded-xl overflow-hidden hover:border-indigo-500/50 transition-colors cursor-pointer group"
            onClick={() =>
              jumpToCitation({
                id: citation.id,
                ruleType: citation.ruleType as any,
                ruleName: citation.ruleName,
                page: citation.page,
                sourceText: citation.sourceText,
                boundingBox: citation.boundingBox,
              })
            }
          >
            <div className="p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-medium px-2.5 py-1 rounded-full border ${colorClass}`}>
                    {citation.ruleType.replace(/_/g, ' ')}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-slate-300 bg-slate-800 px-2.5 py-1 rounded-lg">
                    Page {citation.page}
                  </span>
                  <ExternalLink className="w-3.5 h-3.5 text-slate-600 group-hover:text-indigo-400 transition-colors" />
                </div>
              </div>

              <p className="text-xs font-semibold text-white mb-2">{citation.ruleName}</p>

              <blockquote className="text-xs text-slate-300 leading-relaxed italic border-l-2 border-indigo-500/60 pl-3 py-1 bg-slate-950/40 rounded-r-lg">
                "{citation.sourceText?.slice(0, 300)}{citation.sourceText?.length > 300 ? '...' : ''}"
              </blockquote>

              {citation.boundingBox && (
                <div className="mt-2 flex items-center gap-1.5 text-xs text-slate-600">
                  <div className="w-1.5 h-1.5 rounded-full bg-indigo-600" />
                  Bounding box coordinates available for PDF highlighting
                </div>
              )}
            </div>
          </div>
        );
      })}

      <div className="text-xs text-slate-600 text-center pt-2">
        Citations extracted by AI from the original policy document
      </div>
    </div>
  );
}
