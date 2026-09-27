'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { PolicyUpload } from '@/components/upload/PolicyUpload';
import { DemoModeCard } from '@/components/common/DemoModeCard';
import { SystemHealthBanner } from '@/components/common/SystemHealthBanner';
import { getLatestPolicy } from '@/lib/api';
import { Shield, Brain, Calculator, FileText, ChevronRight, Zap, Lock, Eye } from 'lucide-react';

export default function HomePage() {
  const router = useRouter();
  const [hasExistingPolicy, setHasExistingPolicy] = useState(false);
  const [latestPolicyId, setLatestPolicyId] = useState<string | null>(null);

  useEffect(() => {
    getLatestPolicy()
      .then((p) => {
        if (p?.id) {
          setHasExistingPolicy(true);
          setLatestPolicyId(p.id);
        }
      })
      .catch(() => {});
  }, []);

  const handlePolicyReady = (policyId: string) => {
    router.push(`/estimate/${policyId}`);
  };

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        {/* Background Grid Pattern */}
        <div
          className="absolute inset-0 opacity-5"
          style={{
            backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
            backgroundSize: '40px 40px',
          }}
        />

        {/* Gradient Orbs */}
        <div className="absolute top-20 left-20 w-96 h-96 bg-indigo-600/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute top-40 right-20 w-80 h-80 bg-violet-600/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[600px] h-64 bg-blue-700/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative max-w-7xl mx-auto px-4 pt-12 pb-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-12">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-indigo-600 rounded-xl shadow-lg shadow-indigo-900/50">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-white">PolicyEstimator</h1>
                <p className="text-xs text-slate-400">AI-Powered Cost Transparency</p>
              </div>
            </div>

            <SystemHealthBanner />
          </div>

          {/* Hero Text */}
          <div className="text-center max-w-4xl mx-auto mb-12">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-950/80 border border-indigo-700/50 rounded-full text-sm text-indigo-300 mb-6 shadow-lg">
              <Zap className="w-4 h-4 text-yellow-400" />
              <span>Zero guesswork. Deterministic calculations. Full policy citations.</span>
            </div>

            <h2 className="text-5xl md:text-6xl font-extrabold text-white tracking-tight mb-6 leading-tight">
              Know Exactly What Your{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-violet-400">
                Insurance Covers
              </span>{' '}
              Before You're Admitted
            </h2>

            <p className="text-xl text-slate-300 leading-relaxed max-w-3xl mx-auto">
              Upload your health policy PDF. Our AI extracts every clause — room rent caps, co-payments, sub-limits,
              waiting periods. Then a deterministic engine calculates your exact out-of-pocket cost for any treatment.
            </p>
          </div>

          {/* Feature Pills */}
          <div className="flex flex-wrap justify-center gap-3 mb-12">
            {[
              { icon: Brain, text: 'LLM Extraction', sub: 'Gemini/GPT-powered' },
              { icon: Calculator, text: 'Deterministic Math', sub: 'Zero AI in calculations' },
              { icon: FileText, text: 'Page Citations', sub: 'Every rule cited' },
              { icon: Lock, text: 'Demo Mode', sub: 'No API key needed' },
              { icon: Eye, text: 'Full Audit Trail', sub: '9-step trace' },
            ].map(({ icon: Icon, text, sub }) => (
              <div
                key={text}
                className="flex items-center gap-2 px-4 py-2.5 bg-slate-800/60 border border-slate-700/60 rounded-xl backdrop-blur-sm hover:border-indigo-500/50 transition-colors"
              >
                <Icon className="w-4 h-4 text-indigo-400" />
                <div>
                  <div className="text-sm font-medium text-white">{text}</div>
                  <div className="text-xs text-slate-400">{sub}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 pb-16">
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
          {/* Left: Upload Area */}
          <div className="lg:col-span-3">
            <PolicyUpload onPolicyReady={handlePolicyReady} />
          </div>

          {/* Right: Demo Mode Card + How it Works */}
          <div className="lg:col-span-2 space-y-6">
            {/* Demo Mode Card */}
            <DemoModeCard
              hasSamplePolicy={hasExistingPolicy}
              samplePolicyId={latestPolicyId}
              onLoadDemo={handlePolicyReady}
            />

            {/* How it Works */}
            <div className="bg-slate-900/60 border border-slate-700/50 rounded-2xl p-6 backdrop-blur-sm">
              <h3 className="text-lg font-bold text-white mb-5 flex items-center gap-2">
                <ChevronRight className="w-5 h-5 text-indigo-400" />
                How It Works
              </h3>
              <div className="space-y-4">
                {[
                  {
                    step: '01',
                    title: 'Upload PDF',
                    desc: 'Drop your insurance policy PDF. Accepted from all major Indian insurers.',
                    color: 'text-blue-400',
                  },
                  {
                    step: '02',
                    title: 'AI Extracts Rules',
                    desc: 'LLM reads every clause: room caps, co-pays, sub-limits, exclusions with page citations.',
                    color: 'text-violet-400',
                  },
                  {
                    step: '03',
                    title: 'Select Procedure',
                    desc: 'Choose from 15+ procedures with benchmark hospital cost data.',
                    color: 'text-indigo-400',
                  },
                  {
                    step: '04',
                    title: 'Get Exact Estimate',
                    desc: 'Deterministic 9-step engine calculates your exact insurer payment and OOP cost.',
                    color: 'text-emerald-400',
                  },
                ].map(({ step, title, desc, color }) => (
                  <div key={step} className="flex gap-4">
                    <div className={`text-2xl font-black ${color} opacity-60 w-8 shrink-0 leading-tight`}>
                      {step}
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-white mb-0.5">{title}</div>
                      <div className="text-xs text-slate-400 leading-relaxed">{desc}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Trust Signals */}
            <div className="bg-gradient-to-br from-emerald-950/60 to-teal-950/60 border border-emerald-800/40 rounded-2xl p-5">
              <div className="flex items-center gap-2 mb-3">
                <Lock className="w-4 h-4 text-emerald-400" />
                <span className="text-sm font-semibold text-emerald-300">Privacy &amp; Accuracy</span>
              </div>
              <ul className="space-y-2 text-xs text-slate-300">
                <li className="flex items-start gap-2">
                  <span className="text-emerald-400 mt-0.5">✓</span>
                  PDFs are processed locally and never shared with third parties
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-400 mt-0.5">✓</span>
                  Calculations are 100% deterministic — same inputs always produce same output
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-400 mt-0.5">✓</span>
                  Every policy clause linked to exact page number for verification
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-400 mt-0.5">✓</span>
                  Estimates are advisory — always confirm with your insurer
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
