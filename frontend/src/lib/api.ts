/**
 * Typed API Client for DealGuard AI Backend with Authenticated Session Management
 */

import {
  AuthResponse,
  CagrAnalysisItem,
  ComparableAnalysisItem,
  ComparableCompanyItem,
  CurrentUserProfile,
  DcfValuationItem,
  Deal,
  DocumentChunkItem,
  DocumentItem,
  FinancialMetricItem,
  FinancialStatementItem,
  FinancialValidationItem,
  JobExecutionItem,
  PrecedentAnalysisItem,
  PrecedentTransactionItem,
  QoEAdjustmentItem,
  QoEBridgeItem,
  SemanticSearchResult,
  SensitivityMatrixItem,
  SystemHealth,
  SystemInfo,
  ValuationAssumptionItem,
  ValuationItem,
  ValuationSummaryItem,
  ValuationValidationItem,
  WaccAnalysisItem,
} from '@/types';




const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details?: Record<string, any>
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// In-memory access token storage
let currentAccessToken: string | null = null;
let currentOrgId: string | null = null;

export const tokenStore = {
  getAccessToken: () => currentAccessToken,
  setAccessToken: (token: string | null) => {
    currentAccessToken = token;
    if (typeof window !== 'undefined') {
      if (token) {
        sessionStorage.setItem('dealguard_access_token', token);
      } else {
        sessionStorage.removeItem('dealguard_access_token');
      }
    }
  },
  getOrgId: () => currentOrgId,
  setOrgId: (orgId: string | null) => {
    currentOrgId = orgId;
    if (typeof window !== 'undefined') {
      if (orgId) {
        localStorage.setItem('dealguard_active_org_id', orgId);
      } else {
        localStorage.removeItem('dealguard_active_org_id');
      }
    }
  },
  init: () => {
    if (typeof window !== 'undefined') {
      currentAccessToken = sessionStorage.getItem('dealguard_access_token');
      currentOrgId = localStorage.getItem('dealguard_active_org_id');
    }
  },
};

