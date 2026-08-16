/**
 * Typed API Client for DealGuard AI Backend with Authenticated Session Management
 */

import {
  AuthResponse,
  CagrAnalysisItem,
  CurrentUserProfile,
  Deal,
  DocumentChunkItem,
  DocumentItem,
  FinancialMetricItem,
  FinancialStatementItem,
  FinancialValidationItem,
  JobExecutionItem,
  QoEAdjustmentItem,
  QoEBridgeItem,
  SemanticSearchResult,
  SystemHealth,
  SystemInfo,
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
};


