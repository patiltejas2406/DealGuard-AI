/**
 * Core Type Definitions for DealGuard AI Frontend
 */

export type DealStage =
  | 'SOURCING'
  | 'PRE_DILIGENCE'
  | 'CONFIRMATORY_DILIGENCE'
  | 'IC_REVIEW'
  | 'NEGOTIATION'
  | 'CLOSED'
  | 'VALUE_CREATION';

export type RiskSeverity = 1 | 2 | 3 | 4 | 5;
export type RiskLikelihood = 1 | 2 | 3 | 4 | 5;

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_superuser: boolean;
}

export interface OrganizationBrief {
  id: string;
  name: string;
  slug: string;
  role?: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
  organization: OrganizationBrief;
  role: string;
  permissions: string[];
}

export interface CurrentUserProfile {
  user: User;
  organization: OrganizationBrief;
  role: string;
  permissions: string[];
  accessible_organizations: OrganizationBrief[];
}

export interface Deal {
  id: string;
  organization_id: string;
  target_company_id: string;
  title: string;
  code_name?: string;
  deal_type: string;
  stage: DealStage;
  status: string;
  target_ev?: number;
  currency: string;
  decision_score?: number;
  created_at: string;
}

export interface DocumentItem {
  id: string;
  deal_id: string;
  name: string;
  file_type: string;
  mime_type: string;
  size_bytes: number;
  sha256_hash: string;
  status: 'UPLOADED' | 'QUEUED' | 'PROCESSING' | 'INDEXED' | 'FAILED';
  doc_category?: string;
  created_at: string;
}

export interface DocumentChunkItem {
  id: string;
  document_id: string;
  chunk_index: number;
  page_number: number;
  section_title?: string;

  content: string;
  token_count?: number;
  embedding_model: string;
  metadata_json?: Record<string, any>;
}

export interface JobExecutionItem {
  id: string;
  organization_id: string;
  deal_id?: string;
  job_type: string;
  status: 'QUEUED' | 'EXTRACTING' | 'CHUNKING' | 'EMBEDDING' | 'INDEXING' | 'COMPLETED' | 'FAILED';
  progress_pct: number;
  error_message?: string;
  result_metadata?: Record<string, any>;
  started_at?: string;
  completed_at?: string;
}

export interface SemanticSearchResult {
  chunk_id: string;
  document_id: string;
  document_name: string;
  page_number: number;
  section_title?: string;
  content: string;
  similarity_score: number;
  metadata?: Record<string, any>;
}


export interface Citation {
  id: string;
  documentId: string;
  documentName: string;
  pageNumber: number;
  section?: string;
  exactQuote: string;
  confidenceScore: number;
}

export interface RiskItem {
  id: string;
  category: string;
  title: string;
  severity: RiskSeverity;
  likelihood: RiskLikelihood;
  score: number;
  status: 'IDENTIFIED' | 'REVIEWED' | 'MITIGATED' | 'ACCEPTED';
  citation?: Citation;
  mitigationStrategy?: string;
}

export interface FinancialStatementItem {
  id: string;
  deal_id: string;
  statement_type: 'INCOME_STATEMENT' | 'BALANCE_SHEET' | 'CASH_FLOW';
  period_type: string;
  fiscal_year: number;
  fiscal_period: string;
  source_currency: string;
  is_audited: boolean;
  is_normalized: boolean;
  source_document_id?: string;
  line_items: Record<string, any>;
  created_at: string;
}

export interface FinancialMetricItem {
  id: string;
  deal_id: string;
  metric_name: string;
  period: string;
  value: number;
  unit: string;
  source_currency: string;
  is_normalized: boolean;
  calculation_formula?: string;
  citation_id?: string;
}

export interface QoEAdjustmentItem {
  id: string;
  deal_id: string;
  category: string;
  description: string;
  amount: number;
  currency: string;
  period: string;
  treatment: 'ADD_BACK' | 'DEDUCTION';
  status: 'PROPOSED' | 'APPROVED' | 'REJECTED';
  notes?: string;
  citation_id?: string;
  created_at: string;
}

export interface QoEBridgeItem {
  deal_id: string;
  period: string;
  bridge: {
    reported_ebitda: number | null;
    total_add_backs: number;
    total_deductions: number;
    net_adjustment: number;
    adjusted_ebitda: number | null;
    adjustment_count: number;
    applied_adjustments_count: number;
    category_breakdown: Record<string, number>;
  };
  adjustments: QoEAdjustmentItem[];
}

export interface FinancialValidationCheck {
  statement_type: string;
  period: string;
  check_name: string;
  passed: boolean;
  severity: string;
  message: string;
}


export interface FinancialValidationItem {
  deal_id: string;
  status: 'HEALTHY' | 'DISCREPANCIES_FOUND';
  total_statements_checked: number;
  checks: FinancialValidationCheck[];
}

export interface CagrAnalysisItem {
  start_period?: string;
  end_period?: string;
  years?: number;
  revenue_start?: number;
  revenue_end?: number;
  revenue_cagr?: number;
  ebitda_start?: number;
  ebitda_end?: number;
  ebitda_cagr?: number;
  message?: string;
}


export interface ValuationSummary {
  method: 'DCF' | 'CCA' | 'PRECEDENT';
  impliedEvBase: number;
  impliedEvLow: number;
  impliedEvHigh: number;
  wacc?: number;
  terminalGrowthRate?: number;
  exitMultiple?: number;
}

export interface SystemHealth {
  status: string;
  service: string;
  version: string;
  environment: string;
  timestamp: string;
  dependencies?: {
    database: string;
    storage_provider: string;
    embedding_provider: string;
  };
}

export interface SystemInfo {
  platform: string;
  version: string;
  environment: string;
  architecture: {
    type: string;
    deterministic_financial_engine: boolean;
    evidence_grounding_enforced: boolean;
    prompt_injection_defense: boolean;
  };
  ai_spec: {
    embedding_provider: string;
    embedding_model: string;
    embedding_dimension: number;
    vector_store: string;
  };
  background_jobs: {
    engine: string;
    states_supported: string[];
  };
  security: {
    password_hasher: string;
    session_type: string;
    tenant_isolation: string;
  };
}