async function fetchJson<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  tokenStore.init();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };

  if (currentAccessToken && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${currentAccessToken}`;
  }

  if (currentOrgId && !headers['X-Organization-ID']) {
    headers['X-Organization-ID'] = currentOrgId;
  }

  try {
    const res = await fetch(url, {
      ...options,
      headers,
    });

    if (!res.ok) {
      let errorData = { code: 'HTTP_ERROR', message: res.statusText, details: {} };
      try {
        const json = await res.json();
        if (json.error) {
          errorData = json.error;
        }
      } catch {
        // Fallback to statusText
      }
      throw new ApiError(res.status, errorData.code, errorData.message, errorData.details);
    }

    return await res.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(500, 'NETWORK_ERROR', (error as Error).message);
  }
}

export const api = {
  // System Health
  getHealth: () => fetchJson<SystemHealth>('/health'),
  getReadiness: () => fetchJson<SystemHealth>('/health/ready'),
  getSystemInfo: () => fetchJson<SystemInfo>('/system/info'),

  // Authentication
  login: (email: string, password: string, organizationId?: string) =>
    fetchJson<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password, organization_id: organizationId }),
    }),

  refreshToken: (refreshToken: string) =>
    fetchJson<AuthResponse>('/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    }),

  logout: (refreshToken: string) =>
    fetchJson<{ success: boolean; message: string }>('/auth/logout', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    }),

  getMe: () => fetchJson<CurrentUserProfile>('/auth/me'),

  // Deals
  getDeals: () => fetchJson<Deal[]>('/deals'),

  // Documents & Ingestion
  getDealDocuments: (dealId: string) => fetchJson<DocumentItem[]>(`/deals/${dealId}/documents`),

  getDocumentDetails: (dealId: string, documentId: string) =>
    fetchJson<DocumentItem>(`/deals/${dealId}/documents/${documentId}`),

  getDocumentChunks: (dealId: string, documentId: string) =>
    fetchJson<DocumentChunkItem[]>(`/deals/${dealId}/documents/${documentId}/chunks`),

  uploadDocument: async (dealId: string, file: File, category?: string): Promise<{ document: DocumentItem; job: JobExecutionItem }> => {
    const formData = new FormData();
    formData.append('file', file);
    if (category) formData.append('category', category);

    tokenStore.init();
    const token = tokenStore.getAccessToken();
    const orgId = tokenStore.getOrgId();

    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    if (orgId) headers['X-Organization-ID'] = orgId;

    const res = await fetch(`${API_BASE}/deals/${dealId}/documents/upload`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!res.ok) {
      let errorData = { code: 'HTTP_ERROR', message: res.statusText, details: {} };
      try {
        const json = await res.json();
        if (json.error) errorData = json.error;
      } catch {}
      throw new ApiError(res.status, errorData.code, errorData.message, errorData.details);
    }
    return await res.json();
  },

  searchDealEvidence: (dealId: string, query: string, topK: number = 5) =>
    fetchJson<SemanticSearchResult[]>(`/deals/${dealId}/documents/search`, {
      method: 'POST',
      body: JSON.stringify({ query, top_k: topK }),
    }),

  // Background Jobs
  getJobStatus: (jobId: string) => fetchJson<JobExecutionItem>(`/jobs/${jobId}`),

  // Financials & 3-Statements
  getFinancialStatements: (dealId: string) =>
    fetchJson<FinancialStatementItem[]>(`/deals/${dealId}/financials/statements`),

  upsertFinancialStatement: (dealId: string, payload: any) =>
    fetchJson<FinancialStatementItem>(`/deals/${dealId}/financials/statements`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getFinancialMetrics: (dealId: string) =>
    fetchJson<FinancialMetricItem[]>(`/deals/${dealId}/financials/metrics`),

  getDealCagr: (dealId: string) =>
    fetchJson<CagrAnalysisItem>(`/deals/${dealId}/financials/cagr`),

  getQoEBridge: (dealId: string, period: string = 'FY2023') =>
    fetchJson<QoEBridgeItem>(`/deals/${dealId}/financials/qoe?period=${encodeURIComponent(period)}`),

  createQoEAdjustment: (dealId: string, payload: any) =>
    fetchJson<QoEAdjustmentItem>(`/deals/${dealId}/financials/qoe`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  updateQoEAdjustment: (dealId: string, adjustmentId: string, payload: any) =>
    fetchJson<QoEAdjustmentItem>(`/deals/${dealId}/financials/qoe/${adjustmentId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  deleteQoEAdjustment: (dealId: string, adjustmentId: string) =>
    fetchJson<{ success: boolean; message: string }>(`/deals/${dealId}/financials/qoe/${adjustmentId}`, {
      method: 'DELETE',
    }),

  getFinancialValidation: (dealId: string) =>
    fetchJson<FinancialValidationItem>(`/deals/${dealId}/financials/validation`),

  // Valuation Intelligence Engine
  getValuation: (dealId: string) =>
    fetchJson<ValuationItem>(`/deals/${dealId}/valuation`),

  updateValuation: (dealId: string, valuationId: string, payload: any) =>
    fetchJson<ValuationItem>(`/deals/${dealId}/valuation/${valuationId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  getWaccAnalysis: (dealId: string) =>
    fetchJson<WaccAnalysisItem>(`/deals/${dealId}/valuation/wacc`),

  calculateWacc: (dealId: string, payload: any) =>
    fetchJson<WaccAnalysisItem>(`/deals/${dealId}/valuation/wacc/calculate`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getValuationAssumptions: (dealId: string) =>
    fetchJson<ValuationAssumptionItem[]>(`/deals/${dealId}/valuation/assumptions`),

  upsertValuationAssumption: (dealId: string, payload: any) =>
    fetchJson<ValuationAssumptionItem>(`/deals/${dealId}/valuation/assumptions`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getDcfValuation: (dealId: string, terminalMethod: string = 'PERPETUITY_GROWTH') =>
    fetchJson<DcfValuationItem>(`/deals/${dealId}/valuation/dcf?terminal_method=${encodeURIComponent(terminalMethod)}`),

  calculateDcf: (dealId: string, payload: any) =>
    fetchJson<DcfValuationItem>(`/deals/${dealId}/valuation/dcf/calculate`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getComparables: (dealId: string) =>
    fetchJson<ComparableAnalysisItem>(`/deals/${dealId}/valuation/comparables`),

  createComparable: (dealId: string, payload: any) =>
    fetchJson<ComparableCompanyItem>(`/deals/${dealId}/valuation/comparables`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  updateComparable: (dealId: string, compId: string, payload: any) =>
    fetchJson<ComparableCompanyItem>(`/deals/${dealId}/valuation/comparables/${compId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  deleteComparable: (dealId: string, compId: string) =>
    fetchJson<{ success: boolean; message: string }>(`/deals/${dealId}/valuation/comparables/${compId}`, {
      method: 'DELETE',
    }),

  getPrecedents: (dealId: string) =>
    fetchJson<PrecedentAnalysisItem>(`/deals/${dealId}/valuation/precedents`),

  createPrecedent: (dealId: string, payload: any) =>
    fetchJson<PrecedentTransactionItem>(`/deals/${dealId}/valuation/precedents`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  updatePrecedent: (dealId: string, txId: string, payload: any) =>
    fetchJson<PrecedentTransactionItem>(`/deals/${dealId}/valuation/precedents/${txId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  deletePrecedent: (dealId: string, txId: string) =>
    fetchJson<{ success: boolean; message: string }>(`/deals/${dealId}/valuation/precedents/${txId}`, {
      method: 'DELETE',
    }),

  getValuationSensitivity: (dealId: string, matrixType: string = 'WACC_VS_GROWTH') =>
    fetchJson<SensitivityMatrixItem>(`/deals/${dealId}/valuation/sensitivity?matrix_type=${encodeURIComponent(matrixType)}`),

  getValuationSummary: (dealId: string) =>
    fetchJson<ValuationSummaryItem>(`/deals/${dealId}/valuation/summary`),

  getValuationValidation: (dealId: string) =>
    fetchJson<ValuationValidationItem>(`/deals/${dealId}/valuation/validation`),

  // ==========================================
  // Phase 7: 17-Pillar Risk Intelligence APIs
  // ==========================================
  listRisks: (
    dealId: string,
    params?: {
      category?: string;
      risk_level?: string;
      status?: string;
      min_severity?: number;
      min_likelihood?: number;
      search?: string;
      sort_by?: string;
      sort_desc?: boolean;
      offset?: number;
      limit?: number;
    }
  ) => {
    const query = new URLSearchParams();
    if (params?.category) query.append('category', params.category);
    if (params?.risk_level) query.append('risk_level', params.risk_level);
    if (params?.status) query.append('status', params.status);
    if (params?.min_severity) query.append('min_severity', params.min_severity.toString());
    if (params?.min_likelihood) query.append('min_likelihood', params.min_likelihood.toString());
    if (params?.search) query.append('search', params.search);
    if (params?.sort_by) query.append('sort_by', params.sort_by);
    if (params?.sort_desc !== undefined) query.append('sort_desc', params.sort_desc.toString());
    if (params?.offset !== undefined) query.append('offset', params.offset.toString());
    if (params?.limit !== undefined) query.append('limit', params.limit.toString());
    const qs = query.toString() ? `?${query.toString()}` : '';
    return fetchJson<{ total: number; items: any[] }>(`/deals/${dealId}/risks${qs}`);
  },

  getRiskMatrix: (dealId: string) =>
    fetchJson<any>(`/deals/${dealId}/risks/matrix`),

  getRiskCategories: (dealId: string) =>
    fetchJson<any[]>(`/deals/${dealId}/risks/categories`),

  createRisk: (dealId: string, payload: any) =>
    fetchJson<any>(`/deals/${dealId}/risks`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  detectRisks: (dealId: string, payload?: { categories?: string[]; min_confidence?: number }) =>
    fetchJson<any>(`/deals/${dealId}/risks/detect`, {
      method: 'POST',
      body: JSON.stringify(payload || { min_confidence: 0.6 }),
    }),

  getRisk: (dealId: string, riskId: string) =>
    fetchJson<any>(`/deals/${dealId}/risks/${riskId}`),

  updateRisk: (dealId: string, riskId: string, payload: any) =>
    fetchJson<any>(`/deals/${dealId}/risks/${riskId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),

  updateRiskStatus: (dealId: string, riskId: string, payload: { status: string; rationale?: string }) =>
    fetchJson<any>(`/deals/${dealId}/risks/${riskId}/status`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  deleteRisk: (dealId: string, riskId: string) =>
    fetchJson<void>(`/deals/${dealId}/risks/${riskId}`, {
      method: 'DELETE',
    }),

  // ==========================================
  // Phase 8: Composite Decision Score APIs
  // ==========================================
  getDecisionScore: (dealId: string, forceRecalculate: boolean = false) =>
    fetchJson<any>(`/deals/${dealId}/decision-score${forceRecalculate ? '?force_recalculate=true' : ''}`),

  calculateDecisionScore: (dealId: string, payload?: { custom_weights?: Record<string, number> }) =>
    fetchJson<any>(`/deals/${dealId}/decision-score/calculate`, {
      method: 'POST',
      body: JSON.stringify(payload || {}),
    }),

  getDecisionScoreBreakdown: (dealId: string) =>
    fetchJson<any>(`/deals/${dealId}/decision-score/breakdown`),

  getDecisionScoreHistory: (dealId: string, limit: number = 50) =>
    fetchJson<any>(`/deals/${dealId}/decision-score/history?limit=${limit}`),
};



