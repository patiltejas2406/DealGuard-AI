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

export interface FinancialMetric {
  metricName: string;
  period: string;
  value: number;
  unit: string;
  sourceCurrency: string;
  isNormalized: boolean;
  citation?: Citation;
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
