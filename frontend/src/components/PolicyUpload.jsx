import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, AlertTriangle, Loader2, ArrowRight, ShieldCheck } from 'lucide-react';
import { uploadPolicy } from '../services/api';

export default function PolicyUpload({ onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState('');
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const validateAndSetFile = (selectedFile) => {
    setError(null);
    if (!selectedFile) return;

    if (!selectedFile.name.toLowerCase().endsWith('.pdf')) {
      setError('Invalid file format. Please upload an insurance policy document in PDF format (.pdf).');
      return;
    }

    if (selectedFile.size > 25 * 1024 * 1024) {
      setError('File size exceeds maximum limit of 25MB.');
      return;
    }

    setFile(selectedFile);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleUploadSubmit = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);
    setProgress(15);
    setStatusMessage('Uploading policy PDF...');

    try {
      const response = await uploadPolicy(file, (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 80) / progressEvent.total);
        setProgress(percentCompleted);
      });

      setProgress(85);
      setStatusMessage('Extracting policy text & identifying clauses...');
      
      setTimeout(() => {
        setProgress(100);
        setStatusMessage('Ready to estimate ✓');
        setUploading(false);
        if (onUploadSuccess) {
          onUploadSuccess(response);
        }
      }, 400);

    } catch (err) {
      console.error('Upload Error:', err);
      setUploading(false);
      setProgress(0);
      const msg = err.response?.data?.detail || err.message || 'Failed to upload and process policy document.';
      setError(msg);
    }
  };

  return (
    <div className="card-white p-6 sm:p-7 space-y-5">
      <div className="flex items-center space-x-3">
        <div className="w-10 h-10 rounded-xl bg-[rgba(57,171,173,0.12)] border border-[#39ABAD]/40 flex items-center justify-center text-[#006668]">
          <UploadCloud className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-base font-bold text-[#003339]">Upload Health Insurance Policy</h3>
          <p className="text-xs text-[#4A5859]">Upload a policy schedule PDF to parse rules and page citations.</p>
        </div>
      </div>

      {/* Drag & Drop Zone */}
      <div
        className={`border-2 border-dashed rounded-xl p-6 sm:p-8 text-center transition-all cursor-pointer ${
          dragActive
            ? 'border-[#006668] bg-[rgba(57,171,173,0.08)]'
            : file
            ? 'border-[#39ABAD] bg-[rgba(57,171,173,0.05)]'
            : 'border-[#E2E8E8] hover:border-[#39ABAD] bg-[#F7F7F8] hover:bg-white'
        }`}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,application/pdf"
          className="hidden"
          onChange={handleChange}
        />

        {file ? (
          <div className="flex flex-col items-center space-y-2.5">
            <div className="w-12 h-12 rounded-xl bg-[rgba(57,171,173,0.12)] border border-[#39ABAD]/40 flex items-center justify-center text-[#006668]">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-bold text-[#003339]">{file.name}</p>
              <p className="text-xs text-[#4A5859] font-mono mt-0.5">
                {(file.size / (1024 * 1024)).toFixed(2)} MB • PDF Document
              </p>
            </div>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setFile(null);
                setError(null);
              }}
              className="text-xs font-medium text-[#D51B1D] hover:underline cursor-pointer"
            >
              Choose a different document
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center space-y-2.5">
            <div className="w-12 h-12 rounded-xl bg-white border border-[#E2E8E8] flex items-center justify-center text-[#006668] shadow-2xs">
              <UploadCloud className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-semibold text-[#003339]">
                Drag & drop your policy PDF, or <span className="text-[#006668] underline">browse</span>
              </p>
              <p className="text-xs text-[#4A5859] mt-0.5">Supports PDF documents up to 25MB</p>
            </div>
          </div>
        )}
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-3.5 rounded-xl bg-[rgba(213,27,29,0.06)] border border-[#D51B1D]/40 text-[#D51B1D] text-xs flex items-start space-x-2.5">
          <AlertTriangle className="w-4 h-4 text-[#D51B1D] flex-shrink-0 mt-0.5" />
          <div>
            <strong className="font-semibold block text-[#003339]">Upload Error</strong>
            {error}
          </div>
        </div>
      )}

      {/* Uploading Progress */}
      {uploading && (
        <div className="space-y-2">
          <div className="flex justify-between text-xs text-[#003339] font-medium">
            <span className="flex items-center space-x-2">
              <Loader2 className="w-3.5 h-3.5 text-[#006668] animate-spin" />
              <span>{statusMessage}</span>
            </span>
            <span className="font-mono text-[#006668] font-bold">{progress}%</span>
          </div>
          <div className="w-full h-2 bg-[#F7F7F8] rounded-full overflow-hidden border border-[#E2E8E8]">
            <div
              className="h-full bg-[#006668] transition-all duration-300 rounded-full"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>
      )}

      {/* Submit Action */}
      <button
        type="button"
        disabled={!file || uploading}
        onClick={handleUploadSubmit}
        className={`w-full py-3 rounded-xl text-sm font-bold flex items-center justify-center space-x-2 transition-all cursor-pointer ${
          !file || uploading
            ? 'bg-[#F7F7F8] text-[#4A5859]/60 border border-[#E2E8E8] cursor-not-allowed'
            : 'btn-primary'
        }`}
      >
        {uploading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin text-white" />
            <span>Processing Policy Document...</span>
          </>
        ) : (
          <>
            <ShieldCheck className="w-4 h-4" />
            <span>Process &amp; Index Policy</span>
            <ArrowRight className="w-4 h-4" />
          </>
        )}
      </button>
    </div>
  );
}
