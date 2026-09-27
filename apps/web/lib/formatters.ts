export function formatCurrency(amount: number | null | undefined): string {
  if (amount === null || amount === undefined || isNaN(amount)) {
    return '—';
  }
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatPercentage(pct: number | null | undefined): string {
  if (pct === null || pct === undefined || isNaN(pct)) {
    return '—';
  }
  return `${pct}%`;
}

export function formatRoomCategory(cat: string): string {
  switch (cat) {
    case 'GENERAL':
      return 'General Ward';
    case 'TWIN_SHARING':
      return 'Twin Sharing (Semi-Private)';
    case 'SINGLE_PRIVATE':
      return 'Single Private Room';
    case 'DELUXE':
      return 'Deluxe / Suite';
    default:
      return cat.replace(/_/g, ' ');
  }
}

export function formatStatus(status: string): string {
  switch (status) {
    case 'UPLOADING':
      return 'Uploading File';
    case 'UPLOADED':
      return 'Uploaded';
    case 'PARSING':
      return 'Parsing Policy Layout';
    case 'EXTRACTING':
      return 'Extracting Coverage Rules';
    case 'VALIDATING':
      return 'Validating Structured Policy';
    case 'READY':
      return 'Policy Ready';
    case 'FAILED':
      return 'Processing Failed';
    default:
      return status;
  }
}
