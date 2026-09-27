'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getPolicy, getPolicyStatus, getProcedures, calculateTreatment, recalculateTreatment } from '@/lib/api';
import { PolicyRulesPanel } from '@/components/estimate/PolicyRulesPanel';
import { ScenarioConfigurator } from '@/components/estimate/ScenarioConfigurator';
import { ResultsDashboard } from '@/components/estimate/ResultsDashboard';
import { CalculationTrace } from '@/components/estimate/CalculationTrace';
import { CitationPanel } from '@/components/estimate/CitationPanel';
import { ProcessingStatus } from '@/components/estimate/ProcessingStatus';
import { useScenarioStore } from '@/store/scenarioStore';
import type { CalculationResponse, Procedure, RoomCategory } from '@policy-estimator/types';
import {
  ArrowLeft,
  Shield,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  FileText,
  Calculator,
  ListChecks,
  MessageSquare,
} from 'lucide-react';

type Tab = 'results' | 'trace' | 'rules' | 'citations';

export default function EstimatePage() {
  const params = useParams();
  const router = useRouter();
  const policyId = params.id as string;

  const { setPolicy, setCalculation, setIsRecalculating, selectedProcedureCode, selectedRoomCategory, stayDays, city, calculation } =
    useScenarioStore();

  const [policy, setPolicyData] = useState<any>(null);
  const [status, setStatus] = useState<string>('READY');
  const [procedures, setProcedures] = useState<Procedure[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCalculating, setIsCalculating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('results');
  const [showCitations, setShowCitations] = useState(false);

  // Load policy and procedures
  useEffect(() => {
    if (!policyId) return;

    const loadData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const [policyData, procsData] = await Promise.all([getPolicy(policyId), getProcedures()]);
        setPolicyData(policyData);
        setPolicy(policyId, policyData);
        setProcedures(procsData);
        setStatus(policyData.status);

        // If already ready, run initial calculation
        if (policyData.status === 'READY') {
          await runCalculation(policyId, selectedProcedureCode, selectedRoomCategory, stayDays, city, false);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load policy');
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [policyId]);

  // Poll for processing status
  useEffect(() => {
    if (!policy || !['UPLOADING', 'PARSING', 'EXTRACTING', 'VALIDATING'].includes(status)) return;

    const interval = setInterval(async () => {
      try {
        const s = await getPolicyStatus(policyId);
        setStatus(s.status);
        if (s.status === 'READY') {
          clearInterval(interval);
          const policyData = await getPolicy(policyId);
          setPolicyData(policyData);
          setPolicy(policyId, policyData);
          await runCalculation(policyId, selectedProcedureCode, selectedRoomCategory, stayDays, city, false);
        } else if (s.status === 'FAILED') {
          clearInterval(interval);
          setError(s.errorMessage || 'Policy processing failed');
        }
      } catch (_) {}
    }, 2000);

    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [policy, status]);

  const runCalculation = useCallback(
    async (
      pid: string,
      procCode: string,
      room: RoomCategory,
      days: number,
      cityName: string,
      isRecalc: boolean
    ) => {
      setIsCalculating(true);
      setIsRecalculating(isRecalc);
      setError(null);
      try {
        const fn = isRecalc ? recalculateTreatment : calculateTreatment;
        const result = await fn(pid, {
          procedureCode: procCode,
          roomCategory: room,
          stayDays: days,
          city: cityName,
        });
        setCalculation(result);
        setActiveTab('results');
      } catch (err: any) {
        setError(err.message || 'Calculation failed');
      } finally {
        setIsCalculating(false);
        setIsRecalculating(false);
      }
    },
    [setCalculation, setIsRecalculating]
  );

  const handleRecalculate = (procCode: string, room: RoomCategory, days: number, cityName: string) => {
    runCalculation(policyId, procCode, room, days, cityName, true);
  };

  const tabs: { id: Tab; label: string; icon: typeof Calculator }[] = [
    { id: 'results', label: 'Cost Breakdown', icon: Calculator },
    { id: 'trace', label: 'Calculation Trace', icon: ListChecks },
    { id: 'rules', label: 'Policy Rules', icon: FileText },
    { id: 'citations', label: 'Citations', icon: MessageSquare },
  ];

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-indigo-500/30 border-t-indigo-400 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-300 text-lg">Loading policy data...</p>
        </div>
      </div>
    );
  }

  const isProcessing = ['UPLOADING', 'PARSING', 'EXTRACTING', 'VALIDATING'].includes(status);

  return (
    <div className="min-h-screen">
      {/* Top Nav */}
      <div className="sticky top-0 z-40 bg-slate-950/90 border-b border-slate-800/60 backdrop-blur-xl">
        <div className="max-w-screen-2xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push('/')}
              className="flex items-center gap-1.5 text-slate-400 hover:text-white transition-colors text-sm"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </button>
            <div className="h-4 w-px bg-slate-700" />
            <div className="flex items-center gap-2">
              <div className="p-1.5 bg-indigo-600 rounded-lg">
                <Shield className="w-4 h-4 text-white" />
              </div>
              <div>
                <p className="text-sm font-semibold text-white leading-tight">
                  {policy?.policyName || 'Policy Analysis'}
                </p>
                <p className="text-xs text-slate-400 leading-tight">{policy?.insurerName || 'Insurance Policy'}</p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {calculation && (
              <div className="hidden sm:flex items-center gap-3 text-xs">
                <span className="px-2 py-1 bg-slate-800 rounded-lg text-slate-300">
                  Engine v{calculation.engineVersion}
                </span>
                <span
                  className={`px-2 py-1 rounded-lg font-medium ${
                    calculation.confidence.overall === 'HIGH'
                      ? 'bg-emerald-900/60 text-emerald-300'
                      : calculation.confidence.overall === 'MEDIUM'
                      ? 'bg-yellow-900/60 text-yellow-300'
                      : 'bg-red-900/60 text-red-300'
                  }`}
                >
                  {calculation.confidence.overall} Confidence
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-screen-2xl mx-auto px-4 py-6">
        {/* Processing State */}
        {isProcessing && (
          <div className="mb-6">
            <ProcessingStatus status={status} />
          </div>
        )}

        {/* Error State */}
        {error && !isProcessing && (
          <div className="mb-6 p-4 bg-red-950/50 border border-red-800/50 rounded-xl text-red-300 text-sm flex items-center gap-2">
            <RefreshCw className="w-4 h-4 shrink-0" />
            <span>{error}</span>
            <button
              onClick={() => setError(null)}
              className="ml-auto text-red-400 hover:text-red-200 underline text-xs"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Main 3-Column Layout */}
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
          {/* LEFT: Scenario Configurator */}
          <div className="xl:col-span-3">
            <ScenarioConfigurator
              procedures={procedures}
              policyId={policyId}
              isReady={status === 'READY'}
              isCalculating={isCalculating}
              onRecalculate={handleRecalculate}
            />
          </div>

          {/* CENTER: Tabs + Content */}
          <div className="xl:col-span-6 space-y-4">
            {/* Tab Bar */}
            <div className="flex gap-1 p-1 bg-slate-900/60 border border-slate-800/60 rounded-xl">
              {tabs.map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  onClick={() => setActiveTab(id)}
                  className={`flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-medium transition-all ${
                    activeTab === id
                      ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-900/50'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">{label}</span>
                </button>
              ))}
            </div>

            {/* Tab Content */}
            {activeTab === 'results' && (
              <ResultsDashboard calculation={calculation} isLoading={isCalculating} />
            )}
            {activeTab === 'trace' && (
              <CalculationTrace trace={calculation?.calculationTrace} isLoading={isCalculating} />
            )}
            {activeTab === 'rules' && <PolicyRulesPanel rules={policy?.rules} citations={policy?.citations} />}
            {activeTab === 'citations' && (
              <CitationPanel
                citations={calculation?.citations}
                policyCitations={policy?.citations}
              />
            )}
          </div>

          {/* RIGHT: Policy Summary Sidebar */}
          <div className="xl:col-span-3">
            <div className="bg-slate-900/60 border border-slate-700/50 rounded-2xl overflow-hidden backdrop-blur-sm">
              <div className="p-4 border-b border-slate-800/60">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <FileText className="w-4 h-4 text-indigo-400" />
                  Policy Summary
                </h3>
              </div>

              {policy?.rules && (
                <div className="p-4 space-y-3">
                  {policy.rules
                    .filter((r: any) => ['SUM_INSURED', 'ROOM_RENT_CAP', 'COPAY'].includes(r.ruleType))
                    .map((rule: any) => (
                      <RuleSummaryItem key={rule.id} rule={rule} />
                    ))}

                  {/* Sub-limits summary */}
                  {policy.rules.some((r: any) => r.ruleType === 'PROCEDURE_SUBLIMIT') && (
                    <div>
                      <button
                        onClick={() => setShowCitations(!showCitations)}
                        className="w-full flex items-center justify-between text-xs text-slate-400 hover:text-slate-200 py-2 border-t border-slate-800/60 mt-2 pt-3"
                      >
                        <span>
                          {policy.rules.filter((r: any) => r.ruleType === 'PROCEDURE_SUBLIMIT').length} Sub-limits
                        </span>
                        {showCitations ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                      </button>
                      {showCitations && (
                        <div className="space-y-2 mt-2">
                          {policy.rules
                            .filter((r: any) => r.ruleType === 'PROCEDURE_SUBLIMIT')
                            .slice(0, 5)
                            .map((r: any) => (
                              <div key={r.id} className="flex justify-between text-xs">
                                <span className="text-slate-400 truncate max-w-[140px]">
                                  {r.ruleName.replace('Sub-limit: ', '')}
                                </span>
                                <span className="text-white font-medium">
                                  ₹{r.value?.toLocaleString('en-IN')}
                                </span>
                              </div>
                            ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Exclusions */}
                  {policy.rules.some((r: any) => r.ruleType === 'EXCLUSION') && (
                    <div className="pt-3 border-t border-slate-800/60">
                      <p className="text-xs text-slate-500 mb-2">
                        {policy.rules.filter((r: any) => r.ruleType === 'EXCLUSION').length} Exclusions listed
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Policy ID */}
              <div className="px-4 pb-4">
                <div className="p-2.5 bg-slate-950/60 rounded-lg">
                  <p className="text-xs text-slate-500 mb-1">Policy ID</p>
                  <p className="text-xs text-slate-300 font-mono break-all">{policyId}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function RuleSummaryItem({ rule }: { rule: any }) {
  const typeLabels: Record<string, string> = {
    SUM_INSURED: 'Sum Insured',
    ROOM_RENT_CAP: 'Room Rent Cap',
    COPAY: 'Co-payment',
  };

  const typeColors: Record<string, string> = {
    SUM_INSURED: 'text-blue-400',
    ROOM_RENT_CAP: 'text-yellow-400',
    COPAY: 'text-orange-400',
  };

  const formatValue = (rule: any) => {
    if (rule.unit === '%') return `${rule.value}%`;
    if (rule.unit === 'INR') return `₹${rule.value?.toLocaleString('en-IN')}`;
    return `${rule.value} ${rule.unit || ''}`;
  };

  return (
    <div className="flex items-center justify-between py-2 border-b border-slate-800/40 last:border-0">
      <div>
        <p className={`text-xs font-medium ${typeColors[rule.ruleType] || 'text-slate-300'}`}>
          {typeLabels[rule.ruleType] || rule.ruleName}
        </p>
        {rule.sourcePage && (
          <p className="text-xs text-slate-600 mt-0.5">Pg. {rule.sourcePage}</p>
        )}
      </div>
      <div className="text-right">
        <p className="text-sm font-bold text-white">{formatValue(rule)}</p>
        <p className="text-xs text-slate-500">{rule.unit === '%' ? 'of Sum Insured' : 'per claim'}</p>
      </div>
    </div>
  );
}
