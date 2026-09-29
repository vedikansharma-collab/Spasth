import React, { useState, useEffect } from 'react';
import { Database, FileText, ChevronRight, Layers } from 'lucide-react';
import { getPolicies } from '../services/api';

export default function PolicyList({ onSelectPolicy, activePolicyId }) {
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchPolicies = async () => {
    setLoading(true);
    try {
      const data = await getPolicies();
      setPolicies(data);
    } catch (err) {
      console.error('Error listing policies:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPolicies();
  }, [activePolicyId]);

  if (loading) {
    return (
      <div className="card-white p-4 text-slate-500 text-xs text-center">
        Loading indexed policies...
      </div>
    );
  }

  if (policies.length === 0) {
    return null;
  }

  return (
    <div className="card-white p-5 space-y-3">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div className="flex items-center space-x-2">
          <Database className="w-4 h-4 text-emerald-700" />
          <h3 className="font-bold text-slate-900 text-xs uppercase tracking-wider">Indexed Policy Library</h3>
        </div>
        <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-mono font-semibold">
          {policies.length} {policies.length === 1 ? 'Document' : 'Documents'}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {policies.map((p) => (
          <div
            key={p.id}
            onClick={() => onSelectPolicy(p.id)}
            className={`p-3.5 rounded-xl border transition-all cursor-pointer flex items-center justify-between group ${
              activePolicyId === p.id
                ? 'bg-emerald-50/70 border-emerald-500 shadow-2xs'
                : 'bg-slate-50/60 border-slate-200 hover:border-slate-300 hover:bg-slate-100/60'
            }`}
          >
            <div className="flex items-center space-x-3 min-w-0">
              <div className="p-2 rounded-lg bg-white border border-slate-200 text-emerald-700 flex-shrink-0">
                <FileText className="w-4 h-4" />
              </div>
              <div className="min-w-0">
                <h4 className="text-xs font-bold text-slate-900 truncate">{p.original_filename}</h4>
                <div className="flex items-center space-x-2 text-[11px] text-slate-500 mt-0.5 font-mono">
                  <span className="flex items-center space-x-1">
                    <Layers className="w-3 h-3 text-emerald-700" />
                    <span>{p.page_count} pages</span>
                  </span>
                  <span>•</span>
                  <span>{(p.file_size_bytes / 1024).toFixed(1)} KB</span>
                </div>
              </div>
            </div>

            <ChevronRight className={`w-4 h-4 transition-transform ${activePolicyId === p.id ? 'text-emerald-700 translate-x-0.5' : 'text-slate-400 group-hover:text-slate-600'}`} />
          </div>
        ))}
      </div>
    </div>
  );
}
