'use client';

import { useState, useEffect } from 'react';
import { getSystemHealth } from '@/lib/api';
import { Activity, AlertTriangle } from 'lucide-react';

export function SystemHealthBanner() {
  const [status, setStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [demoMode, setDemoMode] = useState(false);

  useEffect(() => {
    getSystemHealth()
      .then((h) => {
        setStatus('online');
        setDemoMode(h.demoMode);
      })
      .catch(() => setStatus('offline'));
  }, []);

  if (status === 'checking') {
    return (
      <div className="flex items-center gap-1.5 text-xs text-slate-500">
        <div className="w-1.5 h-1.5 rounded-full bg-slate-600 animate-pulse" />
        Connecting...
      </div>
    );
  }

  if (status === 'offline') {
    return (
      <div className="flex items-center gap-1.5 text-xs text-red-400 bg-red-950/40 border border-red-800/40 px-3 py-1.5 rounded-full">
        <AlertTriangle className="w-3.5 h-3.5" />
        API Offline — Start the backend server
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3">
      {demoMode && (
        <span className="text-xs text-yellow-400 bg-yellow-950/40 border border-yellow-800/40 px-2.5 py-1 rounded-full">
          Demo Mode
        </span>
      )}
      <div className="flex items-center gap-1.5 text-xs text-emerald-400">
        <Activity className="w-3.5 h-3.5" />
        API Online
      </div>
    </div>
  );
}
