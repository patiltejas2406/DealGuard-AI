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


export interface ValuationItem {
  id: string;
  deal_id: string;
  title: string;
  status: 'DRAFT' | 'ACTIVE' | 'FINAL' | 'ARCHIVED';
  selected_method: 'DCF' | 'CCA' | 'PRECEDENT' | 'MULTI_METHOD';
  currency: string;
  proposed_ev?: number | null;
  proposed_equity_value?: number | null;
  notes?: string;
  created_at: string;
}

export interface ValuationAssumptionItem {
  id: string;
  deal_id: string;
  valuation_id?: string;
  name: string;
  category: string;
  value: number;
  unit: string;
  period?: string;
  source_type: 'DOCUMENT' | 'FINANCIAL_MODEL' | 'MARKET_DATA' | 'ANALYST_INPUT' | 'DERIVED';
  is_analyst_entered: boolean;
  confidence_score?: number;
  citation_id?: string;
  notes?: string;
}

export interface WaccAnalysisItem {
  wacc: number | null;
  cost_of_equity: number | null;
  after_tax_cost_of_debt: number | null;
  equity_weight: number | null;
  debt_weight: number | null;
  formula?: string;
  is_calculable: boolean;
  components?: Record<string, any>;
}

export interface DcfSchedulePeriod {
  period: string;
  year_index: number;
  revenue?: number | null;
  revenue_growth?: number | null;
  ebitda?: number | null;
  ebitda_margin?: number | null;
  ebit?: number | null;
  tax_rate?: number | null;
  nopat?: number | null;
  depreciation_amortization?: number | null;
  capex?: number | null;
  working_capital_change?: number | null;
  ufcf?: number | null;
  discount_factor?: number | null;
  pv_ufcf?: number | null;
}

export interface DcfValuationItem {
  valuation_id: string;
  deal_id: string;
  dcf: {
    terminal_method: string;
    wacc_pct: number;
    terminal_growth_rate_pct?: number | null;
    exit_multiple?: number | null;
    pv_forecast_fcf: number;
    terminal_value: number;
    pv_terminal_value: number;
    terminal_value_formula?: string;
    implied_enterprise_value: number;
    implied_equity_value: number;
    schedule: DcfSchedulePeriod[];
    bridge: {
      enterprise_value: number;
      cash_and_equivalents: number;
      total_debt: number;
      net_debt: number;
      minority_interest: number;
      preferred_equity: number;
      equity_value: number;
    };
  };
}

export interface ComparableCompanyItem {
  id: string;
  deal_id: string;
  valuation_id?: string;
  company_name: string;
  ticker?: string;
  industry?: string;
  geography?: string;
  revenue?: number | null;
  ebitda?: number | null;
  ebit?: number | null;
  net_income?: number | null;
  enterprise_value?: number | null;
  equity_value?: number | null;
  ev_to_revenue?: number | null;
  ev_to_ebitda?: number | null;
  pe_ratio?: number | null;
  revenue_growth?: number | null;
  status: 'INCLUDED' | 'EXCLUDED' | 'REVIEW';
  source: string;
  notes?: string;
  citation_id?: string;
}

export interface MultipleStatistics {
  count: number;
  min: number | null;
  percentile_25: number | null;
  median: number | null;
  mean: number | null;
  percentile_75: number | null;
  max: number | null;
}

export interface ComparableAnalysisItem {
  valuation_id: string;
  deal_id: string;
  companies: ComparableCompanyItem[];
  statistics: {
    total_companies: number;
    included_companies: number;
    ev_to_revenue_stats: MultipleStatistics;
    ev_to_ebitda_stats: MultipleStatistics;
    pe_ratio_stats: MultipleStatistics;
  };
  implied_valuation_revenue: Record<string, any>;
  implied_valuation_ebitda: Record<string, any>;
}

export interface PrecedentTransactionItem {
  id: string;
  deal_id: string;
  valuation_id?: string;
  target_name: string;
  acquirer_name?: string;
  announcement_date?: string;
  transaction_value?: number | null;
  enterprise_value?: number | null;
  revenue?: number | null;
  ebitda?: number | null;
  ev_to_revenue?: number | null;
  ev_to_ebitda?: number | null;
  transaction_type: string;
  industry?: string;
  geography?: string;
  status: 'INCLUDED' | 'EXCLUDED' | 'REVIEW';
  source: string;
  notes?: string;
  citation_id?: string;
}

export interface PrecedentAnalysisItem {
  valuation_id: string;
  deal_id: string;
  transactions: PrecedentTransactionItem[];
  statistics: {
    total_transactions: number;
    included_transactions: number;
    ev_to_revenue_stats: MultipleStatistics;
    ev_to_ebitda_stats: MultipleStatistics;
  };
  implied_valuation_revenue: Record<string, any>;
  implied_valuation_ebitda: Record<string, any>;
}

export interface SensitivityMatrixItem {
  type: string;
  row_variable: string;
  column_variable: string;
  row_values: number[];
  column_values: number[];
  base_row_index: number;
  base_column_index: number;
  enterprise_value_matrix: (number | null)[][];
  equity_value_matrix: (number | null)[][];
}

export interface MethodologyRangeItem {
  methodology: string;
  label: string;
  ev_low: number | null;
  ev_base: number | null;
  ev_high: number | null;
  equity_low: number | null;
  equity_base: number | null;
  equity_high: number | null;
}

export interface ValuationSummaryItem {
  valuation_id: string;
  deal_id: string;
  currency: string;
  proposed_ev?: number | null;
  proposed_equity_value?: number | null;
  methodologies: MethodologyRangeItem[];
  transaction_comparison?: Record<string, any>;
}

export interface ValuationValidationItem {
  deal_id: string;
  status: 'HEALTHY' | 'DISCREPANCIES_FOUND';
  checks: {
    check_name: string;
    passed: boolean;
    severity: string;
    message: string;
  }[];
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
