import React, { useState } from 'react';
import Navbar from '../components/Navbar';
import HeroSection from '../components/HeroSection';
import TrustIndicators from '../components/TrustIndicators';
import HowItWorks from '../components/HowItWorks';
import PolicyUpload from '../components/PolicyUpload';
import PolicyAnalysisSummary from '../components/PolicyAnalysisSummary';
import PolicyList from '../components/PolicyList';
import TreatmentScenarioForm from '../components/TreatmentScenarioForm';
import EstimationResultDashboard from '../components/EstimationResultDashboard';
import EvidenceSection from '../components/EvidenceSection';
import ScenarioSensitivitySection from '../components/ScenarioSensitivitySection';
import ConfidenceSection from '../components/ConfidenceSection';
import WhyFin01Section from '../components/WhyFin01Section';
import FinalCTA from '../components/FinalCTA';
import Footer from '../components/Footer';
import ChatbotModal from '../components/ChatbotModal';
import { calculateEstimate } from '../services/api';

export default function Dashboard() {
  const [activePolicyId, setActivePolicyId] = useState(null);
  const [uploadData, setUploadData] = useState(null);
  const [estimateResult, setEstimateResult] = useState(null);
  const [estimating, setEstimating] = useState(false);
  const [lastScenario, setLastScenario] = useState(null);
  const [isChatOpen, setIsChatOpen] = useState(false);

  const scrollToEstimator = () => {
    const el = document.getElementById('estimator');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const scrollToHowItWorks = () => {
    const el = document.getElementById('how-it-works');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleUploadSuccess = (data) => {
    setUploadData(data);
    setActivePolicyId(data.policy_id);
    setEstimateResult(null);
  };

  const handleReset = () => {
    setActivePolicyId(null);
    setUploadData(null);
    setEstimateResult(null);
    setLastScenario(null);
  };

  const handleSelectPolicy = (policyId) => {
    setActivePolicyId(policyId);
    setUploadData(null);
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
      // Smooth scroll to results
      setTimeout(() => {
        const resEl = document.getElementById('results');
        if (resEl) {
          resEl.scrollIntoView({ behavior: 'smooth' });
        }
      }, 100);
    } catch (err) {
      console.error('Error calculating financial estimate:', err);
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

  return (
    <div className="min-h-screen flex flex-col bg-white text-slate-900 font-sans">
      {/* Section 1: Navigation */}
      <Navbar onOpenChat={() => setIsChatOpen(true)} />

      {/* Section 2: Hero Section */}
      <HeroSection
        onAnalyzeClick={scrollToEstimator}
        onHowItWorksClick={scrollToHowItWorks}
      />

      {/* Section 3: Trust & Value Indicators */}
      <TrustIndicators />

      {/* Section 4: How It Works */}
      <HowItWorks />

      {/* Section 5: Core Estimator Application (#estimator) */}
      <section id="estimator" className="py-16 bg-offwhite border-t border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
          
          <div className="text-center max-w-3xl mx-auto space-y-3">
            <h2 className="text-3xl sm:text-4xl font-black text-slate-900 tracking-tight">
              Estimate Your Out-of-Pocket Cost
            </h2>
            <p className="text-base text-slate-600 font-normal">
              See how your health policy may apply to a specific medical treatment scenario.
            </p>
          </div>

          {/* Full-Width Stacked Sequential Layout (Top-to-Bottom Flow) */}
          <div className="space-y-8">
            {/* STEP 1: Policy Upload & Document Analysis (Full Width) */}
            <div className="space-y-6">
              {!activePolicyId ? (
                <PolicyUpload onUploadSuccess={handleUploadSuccess} />
              ) : (
                <PolicyAnalysisSummary
                  policyId={activePolicyId}
                  uploadData={uploadData}
                  onReset={handleReset}
                />
              )}
            </div>

            {/* Indexed Policy Document Library */}
            <PolicyList
              onSelectPolicy={handleSelectPolicy}
              activePolicyId={activePolicyId}
            />

            {/* STEP 2: Treatment Scenario Builder (Full Width) */}
            <div className="space-y-4">
              <TreatmentScenarioForm
                policyId={activePolicyId}
                onCalculate={handleCalculateScenario}
                loading={estimating}
              />

              {!activePolicyId && (
                <div className="card-white p-5 text-center text-xs text-slate-500 space-y-1 border-dashed max-w-2xl mx-auto">
                  <p className="font-semibold text-slate-700">📌 Step 1 Required</p>
                  <p>Upload a policy PDF or select an indexed document above to enable scenario calculation.</p>
                </div>
              )}
            </div>

            {/* STEP 3: Financial Breakdown Dashboard (Full Width) */}
            {estimateResult && (
              <EstimationResultDashboard
                estimate={estimateResult}
                onRecalculate={handleRoomRecalculate}
                loading={estimating}
              />
            )}
          </div>
        </div>
      </section>

      {/* Section 7: Evidence & Citation Section */}
      <EvidenceSection onInspectClick={scrollToEstimator} />

      {/* Section 8: Scenario Sensitivity Section */}
      <ScenarioSensitivitySection
        currentEstimate={estimateResult}
        onToggleRoom={handleRoomRecalculate}
        loading={estimating}
      />

      {/* Section 9: Confidence & Transparency Section */}
      <ConfidenceSection />

      {/* Section 10: Why Spasth Section */}
      <WhyFin01Section />

      {/* Section 11: Final CTA */}
      <FinalCTA onAnalyzeClick={scrollToEstimator} />

      {/* Section 12: Footer */}
      <Footer />

      {/* Section 13: Interactive AI Policy Chatbot Modal */}
      <ChatbotModal isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
    </div>
  );
}
