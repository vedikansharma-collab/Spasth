import {
  CalculationResponse,
  Procedure,
  HospitalCostScenario,
  TreatmentScenarioInput,
} from '@policy-estimator/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options);
  if (!res.ok) {
    let errMessage = `HTTP error ${res.status}`;
    try {
      const errData = await res.json();
      errMessage = errData.message || errData.errorCode || errMessage;
    } catch (_) {}
    throw new Error(errMessage);
  }
  return res.json();
}

export async function uploadPolicyPdf(file: File): Promise<{ policyId: string; status: string }> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/api/policies/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: 'Upload failed' }));
    throw new Error(err.message || 'Policy upload failed');
  }

  return res.json();
}

export async function getPolicy(id: string): Promise<any> {
  return fetchJson(`${API_BASE}/api/policies/${id}`);
}

export async function getPolicyStatus(id: string): Promise<{ id: string; status: string; errorMessage?: string }> {
  return fetchJson(`${API_BASE}/api/policies/${id}/status`);
}

export async function getLatestPolicy(): Promise<any> {
  return fetchJson(`${API_BASE}/api/policies/latest`);
}

export async function getProcedures(): Promise<Procedure[]> {
  return fetchJson(`${API_BASE}/api/procedures`);
}

export async function getProcedureCosts(procedureCode: string): Promise<HospitalCostScenario[]> {
  return fetchJson(`${API_BASE}/api/procedures/${procedureCode}/costs`);
}

export async function calculateTreatment(
  policyId: string,
  input: TreatmentScenarioInput
): Promise<CalculationResponse> {
  return fetchJson(`${API_BASE}/api/calculations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      policyId,
      procedureCode: input.procedureCode,
      roomCategory: input.roomCategory,
      stayDays: input.stayDays,
      city: input.city,
      customRoomRate: input.customRoomRate,
    }),
  });
}

export async function recalculateTreatment(
  policyId: string,
  input: TreatmentScenarioInput
): Promise<CalculationResponse> {
  return fetchJson(`${API_BASE}/api/calculations/recalculate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      policyId,
      procedureCode: input.procedureCode,
      roomCategory: input.roomCategory,
      stayDays: input.stayDays,
      city: input.city,
      customRoomRate: input.customRoomRate,
    }),
  });
}

export async function getCalculation(id: string): Promise<any> {
  return fetchJson(`${API_BASE}/api/calculations/${id}`);
}

export async function getSystemHealth(): Promise<any> {
  return fetchJson(`${API_BASE}/api/health`);
}
