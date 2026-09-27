import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingStateProps {
  message?: string;
  subtext?: string;
}

export function LoadingState({
  message = 'Processing request...',
  subtext,
}: LoadingStateProps) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center space-y-3">
      <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
      <p className="text-sm font-medium text-slate-800">{message}</p>
      {subtext && <p className="text-xs text-slate-500 max-w-sm">{subtext}</p>}
    </div>
  );
}
