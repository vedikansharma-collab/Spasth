import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import DashboardHomeView from '../components/DashboardHomeView';
import PolicyAssistantView from '../components/PolicyAssistantView';
import CostEstimatorView from '../components/CostEstimatorView';
import PolicyDocumentView from '../components/PolicyDocumentView';
import PolicyUpload from '../components/PolicyUpload';
import { calculateEstimate, getPolicyDetail, getPolicies } from '../services/api';
import { X, UploadCloud } from 'lucide-react';

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [activePolicyId, setActivePolicyId] = useState(null);
  const [activePolicy, setActivePolicy] = useState(null);
  const [policies, setPolicies] = useState([]);
  const [estimateResult, setEstimateResult] = useState(null);
  const [estimating, setEstimating] = useState(false);
  const [lastScenario, setLastScenario] = useState(null);

  // Citation navigation targets
  const [targetDocPage, setTargetDocPage] = useState(1);
  const [targetDocCitation, setTargetDocCitation] = useState(null);
  const [previousTab, setPreviousTab] = useState('dashboard');

  // Quick Upload Modal
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

  // Load indexed policies on mount
  const refreshPolicies = async () => {
    try {
      const list = await getPolicies();
      setPolicies(list || []);
      // If no active policy is set, auto-select the latest indexed document
      if (!activePolicyId && list && list.length > 0) {
        setActivePolicyId(list[0].id);
      }
    } catch (err) {
      console.error('Error fetching indexed policies:', err);
    }
  };

  useEffect(() => {
    refreshPolicies();
  }, []);

  // Fetch full policy details whenever activePolicyId changes
  useEffect(() => {
    if (!activePolicyId) {
      setActivePolicy(null);
      return;
    }

    const loadPolicyDetail = async () => {
      try {
        const detail = await getPolicyDetail(activePolicyId);
        setActivePolicy(detail);
      } catch (err) {
        console.error('Error loading policy details:', err);
      }
    };

    loadPolicyDetail();
  }, [activePolicyId]);

  const handleUploadSuccess = (data) => {
    setActivePolicyId(data.policy_id);
    setIsUploadModalOpen(false);
    refreshPolicies();
    setActiveTab('dashboard');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSelectPolicy = (policyId) => {
    setActivePolicyId(policyId);
    setEstimateResult(null);
    setLastScenario(null);
  };

  const handleReset = () => {
    setActivePolicyId(null);
    setActivePolicy(null);
    setEstimateResult(null);
    setLastScenario(null);
  };

  const handleCalculateScenario = async (scenarioPayload) => {
    if (!activePolicyId) return;

    setEstimating(true);
    setLastScenario(scenarioPayload);
    try {
      const result = await calculateEstimate({
        ...scenarioPayload,
        policy_id: activePolicyId
      });
      setEstimateResult(result);
    } catch (err) {
      console.error('Error calculating estimate:', err);
      alert(err.response?.data?.detail || 'Failed to calculate out-of-pocket estimate.');
    } finally {
      setEstimating(false);
    }
  };

  const handleRoomRecalculate = (newRoomCategory) => {
    if (!lastScenario || !activePolicyId) return;
    handleCalculateScenario({
      ...lastScenario,
      room_category: newRoomCategory
    });
  };

  // Bidirectional citation navigation
  const handleNavigateToDoc = (pageNumber, citation = null) => {
    setPreviousTab(activeTab);
    setTargetDocPage(pageNumber || 1);
    setTargetDocCitation(citation);
    setActiveTab('document');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleReturnFromDoc = (targetDestination) => {
    setTargetDocCitation(null);
    setActiveTab(targetDestination || previousTab || 'dashboard');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleTabChange = (tabId) => {
    setActiveTab(tabId);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen flex flex-col bg-white text-[#003339] font-sans antialiased">
      {/* 1. Global Navigation Bar */}
      <Navbar
        activeTab={activeTab}
        onTabChange={handleTabChange}
        activePolicy={activePolicy}
        onUploadClick={() => setIsUploadModalOpen(true)}
      />

      {/* 2. Main Content Area */}
      <main className="flex-1">
        {activeTab === 'dashboard' && (
          <DashboardHomeView
            activePolicyId={activePolicyId}
            activePolicy={activePolicy}
            onUploadSuccess={handleUploadSuccess}
            onSelectPolicy={handleSelectPolicy}
            onOpenAssistant={() => handleTabChange('assistant')}
            onOpenEstimator={() => handleTabChange('estimator')}
            onOpenDocument={(page, cite) => handleNavigateToDoc(page, cite)}
            onResetPolicy={handleReset}
            policies={policies}
          />
        )}

        {activeTab === 'assistant' && (
          <PolicyAssistantView
            activePolicyId={activePolicyId}
            activePolicy={activePolicy}
            onNavigateToDoc={(page, cite) => handleNavigateToDoc(page, cite)}
            onSelectPolicy={handleSelectPolicy}
            policies={policies}
          />
        )}

        {activeTab === 'estimator' && (
          <CostEstimatorView
            activePolicyId={activePolicyId}
            activePolicy={activePolicy}
            onCalculate={handleCalculateScenario}
            estimateResult={estimateResult}
            estimating={estimating}
            onRecalculateRoom={handleRoomRecalculate}
            onNavigateToDoc={(page, cite) => handleNavigateToDoc(page, cite)}
            onSelectPolicy={handleSelectPolicy}
            policies={policies}
          />
        )}

        {activeTab === 'document' && (
          <PolicyDocumentView
            activePolicyId={activePolicyId}
            activePolicy={activePolicy}
            targetPage={targetDocPage}
            targetCitation={targetDocCitation}
            onReturnToAssistant={() => handleReturnFromDoc('assistant')}
            onReturnToEstimator={() => handleReturnFromDoc('estimator')}
            onSelectPolicy={handleSelectPolicy}
            policies={policies}
          />
        )}
      </main>

      {/* 3. Global Footer */}
      <Footer />

      {/* 4. Upload Policy Modal Dialog */}
      {isUploadModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-fade-in">
          <div 
            className="card-white max-w-lg w-full p-6 space-y-4 shadow-2xl relative border-[#E2E8E8]"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-3 border-b border-[#E2E8E8]">
              <div className="flex items-center space-x-2.5">
                <div className="w-9 h-9 rounded-xl bg-[rgba(57,171,173,0.12)] border border-[#39ABAD]/40 flex items-center justify-center text-[#006668]">
                  <UploadCloud className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-[#003339] text-base">Upload Policy PDF</h3>
                  <p className="text-xs text-[#4A5859]">Index clauses and preserve page citations</p>
                </div>
              </div>
              <button
                onClick={() => setIsUploadModalOpen(false)}
                className="p-1.5 rounded-lg bg-[#F7F7F8] text-[#4A5859] hover:text-[#003339] hover:bg-slate-200 transition-colors cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <PolicyUpload onUploadSuccess={handleUploadSuccess} />
          </div>
        </div>
      )}
    </div>
  );
}
