import { create } from 'zustand';
import {
  CalculationResponse,
  RoomCategory,
  CitationReference,
} from '@policy-estimator/types';

interface ScenarioState {
  policyId: string | null;
  policyData: any | null;
  selectedProcedureCode: string;
  selectedRoomCategory: RoomCategory;
  stayDays: number;
  city: string;
  calculation: CalculationResponse | null;
  isRecalculating: boolean;
  
  // PDF & Citation Navigation
  activePdfPage: number;
  pdfZoom: number;
  activeCitation: CitationReference | null;

  // Actions
  setPolicy: (id: string, data?: any) => void;
  setScenario: (params: {
    procedureCode?: string;
    roomCategory?: RoomCategory;
    stayDays?: number;
    city?: string;
  }) => void;
  setCalculation: (calc: CalculationResponse | null) => void;
  setIsRecalculating: (val: boolean) => void;
  jumpToCitation: (citation: CitationReference) => void;
  setPdfPage: (page: number) => void;
  setPdfZoom: (zoom: number) => void;
  reset: () => void;
}

export const useScenarioStore = create<ScenarioState>((set) => ({
  policyId: null,
  policyData: null,
  selectedProcedureCode: 'PROC-APP-LAP',
  selectedRoomCategory: 'SINGLE_PRIVATE',
  stayDays: 2,
  city: 'National Average',
  calculation: null,
  isRecalculating: false,

  activePdfPage: 12, // Default to room rent page for demo
  pdfZoom: 100,
  activeCitation: null,

  setPolicy: (id, data) => set({ policyId: id, policyData: data || null }),
  setScenario: (params) =>
    set((state) => ({
      selectedProcedureCode: params.procedureCode ?? state.selectedProcedureCode,
      selectedRoomCategory: params.roomCategory ?? state.selectedRoomCategory,
      stayDays: params.stayDays ?? state.stayDays,
      city: params.city ?? state.city,
    })),
  setCalculation: (calc) => set({ calculation: calc }),
  setIsRecalculating: (val) => set({ isRecalculating: val }),
  jumpToCitation: (citation) =>
    set({
      activePdfPage: citation.page,
      activeCitation: citation,
    }),
  setPdfPage: (page) => set({ activePdfPage: page }),
  setPdfZoom: (zoom) => set({ pdfZoom: zoom }),
  reset: () =>
    set({
      policyId: null,
      policyData: null,
      calculation: null,
      activeCitation: null,
      activePdfPage: 1,
    }),
}));
