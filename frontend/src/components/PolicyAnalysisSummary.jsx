import React, { useState, useEffect } from 'react';
import { CheckCircle2, FileText, Hash, Search, BookOpen, Eye } from 'lucide-react';
import { getPolicyDetail } from '../services/api';
import PolicyRulesCards from './PolicyRulesCards';

export default function PolicyAnalysisSummary({ policyId, uploadData, onReset }) {
  const [policyDetail, setPolicyDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedPageNum, setSelectedPageNum] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    if (!policyId) return;

    const fetchDetail = async () => {
      setLoading(true);
      try {
        const data = await getPolicyDetail(policyId);
        setPolicyDetail(data);
      } catch (err) {
        console.error('Error fetching policy details:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDetail();
  }, [policyId]);

  const activePage = policyDetail?.pages?.find((p) => p.page_number === selectedPageNum);

  const filteredText = activePage?.content
    ? searchTerm
      ? activePage.content.split('\n').filter(line => line.toLowerCase().includes(searchTerm.toLowerCase())).join('\n')
      : activePage.content
    : '';

  return (
    <div className="space-y-6">
      {/* Top Banner: Analysis Status Checklist */}
      <div className="card-white p-6 border-emerald-200 bg-emerald-50/40 relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start space-x-3.5">
            <div className="w-10 h-10 rounded-xl bg-emerald-100 border border-emerald-300 flex items-center justify-center text-emerald-800 flex-shrink-0">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-lg font-bold text-slate-900 tracking-tight">
                  Policy Rules &amp; Citations Extracted
                </h3>
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
                  Ready for Scenario Calculation
                </span>
              </div>
              <p className="text-xs text-slate-600 mt-1">
                Document processed with 1-indexed page text retention and grounded clause citations.
              </p>
            </div>
          </div>

          <button
            onClick={onReset}
            className="btn-secondary text-xs px-4 py-2 cursor-pointer"
          >
            Upload Another Policy
          </button>
        </div>

        {/* 3 Status Checkmarks */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-5 pt-4 border-t border-emerald-200/60">
          <div className="flex items-center space-x-2.5 p-3 rounded-xl bg-white border border-slate-200">
            <CheckCircle2 className="w-4 h-4 text-emerald-700 flex-shrink-0" />
            <div className="min-w-0">
              <p className="text-[11px] text-slate-500 font-medium">Policy Document</p>
              <p className="text-xs font-bold text-slate-900 truncate">
                {uploadData?.original_filename || policyDetail?.original_filename || 'policy.pdf'}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2.5 p-3 rounded-xl bg-white border border-slate-200">
            <CheckCircle2 className="w-4 h-4 text-emerald-700 flex-shrink-0" />
            <div>
              <p className="text-[11px] text-slate-500 font-medium">Pages Retained</p>
              <p className="text-xs font-bold text-slate-900">
                {uploadData?.page_count || policyDetail?.page_count || 0} Pages Preserved
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2.5 p-3 rounded-xl bg-white border border-slate-200">
            <CheckCircle2 className="w-4 h-4 text-emerald-700 flex-shrink-0" />
            <div>
              <p className="text-[11px] text-slate-500 font-medium">Clauses Grounded</p>
              <p className="text-xs font-bold text-emerald-800 font-mono">
                Sum Insured, Copay, Caps
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Extracted Policy Rules Cards */}
      <PolicyRulesCards />

      {/* Page-by-Page Interactive Text Inspector */}
      {loading ? (
        <div className="card-white p-6 text-center text-slate-500 text-xs">
          Loading preserved page chunks...
        </div>
      ) : policyDetail?.pages ? (
        <div className="card-white p-6 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
            <div className="flex items-center space-x-2">
              <BookOpen className="w-4 h-4 text-emerald-700" />
              <h4 className="font-bold text-slate-900 text-sm">Preserved Page Text Inspector</h4>
              <span className="text-[10px] px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-mono">
                1-Indexed Pages
              </span>
            </div>

            {/* Keyword Search */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Filter page text..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8 pr-3 py-1.5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-emerald-600 w-full sm:w-52 font-medium"
              />
            </div>
          </div>

          {/* Page Tabs */}
          <div className="flex items-center space-x-2 overflow-x-auto pb-1 scrollbar-thin">
            {policyDetail.pages.map((p) => (
              <button
                key={p.page_number}
                onClick={() => setSelectedPageNum(p.page_number)}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all shrink-0 cursor-pointer ${
                  selectedPageNum === p.page_number
                    ? 'bg-emerald-700 text-white shadow-2xs'
                    : 'bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200'
                }`}
              >
                <Hash className="w-3 h-3" />
                <span>Page {p.page_number}</span>
                <span className="opacity-70 text-[10px] font-mono">({p.word_count} words)</span>
              </button>
            ))}
          </div>

          {/* Active Page Content Preview */}
          {activePage ? (
            <div className="space-y-2.5">
              <div className="flex items-center justify-between text-xs text-slate-500 bg-slate-50 px-3.5 py-2 rounded-xl border border-slate-200">
                <span className="flex items-center space-x-1.5">
                  <Eye className="w-3.5 h-3.5 text-emerald-700" />
                  <span>Viewing <strong>Page {activePage.page_number}</strong> Text</span>
                </span>
                <div className="flex items-center space-x-4 font-mono text-[11px]">
                  <span>Words: <strong className="text-slate-800">{activePage.word_count}</strong></span>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-900 text-slate-200 font-mono text-xs leading-relaxed max-h-72 overflow-y-auto whitespace-pre-wrap select-text">
                {filteredText || <span className="text-slate-400 italic">No matching text found on Page {activePage.page_number}.</span>}
              </div>
            </div>
          ) : (
            <p className="text-xs text-slate-500 py-3 text-center">Select a page above to inspect text.</p>
          )}
        </div>
      ) : null}
    </div>
  );
}
