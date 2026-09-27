import React from 'react';
import { formatStatus } from '../../lib/formatters';

interface StatusBadgeProps {
  status: string;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  let badgeColor = 'bg-slate-100 text-slate-700 border-slate-200';

  if (status === 'READY' || status === 'CALCULATED') {
    badgeColor = 'bg-emerald-50 text-emerald-700 border-emerald-200';
  } else if (status === 'PARSING' || status === 'EXTRACTING' || status === 'VALIDATING' || status === 'UPLOADING') {
    badgeColor = 'bg-blue-50 text-blue-700 border-blue-200 animate-pulse';
  } else if (status === 'INCOMPLETE') {
    badgeColor = 'bg-amber-50 text-amber-700 border-amber-200';
  } else if (status === 'FAILED' || status === 'INVALID' || status === 'ERROR') {
    badgeColor = 'bg-rose-50 text-rose-700 border-rose-200';
  }

  return (
    <span
      id={`status-badge-${status.toLowerCase()}`}
      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${badgeColor}`}
    >
      <span className="w-1.5 h-1.5 mr-1.5 rounded-full bg-current" />
      {formatStatus(status)}
    </span>
  );
}
