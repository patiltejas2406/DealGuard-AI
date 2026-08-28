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
  CopilotCitation,
} from '@/types';




export function getApiBaseUrl(): string {
  const envUrl = process.env.NEXT_PUBLIC_API_URL;
  if (envUrl && typeof envUrl === 'string' && envUrl.trim() !== '') {
    const cleaned = envUrl.trim().replace(/\/+$/, '');
    if (typeof window !== 'undefined') {
      const hostname = window.location.hostname;
      const isRemoteHost = hostname !== 'localhost' && hostname !== '127.0.0.1';
      if (isRemoteHost && cleaned.includes('localhost')) {
        return 'https://victorious-charisma-production-9f0c.up.railway.app/api/v1';
      }
    }
    return cleaned;
  }

  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    const isRemoteHost = hostname !== 'localhost' && hostname !== '127.0.0.1';
    if (isRemoteHost) {
      return 'https://victorious-charisma-production-9f0c.up.railway.app/api/v1';
    }
  }

  return 'http://localhost:8000/api/v1';
}

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
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

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
      credentials: options.credentials || 'include',
    });

    if (!res.ok) {
      let errorData = { code: 'HTTP_ERROR', message: res.statusText, details: {} };
      try {
        const json = await res.json();
        if (json.error) {
          errorData = json.error;
        } else if (json.detail) {
          errorData.message = typeof json.detail === 'string' ? json.detail : JSON.stringify(json.detail);
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
    const rawMsg = (error as Error).message || '';
    const isNetworkAbort = rawMsg === 'Load failed' || rawMsg.includes('Failed to fetch') || rawMsg.includes('NetworkError');
    const msg = isNetworkAbort
      ? `Unable to connect to backend at ${baseUrl}. Please verify internet access and ensure your browser is not blocking cross-origin requests.`
      : rawMsg || 'An unknown network error occurred.';
    throw new ApiError(500, 'NETWORK_ERROR', msg);
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

    const res = await fetch(`${getApiBaseUrl()}/deals/${dealId}/documents/upload`, {
      method: 'POST',
      headers,
      body: formData,
      credentials: 'include',
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

  // ==========================================
  // Phase 9: What-If & Monte Carlo Simulation APIs
  // ==========================================
  getScenarios: (dealId: string) =>
    fetchJson<any[]>(`/deals/${dealId}/scenarios`),

  createScenario: (dealId: string, payload: { name: string; description?: string; scenario_type?: string; assumptions: Record<string, number> }) =>
    fetchJson<any>(`/deals/${dealId}/scenarios`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getScenario: (dealId: string, scenarioId: string) =>
    fetchJson<any>(`/deals/${dealId}/scenarios/${scenarioId}`),

  runScenario: (dealId: string, scenarioId: string) =>
    fetchJson<any>(`/deals/${dealId}/scenarios/${scenarioId}/run`, {
      method: 'POST',
    }),

  deleteScenario: (dealId: string, scenarioId: string) =>
    fetchJson<void>(`/deals/${dealId}/scenarios/${scenarioId}`, {
      method: 'DELETE',
    }),

  runSensitivity: (dealId: string, payload: any) =>
    fetchJson<any>(`/deals/${dealId}/scenarios/sensitivity`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  runMonteCarlo: (dealId: string, payload: { variable_distributions: Record<string, any>; iterations?: number; random_seed?: number }) =>
    fetchJson<any>(`/deals/${dealId}/scenarios/monte-carlo`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // ==========================================
  // Phase 10: Synergy Realization & Value Creation APIs
  // ==========================================
  getSynergies: (dealId: string, synergyType?: string) =>
    fetchJson<any[]>(`/deals/${dealId}/synergies${synergyType ? `?synergy_type=${synergyType}` : ''}`),

  createSynergy: (dealId: string, payload: any) =>
    fetchJson<any>(`/deals/${dealId}/synergies`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getSynergy: (dealId: string, synergyId: string) =>
    fetchJson<any>(`/deals/${dealId}/synergies/${synergyId}`),

  updateSynergy: (dealId: string, synergyId: string, payload: any) =>
    fetchJson<any>(`/deals/${dealId}/synergies/${synergyId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),

  updateSynergyStatus: (dealId: string, synergyId: string, payload: { status: string; notes?: string }) =>
    fetchJson<any>(`/deals/${dealId}/synergies/${synergyId}/status`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  logSynergyActual: (dealId: string, synergyId: string, payload: { fiscal_period: string; planned_value: number; actual_value: number; notes?: string }) =>
    fetchJson<any>(`/deals/${dealId}/synergies/${synergyId}/actual`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  deleteSynergy: (dealId: string, synergyId: string) =>
    fetchJson<void>(`/deals/${dealId}/synergies/${synergyId}`, {
      method: 'DELETE',
    }),

  getSynergySummary: (dealId: string) =>
    fetchJson<any>(`/deals/${dealId}/synergies/summary`),

  getSynergyValueBridge: (dealId: string) =>
    fetchJson<any>(`/deals/${dealId}/synergies/value-bridge`),

  getSynergyRealizationSchedule: (dealId: string) =>
    fetchJson<any>(`/deals/${dealId}/synergies/realization`),

  // ==========================================
  // Phase 11: 100-Day Integration Execution APIs
  // ==========================================
  getIntegrationProgram: (dealId: string) =>
    fetchJson<any>(`/deals/${dealId}/integration`),

  createIntegrationProgram: (dealId: string, payload: any) =>
    fetchJson<any>(`/deals/${dealId}/integration`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  updateIntegrationProgram: (dealId: string, payload: any) =>
    fetchJson<any>(`/deals/${dealId}/integration`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),

  getWorkstreams: (dealId: string, category?: string) =>
    fetchJson<any[]>(`/deals/${dealId}/integration/workstreams${category ? `?category=${category}` : ''}`),

  createWorkstream: (dealId: string, payload: any) =>
    fetchJson<any>(`/deals/${dealId}/integration/workstreams`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  updateWorkstreamStatus: (dealId: string, workstreamId: string, payload: { status: string; notes?: string }) =>
    fetchJson<any>(`/deals/${dealId}/integration/workstreams/${workstreamId}/status`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  getMilestones: (dealId: string, workstreamId?: string) =>
    fetchJson<any[]>(`/deals/${dealId}/integration/milestones${workstreamId ? `?workstream_id=${workstreamId}` : ''}`),

  createMilestone: (dealId: string, payload: any) =>
    fetchJson<any>(`/deals/${dealId}/integration/milestones`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  updateMilestoneStatus: (dealId: string, milestoneId: string, payload: { status: string; completion_pct?: number; notes?: string }) =>
    fetchJson<any>(`/deals/${dealId}/integration/milestones/${milestoneId}/status`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  createDependency: (dealId: string, payload: { predecessor_id: string; successor_id: string; dependency_type?: string }) =>
    fetchJson<any>(`/deals/${dealId}/integration/dependencies`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  deleteDependency: (dealId: string, dependencyId: string) =>
    fetchJson<void>(`/deals/${dealId}/integration/dependencies/${dependencyId}`, {
      method: 'DELETE',
    }),

  getBlockers: (dealId: string) =>
    fetchJson<any[]>(`/deals/${dealId}/integration/blockers`),

  reportBlocker: (dealId: string, payload: any) =>
    fetchJson<any>(`/deals/${dealId}/integration/blockers`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  resolveBlocker: (dealId: string, blockerId: string, payload: { resolution_notes: string }) =>
    fetchJson<any>(`/deals/${dealId}/integration/blockers/${blockerId}/resolve`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  getTimeline: (dealId: string) =>
    fetchJson<any>(`/deals/${dealId}/integration/timeline`),

  getCriticalPath: (dealId: string) =>
    fetchJson<any>(`/deals/${dealId}/integration/critical-path`),

  getIntegrationHealth: (dealId: string) =>
    fetchJson<any>(`/deals/${dealId}/integration/health`),

  getExecutiveAttention: (dealId: string) =>
    fetchJson<any>(`/deals/${dealId}/integration/executive-attention`),

  // ==========================================
  // Phase 12: Legal, Contract & Compliance APIs
  // ==========================================
  getLegalOverview: (dealId: string) =>
    fetchJson<any>(`/deals/${dealId}/legal`),

  scanLegalDocuments: (dealId: string) =>
    fetchJson<any>(`/deals/${dealId}/legal/scan`, {
      method: 'POST',
    }),

  getContracts: (dealId: string, contractType?: string) =>
    fetchJson<any[]>(`/deals/${dealId}/legal/contracts${contractType ? `?contract_type=${contractType}` : ''}`),

  createContract: (dealId: string, payload: any) =>
    fetchJson<any>(`/deals/${dealId}/legal/contracts`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getClauses: (dealId: string, category?: string, contractId?: string) => {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (contractId) params.append('contract_id', contractId);
    const qs = params.toString();
    return fetchJson<any[]>(`/deals/${dealId}/legal/clauses${qs ? `?${qs}` : ''}`);
  },

  getLegalFindings: (dealId: string, findingType?: string, severity?: string) => {
    const params = new URLSearchParams();
    if (findingType) params.append('finding_type', findingType);
    if (severity) params.append('severity', severity);
    const qs = params.toString();
    return fetchJson<any[]>(`/deals/${dealId}/legal/findings${qs ? `?${qs}` : ''}`);
  },

  updateLegalFindingStatus: (dealId: string, findingId: string, payload: { status: string; notes?: string }) =>
    fetchJson<any>(`/deals/${dealId}/legal/findings/${findingId}/status`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  getChangeOfControl: (dealId: string) =>
    fetchJson<any>(`/deals/${dealId}/legal/change-of-control`),

  getComplianceMatrix: (dealId: string, framework?: string) =>
    fetchJson<any[]>(`/deals/${dealId}/legal/compliance${framework ? `?framework=${framework}` : ''}`),

  getLegalSummary: (dealId: string) =>
    fetchJson<any>(`/deals/${dealId}/legal/summary`),

  // ==========================================
  // Phase 13: Technology & Operational APIs
  // ==========================================
  getTechnologyOverview: (dealId: string) =>
    fetchJson<any>(`/deals/${dealId}/technology`),

  scanTechnologyDocuments: (dealId: string) =>
    fetchJson<any>(`/deals/${dealId}/technology/scan`, {
      method: 'POST',
    }),

  getTechnologyFindings: (dealId: string, category?: string, severity?: string) => {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (severity) params.append('severity', severity);
    const qs = params.toString();
    return fetchJson<any[]>(`/deals/${dealId}/technology/findings${qs ? `?${qs}` : ''}`);
  },

  createTechnologyFinding: (dealId: string, payload: any) =>
    fetchJson<any>(`/deals/${dealId}/technology/findings`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  updateTechnologyFindingStatus: (dealId: string, findingId: string, payload: { status: string; notes?: string }) =>
    fetchJson<any>(`/deals/${dealId}/technology/findings/${findingId}/status`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  getInfrastructureMetrics: (dealId: string) =>
    fetchJson<any[]>(`/deals/${dealId}/technology/infrastructure`),

  getTechnologyDependencies: (dealId: string, criticality?: string) =>
    fetchJson<any[]>(`/deals/${dealId}/technology/dependencies${criticality ? `?criticality=${criticality}` : ''}`),

  getReliabilityMetrics: (dealId: string) =>
    fetchJson<any[]>(`/deals/${dealId}/technology/reliability`),

  getTechnologySummary: (dealId: string) =>
    fetchJson<any>(`/deals/${dealId}/technology/summary`),

  // ==========================================
  // Phase 14: Streaming RAG Copilot APIs
  // ==========================================
  getCopilotConversations: (dealId: string) =>
    fetchJson<any[]>(`/deals/${dealId}/copilot/conversations`),

  createCopilotConversation: (dealId: string, payload?: { title?: string }) =>
    fetchJson<any>(`/deals/${dealId}/copilot/conversations`, {
      method: 'POST',
      body: JSON.stringify(payload || {}),
    }),

  getCopilotConversation: (dealId: string, conversationId: string) =>
    fetchJson<any>(`/deals/${dealId}/copilot/conversations/${conversationId}`),

  deleteCopilotConversation: (dealId: string, conversationId: string) =>
    fetchJson<any>(`/deals/${dealId}/copilot/conversations/${conversationId}`, {
      method: 'DELETE',
    }),

  queryCopilot: (dealId: string, payload: { conversation_id?: string; message: string }) =>
    fetchJson<any>(`/deals/${dealId}/copilot/query`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  streamCopilot: async (
    dealId: string,
    payload: { conversation_id?: string; message: string },
    callbacks: {
      onDomain?: (domain: string) => void;
      onToken?: (token: string) => void;
      onCitation?: (citation: CopilotCitation) => void;
      onDone?: (data: any) => void;
      onError?: (error: Error) => void;
    }
  ): Promise<void> => {
    const baseUrl = getApiBaseUrl();
    const url = `${baseUrl}/deals/${dealId}/copilot/stream`;

    tokenStore.init();
    const token = tokenStore.getAccessToken();
    const orgId = tokenStore.getOrgId();

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    if (orgId) headers['X-Organization-ID'] = orgId;

    try {
      const res = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
        credentials: 'include',
      });

      if (!res.ok) {
        let errMsg = `Streaming request failed with status ${res.status}`;
        try {
          const json = await res.json();
          if (json.error?.message) {
            errMsg = json.error.message;
          } else if (json.detail) {
            errMsg = typeof json.detail === 'string' ? json.detail : JSON.stringify(json.detail);
          }
        } catch {
          // Fallback to generic message
        }
        throw new ApiError(res.status, 'STREAM_ERROR', errMsg);
      }

      if (!res.body) {
        throw new ApiError(500, 'STREAM_ERROR', 'Streaming response body is null');
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith('data: ')) {
            const dataStr = trimmed.slice(6);
            try {
              const parsed = JSON.parse(dataStr);
              if (parsed.event === 'domain' && callbacks.onDomain) {
                callbacks.onDomain(parsed.data);
              } else if (parsed.event === 'token' && callbacks.onToken) {
                callbacks.onToken(parsed.data);
              } else if (parsed.event === 'citation' && callbacks.onCitation) {
                callbacks.onCitation(parsed.data);
              } else if (parsed.event === 'done' && callbacks.onDone) {
                callbacks.onDone(parsed.data);
              } else if (parsed.event === 'error' && callbacks.onError) {
                callbacks.onError(new Error(typeof parsed.data === 'string' ? parsed.data : JSON.stringify(parsed.data)));
              }
            } catch {
              // Ignore partial JSON parse errors
            }
          }
        }
      }

      if (buffer.trim().startsWith('data: ')) {
        const dataStr = buffer.trim().slice(6);
        try {
          const parsed = JSON.parse(dataStr);
          if (parsed.event === 'done' && callbacks.onDone) {
            callbacks.onDone(parsed.data);
          }
        } catch {
          // Ignore
        }
      }
    } catch (err: any) {
      if (callbacks.onError) {
        callbacks.onError(err instanceof Error ? err : new Error(String(err)));
      } else {
        throw err;
      }
    }
  },

  // Agentic Intelligence Orchestration API
  listAgents: async (): Promise<AgentMetadataItem[]> => {
    return fetchJson<AgentMetadataItem[]>('/agents');
  },

  getAgentMetadata: async (agentId: string): Promise<AgentMetadataItem> => {
    return fetchJson<AgentMetadataItem>(`/agents/${agentId}`);
  },

  orchestrateAgents: async (
    dealId: string,
    payload: { orchestration_mode?: string; query?: string; target_agent_ids?: string[] }
  ): Promise<AgentOrchestrationResultItem> => {
    return fetchJson<AgentOrchestrationResultItem>(`/deals/${dealId}/agents/orchestrate`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  runStandaloneAgent: async (
    dealId: string,
    agentId: string,
    payload?: { query?: string }
  ): Promise<AgentAssessmentItem> => {
    return fetchJson<AgentAssessmentItem>(`/deals/${dealId}/agents/${agentId}/run`, {
      method: 'POST',
      body: JSON.stringify(payload || {}),
    });
  },

  listAgentExecutions: async (dealId: string): Promise<any[]> => {
    return fetchJson<any[]>(`/deals/${dealId}/agents/executions`);
  },

  getAgentExecutionDetails: async (dealId: string, executionId: string): Promise<any> => {
    return fetchJson<any>(`/deals/${dealId}/agents/executions/${executionId}`);
  },

  // Machine Learning Foundation & XAI Catalog
  listMLModels: async (): Promise<MLModelItem[]> => {
    return fetchJson<MLModelItem[]>('/ml/models');
  },

  getMLModel: async (modelId: string): Promise<MLModelItem> => {
    return fetchJson<MLModelItem>(`/ml/models/${modelId}`);
  },

  getModelMetrics: async (modelId: string): Promise<any> => {
    return fetchJson<any>(`/ml/models/${modelId}/metrics`);
  },

  listTrainingRuns: async (): Promise<any[]> => {
    return fetchJson<any[]>('/ml/training-runs');
  },

  getPredictionRecord: async (predictionId: string): Promise<any> => {
    return fetchJson<any>(`/ml/predictions/${predictionId}`);
  },

  predictDealML: async (
    dealId: string,
    payload: { model_id: string; features_override?: Record<string, any> }
  ): Promise<PredictionResultItem> => {
    return fetchJson<PredictionResultItem>(`/deals/${dealId}/ml/predict`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};

export interface AgentMetadataItem {
  agent_id: string;
  name: string;
  version: string;
  purpose: string;
  domain: string;
  lifecycle_phase: string;
  allowed_tools: string[];
  evidence_requirements: string[];
  confidence_policy: string;
}

export interface AgentAssessmentItem {
  agent_id: string;
  domain: string;
  status: string;
  summary: string;
  confidence: string;
  confidence_score: number;
  key_findings: any[];
  positive_drivers?: string[];
  negative_drivers?: string[];
  citations: CopilotCitation[];
  tools_invoked: string[];
  execution_time_ms: number;
  deterministic_references?: Record<string, any>;
  [key: string]: any;
}

export interface DecisionAssessmentItem {
  recommendation: 'BUY' | 'BUY_WITH_CONDITIONS' | 'RENEGOTIATE' | 'HOLD' | 'AVOID' | 'INSUFFICIENT_EVIDENCE';
  confidence: string;
  confidence_score: number;
  deterministic_decision_score: number | null;
  positive_drivers: string[];
  negative_drivers: string[];
  unresolved_issues: string[];
  required_diligence_items: string[];
  executive_rationale: string;
  citations: CopilotCitation[];
  human_review_required: boolean;
  escalation_reasons: string[];
  recommended_human_action: string | null;
}

export interface AgentOrchestrationResultItem {
  execution_id: string;
  deal_id: string;
  orchestration_mode: string;
  selected_agents: string[];
  specialist_assessments: Record<string, AgentAssessmentItem>;
  decision_assessment: DecisionAssessmentItem;
  total_duration_ms: number;
}

export interface MLModelItem {
  model_id: string;
  name: string;
  version: string;
  task_type: string;
  framework: string;
  training_dataset_id?: string;
  feature_names: string[];
  hyperparameters: Record<string, any>;
  evaluation_metrics: Record<string, number>;
  status: string;
}

export interface FeatureImportanceItem {
  feature_name: string;
  importance_score: number;
  rank: number;
  direction: string;
}

export interface SHAPValueItem {
  feature_name: string;
  base_value: number;
  shap_value: number;
  actual_value: any;
}

export interface XAIExplanationItem {
  explanation_id: string;
  prediction_id: string;
  model_id: string;
  method: string;
  top_features: FeatureImportanceItem[];
  shap_values?: SHAPValueItem[];
  feature_snapshot: Record<string, any>;
  narrative_summary: string;
  generated_at: string;
}

export interface PredictionResultItem {
  prediction_id: string;
  model_id: string;
  model_version: string;
  task_type: string;
  predicted_value: any;
  probability_distribution?: Record<string, number>;
  confidence_interval?: [number, number];
  prediction_confidence: number;
  explanation?: XAIExplanationItem;
  created_at: string;
}



