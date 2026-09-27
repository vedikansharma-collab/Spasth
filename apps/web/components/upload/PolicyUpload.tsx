'use client';

import { useState, useRef, useCallback } from 'react';
import { uploadPolicyPdf, getPolicyStatus } from '@/lib/api';
import { Upload, FileText, CheckCircle, AlertCircle, Loader2, X } from 'lucide-react';

interface PolicyUploadProps {
  onPolicyReady: (policyId: string) => void;
}

type UploadState = 'idle' | 'uploading' | 'processing' | 'ready' | 'error';
type ProcessingStep = 'UPLOADING' | 'PARSING' | 'EXTRACTING' | 'VALIDATING' | 'READY' | 'FAILED';

const STEP_LABELS: Record<ProcessingStep, string> = {
  UPLOADING: 'Uploading PDF...',
  PARSING: 'Parsing document structure...',
  EXTRACTING: 'AI extracting policy rules...',
  VALIDATING: 'Validating extracted data...',
  READY: 'Processing complete!',
  FAILED: 'Processing failed',
};

const STEP_ORDER: ProcessingStep[] = ['UPLOADING', 'PARSING', 'EXTRACTING', 'VALIDATING', 'READY'];

export function PolicyUpload({ onPolicyReady }: PolicyUploadProps) {
  const [state, setState] = useState<UploadState>('idle');
  const [currentStep, setCurrentStep] = useState<ProcessingStep>('UPLOADING');
  const [fileName, setFileName] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  const pollUntilReady = useCallback(
    (policyId: string) => {
      pollRef.current = setInterval(async () => {
        try {
          const s = await getPolicyStatus(policyId);
          const step = s.status as ProcessingStep;
          setCurrentStep(step);

          if (step === 'READY') {
            clearInterval(pollRef.current!);
            setState('ready');
            setTimeout(() => onPolicyReady(policyId), 600);
          } else if (step === 'FAILED') {
            clearInterval(pollRef.current!);
            setState('error');
            setError(s.errorMessage || 'Policy processing failed. Please try again.');
          }
        } catch (_) {}
      }, 1500);
    },
    [onPolicyReady]
  );

  const processFile = useCallback(
    async (file: File) => {
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        setError('Only PDF files are accepted');
        setState('error');
        return;
      }

      if (file.size > 25 * 1024 * 1024) {
        setError('File size exceeds 25MB limit');
        setState('error');
        return;
      }

      setFileName(file.name);
      setState('uploading');
      setCurrentStep('UPLOADING');
      setError('');

      try {
        const res = await uploadPolicyPdf(file);
        setState('processing');
        setCurrentStep('PARSING');
        pollUntilReady(res.policyId);
      } catch (err: any) {
        setState('error');
        setError(err.message || 'Upload failed. Please try again.');
      }
    },
    [pollUntilReady]
  );

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) processFile(file);
    e.target.value = '';
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) processFile(file);
  };

  const reset = () => {
    if (pollRef.current) clearInterval(pollRef.current);
    setState('idle');
    setFileName('');
    setError('');
    setCurrentStep('UPLOADING');
  };

  const stepIndex = STEP_ORDER.indexOf(currentStep);
  const progress =
    state === 'ready' ? 100 : state === 'uploading' ? 15 : Math.round((stepIndex / (STEP_ORDER.length - 1)) * 100);

  return (
    <div className="bg-slate-900/60 border border-slate-700/50 rounded-2xl p-6 backdrop-blur-sm">
      <h3 className="text-lg font-bold text-white mb-2">Upload Policy Document</h3>
      <p className="text-sm text-slate-400 mb-6">
        Upload a health insurance policy PDF to extract rules and calculate treatment costs
      </p>

      {state === 'idle' || state === 'error' ? (
        <>
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragOver(true);
            }}
            onDragLeave={() => setIsDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`relative border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all duration-200 group ${
              isDragOver
                ? 'border-indigo-500 bg-indigo-950/30'
                : 'border-slate-600/60 hover:border-indigo-500/60 hover:bg-slate-800/40'
            }`}
          >
            <input ref={fileInputRef} type="file" accept=".pdf" className="hidden" onChange={handleFileSelect} />

            <div
              className={`w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4 transition-all ${
                isDragOver ? 'bg-indigo-600 scale-110' : 'bg-slate-800 group-hover:bg-indigo-900/60'
              }`}
            >
              <Upload
                className={`w-8 h-8 ${isDragOver ? 'text-white' : 'text-slate-400 group-hover:text-indigo-400'}`}
              />
            </div>

            <p className="text-lg font-semibold text-white mb-1">
              {isDragOver ? 'Drop your PDF here' : 'Drop PDF here or click to browse'}
            </p>
            <p className="text-sm text-slate-400">Supports health insurance policies from all major Indian insurers</p>
            <p className="text-xs text-slate-500 mt-2">Maximum file size: 25MB • PDF only</p>

            {/* Glow effect on drag */}
            {isDragOver && (
              <div className="absolute inset-0 rounded-xl border-2 border-indigo-500 shadow-[0_0_40px_rgba(99,102,241,0.3)] pointer-events-none" />
            )}
          </div>

          {error && (
            <div className="mt-4 p-3 bg-red-950/60 border border-red-800/50 rounded-lg flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
              <p className="text-sm text-red-300">{error}</p>
              <button onClick={reset} className="ml-auto text-red-400 hover:text-red-200">
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Accepted insurers */}
          <div className="mt-5 flex flex-wrap gap-2">
            {['Star Health', 'HDFC ERGO', 'ICICI Lombard', 'Max Bupa', 'New India', 'Niva Bupa'].map((name) => (
              <span key={name} className="px-2.5 py-1 bg-slate-800/60 border border-slate-700/40 rounded-lg text-xs text-slate-400">
                {name}
              </span>
            ))}
            <span className="px-2.5 py-1 bg-slate-800/60 border border-slate-700/40 rounded-lg text-xs text-slate-500">+ more</span>
          </div>
        </>
      ) : (
        <div className="space-y-6">
          {/* File info */}
          <div className="flex items-center gap-3 p-4 bg-slate-800/60 rounded-xl border border-slate-700/50">
            <div className="w-10 h-10 bg-indigo-900/60 rounded-lg flex items-center justify-center shrink-0">
              <FileText className="w-5 h-5 text-indigo-400" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium text-white truncate">{fileName}</p>
              <p className="text-xs text-slate-400">PDF Document</p>
            </div>
            {state !== 'ready' && (
              <button onClick={reset} className="ml-auto text-slate-500 hover:text-slate-300 p-1">
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Progress bar */}
          <div>
            <div className="flex justify-between text-xs text-slate-400 mb-2">
              <span>{STEP_LABELS[currentStep]}</span>
              <span>{progress}%</span>
            </div>
            <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-indigo-600 to-violet-500 rounded-full transition-all duration-700 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          {/* Step indicators */}
          <div className="grid grid-cols-5 gap-2">
            {STEP_ORDER.filter((s) => s !== 'READY').map((step, idx) => {
              const completed = stepIndex > idx || state === 'ready';
              const active = stepIndex === idx && state !== 'ready';
              return (
                <div key={step} className="text-center">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center mx-auto mb-1 transition-all ${
                      completed
                        ? 'bg-emerald-600'
                        : active
                        ? 'bg-indigo-600 ring-2 ring-indigo-400/30'
                        : 'bg-slate-800 border border-slate-700'
                    }`}
                  >
                    {completed ? (
                      <CheckCircle className="w-4 h-4 text-white" />
                    ) : active ? (
                      <Loader2 className="w-4 h-4 text-white animate-spin" />
                    ) : (
                      <span className="text-xs text-slate-500">{idx + 1}</span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500 leading-tight">
                    {step === 'UPLOADING' ? 'Upload' : step === 'PARSING' ? 'Parse' : step === 'EXTRACTING' ? 'Extract' : 'Validate'}
                  </p>
                </div>
              );
            })}
            <div className="text-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center mx-auto mb-1 transition-all ${
                  state === 'ready' ? 'bg-emerald-600' : 'bg-slate-800 border border-slate-700'
                }`}
              >
                {state === 'ready' ? (
                  <CheckCircle className="w-4 h-4 text-white" />
                ) : (
                  <span className="text-xs text-slate-500">5</span>
                )}
              </div>
              <p className="text-xs text-slate-500 leading-tight">Ready</p>
            </div>
          </div>

          {state === 'ready' && (
            <div className="flex items-center gap-2 text-emerald-400 text-sm font-medium">
              <CheckCircle className="w-5 h-5" />
              Policy processed! Redirecting to estimate...
            </div>
          )}
        </div>
      )}
    </div>
  );
}
