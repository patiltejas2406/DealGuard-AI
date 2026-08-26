'use client';

/**
 * DealGuard AI — Phase 12: Legal, Contract & Compliance Diligence Intelligence Console
 */

import React, { useEffect, useState } from 'react';
import {
  Scale,
  FileText,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Plus,
  RefreshCw,
  TrendingUp,
  Shield,
  Building2,
  Clock,
  ArrowRight,
  GitBranch,
  Filter,
  Check,
  AlertCircle,
  Flame,
  Search,
  Eye,
  FileCheck2,
  DollarSign,
  Sparkles,
  Link as LinkIcon,
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { api } from '@/lib/api';
import {
  ChangeOfControlConsoleResponse,
  ChangeOfControlItem,
  ComplianceRequirementResponse,
  ContractClauseResponse,
  ContractRecordResponse,
  Deal,
  LegalFindingResponse,
  LegalSummaryResponse,
} from '@/types';

type ActiveTab = 'CHANGE_OF_CONTROL' | 'CONTRACTS' | 'CLAUSES' | 'FINDINGS' | 'COMPLIANCE';

const CATEGORIES = [
  'ALL',
  'CHANGE_OF_CONTROL',
  'ASSIGNMENT_RESTRICTION',
  'TERMINATION_RIGHT',
  'CONSENT_REQUIREMENT',
  'NON_COMPETE',
  'NON_SOLICITATION',
  'IP_OWNERSHIP',
  'IP_ASSIGNMENT',
  'LICENSE_RESTRICTION',
  'EXCLUSIVITY',
  'AUTO_RENEWAL',
  'TERMINATION_NOTICE',
  'LIABILITY_CAP',
  'INDEMNIFICATION',
  'WARRANTY',
  'DATA_PRIVACY',
  'DATA_PROCESSING',
  'REGULATORY_OBLIGATION',
  'COMPLIANCE_OBLIGATION',
  'PRICE_ESCALATION',
  'MOST_FAVORED_CUSTOMER',
];

export default function LegalIntelligencePage() {
  // Deal & Tab State
  const [deals, setDeals] = useState<Deal[]>([]);
  const [selectedDealId, setSelectedDealId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<ActiveTab>('CHANGE_OF_CONTROL');

  // Legal Data State
  const [summary, setSummary] = useState<LegalSummaryResponse | null>(null);
  const [cocData, setCocData] = useState<ChangeOfControlConsoleResponse | null>(null);
  const [contracts, setContracts] = useState<ContractRecordResponse[]>([]);
  const [clauses, setClauses] = useState<ContractClauseResponse[]>([]);
  const [findings, setFindings] = useState<LegalFindingResponse[]>([]);
  const [complianceItems, setComplianceItems] = useState<ComplianceRequirementResponse[]>([]);

  // Filter State
  const [clauseCategoryFilter, setClauseCategoryFilter] = useState<string>('ALL');
  const [contractTypeFilter, setContractTypeFilter] = useState<string>('ALL');

  // Modals & Drawers State
  const [isRegisterContractOpen, setIsRegisterContractOpen] = useState<boolean>(false);
  const [isEvidenceDrawerOpen, setIsEvidenceDrawerOpen] = useState<boolean>(false);
  const [selectedClauseForEvidence, setSelectedClauseForEvidence] = useState<ContractClauseResponse | null>(null);

  // Form State: Register Contract
  const [cTitle, setCTitle] = useState<string>('');
  const [cType, setCType] = useState<string>('CUSTOMER_MSA');
  const [cCounterparty, setCCounterparty] = useState<string>('');
  const [cAnnualValue, setCAnnualValue] = useState<number>(1000000);
  const [cGoverningLaw, setCGoverningLaw] = useState<string>('Delaware');

  // Feedback State
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // 1. Load Deals on Mount
  useEffect(() => {
    async function loadDeals() {
      try {
        const dealList = await api.getDeals();
        setDeals(dealList);
        if (dealList.length > 0 && !selectedDealId) {
          setSelectedDealId(dealList[0].id);
        }
      } catch (err: any) {
        console.error('Failed to load deals:', err);
      }
    }
    loadDeals();
  }, []);

  // 2. Load Legal Data whenever deal changes
  useEffect(() => {
    if (!selectedDealId) return;
    loadAllLegalData(selectedDealId);
  }, [selectedDealId]);

  async function loadAllLegalData(dealId: string) {
    setIsLoading(true);
    setError(null);
    try {
      const [sumRes, cocRes, cList, clList, fList, compList] = await Promise.all([
        api.getLegalSummary(dealId),
        api.getChangeOfControl(dealId),
        api.getContracts(dealId),
        api.getClauses(dealId),
        api.getLegalFindings(dealId),
        api.getComplianceMatrix(dealId),
      ]);
      setSummary(sumRes);
      setCocData(cocRes);
      setContracts(cList);
      setClauses(clList);
      setFindings(fList);
      setComplianceItems(compList);
    } catch (err: any) {
      setError(err?.message || 'Failed to load legal diligence data.');
    } finally {
      setIsLoading(false);
    }
  }

  // 3. Trigger Legal Scan
  async function handleTriggerScan() {
    if (!selectedDealId) return;
    setIsScanning(true);
    setError(null);
    try {
      const res = await api.scanLegalDocuments(selectedDealId);
      setSuccessMessage(res.message);
      loadAllLegalData(selectedDealId);
    } catch (err: any) {
      setError(err?.message || 'Legal document scan failed.');
    } finally {
      setIsScanning(false);
    }
  }

  // 4. Register Contract
  async function handleRegisterContract(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedDealId || !cTitle || !cCounterparty) return;
    try {
      await api.createContract(selectedDealId, {
        title: cTitle,
        contract_type: cType,
        counterparty: cCounterparty,
        annual_value: cAnnualValue,
        governing_law: cGoverningLaw,
      });
      setSuccessMessage(`Contract '${cTitle}' registered.`);
      setIsRegisterContractOpen(false);
      setCTitle('');
      setCCounterparty('');
      loadAllLegalData(selectedDealId);
    } catch (err: any) {
      setError(err?.message || 'Failed to register contract.');
    }
  }

  // 5. Update Finding Status
  async function handleUpdateFindingStatus(findingId: string, newStatus: string) {
    if (!selectedDealId) return;
    try {
      await api.updateLegalFindingStatus(selectedDealId, findingId, {
        status: newStatus,
        notes: 'Status updated via Legal Intelligence Console',
      });
      setSuccessMessage('Finding status updated.');
      loadAllLegalData(selectedDealId);
    } catch (err: any) {
      setError(err?.message || 'Failed to update finding status.');
    }
  }

  const formatCurrency = (amount: number) => {
    if (amount >= 1000000) {
      return `$${(amount / 1000000).toFixed(1)}M`;
    }
    if (amount >= 1000) {
      return `$${(amount / 1000).toFixed(0)}K`;
    }
    return `$${amount.toLocaleString()}`;
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return <Badge variant="danger" size="sm">CRITICAL</Badge>;
      case 'HIGH':
        return <Badge variant="warning" size="sm">HIGH</Badge>;
      case 'MEDIUM':
        return <Badge variant="info" size="sm">MEDIUM</Badge>;
      default:
        return <Badge variant="default" size="sm">LOW</Badge>;
    }
  };

  const filteredClauses = clauses.filter((c) =>
    clauseCategoryFilter === 'ALL' ? true : c.category === clauseCategoryFilter
  );

  const filteredContracts = contracts.filter((c) =>
    contractTypeFilter === 'ALL' ? true : c.contract_type === contractTypeFilter
  );

  return (
    <div className="min-h-screen bg-surface-base text-slate-100 p-6 space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 border-b border-slate-800 pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <Scale className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2 font-mono">
                Legal & Contract Intelligence Engine
                <Badge variant="success" size="sm">Phase 12 v1.0</Badge>
              </h1>
              <p className="text-xs text-slate-400">
                Grounded 32-Category Contract Parsing, Change-of-Control Consents, Revenue at Risk & Compliance Matrix
              </p>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs font-mono">
            <Building2 className="w-4 h-4 text-emerald-400" />
            <select
              value={selectedDealId || ''}
              onChange={(e) => setSelectedDealId(e.target.value)}
              className="bg-transparent text-slate-200 focus:outline-none cursor-pointer"
            >
              {deals.map((d) => (
                <option key={d.id} value={d.id} className="bg-slate-900 text-slate-200">
                  {d.title} ({d.currency})
                </option>
              ))}
            </select>
          </div>

          <button
            type="button"
            onClick={handleTriggerScan}
            disabled={isScanning}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow font-mono transition-colors"
          >
            <Sparkles className={`w-3.5 h-3.5 ${isScanning ? 'animate-spin' : ''}`} />
            {isScanning ? 'Scanning Data Room...' : 'Run Legal Diligence Scan'}
          </button>

          <button
            type="button"
            onClick={() => setIsRegisterContractOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold border border-slate-700 font-mono transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            Register Contract
          </button>

          <button
            type="button"
            onClick={() => selectedDealId && loadAllLegalData(selectedDealId)}
            className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Summary Scorecard Grid */}
      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3 font-mono">
          <Card className="p-3.5 bg-slate-900/90 border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-500 uppercase">Revenue at Risk</span>
            <p className="text-xl font-bold text-rose-400">{formatCurrency(summary.revenue_at_risk)}</p>
            <span className="text-[10px] text-slate-400">{summary.revenue_at_risk_pct}% of Contract Base</span>
          </Card>

          <Card className="p-3.5 bg-slate-900/90 border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-500 uppercase">Change of Control</span>
            <p className="text-xl font-bold text-amber-400">{summary.change_of_control_contracts_count} Contracts</p>
            <span className="text-[10px] text-slate-400">{summary.consents_required_count} Consents Required</span>
          </Card>

          <Card className="p-3.5 bg-slate-900/90 border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-500 uppercase">Contracts Reviewed</span>
            <p className="text-xl font-bold text-white">{summary.total_contracts_reviewed}</p>
            <span className="text-[10px] text-slate-400">{formatCurrency(summary.total_annual_contract_value)} Base Value</span>
          </Card>

          <Card className="p-3.5 bg-slate-900/90 border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-500 uppercase">Clauses Extracted</span>
            <p className="text-xl font-bold text-blue-400">{summary.total_clauses_extracted}</p>
            <span className="text-[10px] text-slate-400">32-Pillar Taxonomy</span>
          </Card>

          <Card className="p-3.5 bg-slate-900/90 border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-500 uppercase">Legal Findings</span>
            <p className="text-xl font-bold text-white">{summary.total_findings_count}</p>
            <span className="text-[10px] text-rose-400 font-bold">{summary.critical_findings_count} Critical / {summary.high_findings_count} High</span>
          </Card>

          <Card className="p-3.5 bg-slate-900/90 border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-500 uppercase">Compliance Posture</span>
            <p className="text-xl font-bold text-emerald-400">{summary.compliance_evidence_present} Verified</p>
            <span className="text-[10px] text-amber-400 font-bold">{summary.compliance_potential_gaps} Potential Gaps</span>
          </Card>
        </div>
      )}

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2 text-xs font-mono">
        <button
          onClick={() => setActiveTab('CHANGE_OF_CONTROL')}
          className={`px-3.5 py-1.5 rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === 'CHANGE_OF_CONTROL'
              ? 'bg-emerald-600 text-white font-bold shadow'
              : 'text-slate-400 hover:text-white hover:bg-slate-900'
          }`}
        >
          <Flame className="w-3.5 h-3.5 text-amber-400" />
          Change of Control Console ({cocData?.total_change_of_control_contracts || 0})
        </button>
        <button
          onClick={() => setActiveTab('CONTRACTS')}
          className={`px-3.5 py-1.5 rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === 'CONTRACTS'
              ? 'bg-emerald-600 text-white font-bold shadow'
              : 'text-slate-400 hover:text-white hover:bg-slate-900'
          }`}
        >
          <FileText className="w-3.5 h-3.5" />
          Contract Register ({contracts.length})
        </button>
        <button
          onClick={() => setActiveTab('CLAUSES')}
          className={`px-3.5 py-1.5 rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === 'CLAUSES'
              ? 'bg-emerald-600 text-white font-bold shadow'
              : 'text-slate-400 hover:text-white hover:bg-slate-900'
          }`}
        >
          <Scale className="w-3.5 h-3.5" />
          Clause Intelligence ({clauses.length})
        </button>
        <button
          onClick={() => setActiveTab('FINDINGS')}
          className={`px-3.5 py-1.5 rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === 'FINDINGS'
              ? 'bg-emerald-600 text-white font-bold shadow'
              : 'text-slate-400 hover:text-white hover:bg-slate-900'
          }`}
        >
          <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
          Legal Findings ({findings.length})
        </button>
        <button
          onClick={() => setActiveTab('COMPLIANCE')}
          className={`px-3.5 py-1.5 rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === 'COMPLIANCE'
              ? 'bg-emerald-600 text-white font-bold shadow'
              : 'text-slate-400 hover:text-white hover:bg-slate-900'
          }`}
        >
          <Shield className="w-3.5 h-3.5 text-blue-400" />
          Compliance Evidence Matrix ({complianceItems.length})
        </button>
      </div>

      {/* Notifications */}
      {successMessage && (
        <div className="p-3 rounded-lg bg-emerald-950/50 border border-emerald-800/80 text-emerald-300 text-xs flex items-center justify-between font-mono animate-fadeIn">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>{successMessage}</span>
          </div>
          <button onClick={() => setSuccessMessage(null)} className="text-slate-400 hover:text-white">
            <XCircle className="w-4 h-4" />
          </button>
        </div>
      )}

      {error && (
        <div className="p-3 rounded-lg bg-rose-950/50 border border-rose-800/80 text-rose-300 text-xs flex items-center justify-between font-mono">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-400" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-slate-400 hover:text-white">
            <XCircle className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* TAB 1: CHANGE OF CONTROL CONSOLE */}
      {activeTab === 'CHANGE_OF_CONTROL' && cocData && (
        <Card className="p-5 bg-slate-900/90 border-slate-800 space-y-4 font-mono">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h2 className="text-sm font-semibold text-white flex items-center gap-2">
                <Flame className="w-4 h-4 text-amber-400" />
                Change-of-Control & Consent Action Register
              </h2>
              <p className="text-xs text-slate-400">
                Contracts triggered by acquisition requiring counterparty consent, written notification, or carrying termination risk.
              </p>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-right">
              <span className="text-slate-500 text-[10px] uppercase block">Total Exposed Revenue</span>
              <span className="text-rose-400 font-bold text-sm">{formatCurrency(cocData.total_revenue_exposed)}</span>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-[10px] uppercase text-slate-500 border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">Contract Agreement</th>
                  <th className="py-2.5 px-3">Counterparty</th>
                  <th className="py-2.5 px-3">Annual Value</th>
                  <th className="py-2.5 px-3">Consent Required?</th>
                  <th className="py-2.5 px-3">Notice Window</th>
                  <th className="py-2.5 px-3">Severity</th>
                  <th className="py-2.5 px-3">Action Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40">
                {cocData.contracts.map((c, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/30">
                    <td className="py-3 px-3">
                      <div className="font-bold text-white">{c.contract_title}</div>
                      <div className="text-[10px] text-slate-500">{c.clause_summary}</div>
                    </td>
                    <td className="py-3 px-3 text-slate-300 font-bold">{c.counterparty}</td>
                    <td className="py-3 px-3 font-bold text-rose-400">{formatCurrency(c.annual_value)}</td>
                    <td className="py-3 px-3">
                      {c.requires_consent ? (
                        <Badge variant="danger" size="sm">CONSENT REQUIRED</Badge>
                      ) : (
                        <Badge variant="warning" size="sm">NOTICE ONLY</Badge>
                      )}
                    </td>
                    <td className="py-3 px-3 text-slate-400">
                      {c.notice_period_days ? `${c.notice_period_days} Days Pre-Close` : 'Prompt Notice'}
                    </td>
                    <td className="py-3 px-3">{getSeverityBadge(c.severity)}</td>
                    <td className="py-3 px-3 font-bold text-amber-400">{c.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* TAB 2: CONTRACT REGISTER */}
      {activeTab === 'CONTRACTS' && (
        <Card className="p-5 bg-slate-900/90 border-slate-800 space-y-4 font-mono">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
            <span className="text-xs font-bold text-white">Contract Register ({filteredContracts.length})</span>
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-400">Filter Type:</span>
              <select
                value={contractTypeFilter}
                onChange={(e) => setContractTypeFilter(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-slate-200 focus:outline-none cursor-pointer"
              >
                <option value="ALL">ALL (Contract Types)</option>
                <option value="CUSTOMER_MSA">CUSTOMER_MSA</option>
                <option value="VENDOR_SAAS">VENDOR_SAAS</option>
                <option value="EMPLOYMENT">EMPLOYMENT</option>
                <option value="IP_ASSIGNMENT">IP_ASSIGNMENT</option>
                <option value="PARTNERSHIP">PARTNERSHIP</option>
              </select>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-[10px] uppercase text-slate-500 border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">Title / Document</th>
                  <th className="py-2.5 px-3">Type</th>
                  <th className="py-2.5 px-3">Counterparty</th>
                  <th className="py-2.5 px-3">Annual Value</th>
                  <th className="py-2.5 px-3">Governing Law</th>
                  <th className="py-2.5 px-3">Change of Control?</th>
                  <th className="py-2.5 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40">
                {filteredContracts.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-800/30">
                    <td className="py-3 px-3 font-bold text-white">{c.title}</td>
                    <td className="py-3 px-3 text-slate-400">{c.contract_type}</td>
                    <td className="py-3 px-3 text-slate-300 font-bold">{c.counterparty}</td>
                    <td className="py-3 px-3 font-bold text-white">{formatCurrency(c.annual_value)}</td>
                    <td className="py-3 px-3 text-slate-400">{c.governing_law || 'N/A'}</td>
                    <td className="py-3 px-3">
                      {c.has_change_of_control ? (
                        <Badge variant="warning" size="sm">YES (Triggered)</Badge>
                      ) : (
                        <span className="text-[10px] text-slate-500">Standard</span>
                      )}
                    </td>
                    <td className="py-3 px-3">
                      <Badge variant="success" size="sm">{c.status}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* TAB 3: CLAUSE INTELLIGENCE */}
      {activeTab === 'CLAUSES' && (
        <Card className="p-5 bg-slate-900/90 border-slate-800 space-y-4 font-mono">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-400">Filter Category:</span>
              <select
                value={clauseCategoryFilter}
                onChange={(e) => setClauseCategoryFilter(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-slate-200 focus:outline-none cursor-pointer"
              >
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <span className="text-xs text-slate-400">
              Showing {filteredClauses.length} of {clauses.length} Clauses
            </span>
          </div>

          <div className="space-y-3">
            {filteredClauses.map((cl) => (
              <div key={cl.id} className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-white">{cl.clause_title}</span>
                    <Badge variant="default" size="sm">{cl.category}</Badge>
                    {getSeverityBadge(cl.severity)}
                  </div>
                  <button
                    onClick={() => {
                      setSelectedClauseForEvidence(cl);
                      setIsEvidenceDrawerOpen(true);
                    }}
                    className="flex items-center gap-1 text-[10px] text-emerald-400 hover:text-emerald-300 font-bold"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    Verify Citation
                  </button>
                </div>
                <p className="text-xs text-slate-300 font-mono bg-slate-900/80 p-2.5 rounded border border-slate-800/80">
                  &ldquo;{cl.clause_text}&rdquo;
                </p>
                <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1">
                  <span>Section: {cl.section_reference || 'General'} • Page {cl.page_number || 1}</span>
                  <span className="text-emerald-400">Confidence: {cl.confidence}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* TAB 4: LEGAL FINDINGS */}
      {activeTab === 'FINDINGS' && (
        <Card className="p-5 bg-slate-900/90 border-slate-800 space-y-4 font-mono">
          <div className="border-b border-slate-800 pb-3">
            <span className="text-xs font-bold text-white">Actionable Legal & Regulatory Findings ({findings.length})</span>
          </div>

          <div className="space-y-3">
            {findings.map((f) => (
              <div key={f.id} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-white">{f.title}</span>
                      {getSeverityBadge(f.severity)}
                    </div>
                    <div className="text-[10px] text-slate-400 mt-0.5">{f.description}</div>
                  </div>
                  <select
                    value={f.status}
                    onChange={(e) => handleUpdateFindingStatus(f.id, e.target.value)}
                    className="bg-slate-900 border border-slate-800 rounded px-2 py-1 text-[10px] text-slate-200 focus:outline-none cursor-pointer"
                  >
                    <option value="IDENTIFIED">IDENTIFIED</option>
                    <option value="REQUIRES_REVIEW">REQUIRES_REVIEW</option>
                    <option value="ACTION_PLANNED">ACTION_PLANNED</option>
                    <option value="CONSENT_OBTAINED">CONSENT_OBTAINED</option>
                    <option value="MITIGATED">MITIGATED</option>
                    <option value="ACCEPTED">ACCEPTED</option>
                  </select>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  <div className="p-2.5 rounded bg-slate-900/70 border border-slate-800/80 space-y-1">
                    <span className="text-[10px] text-slate-500 uppercase font-bold">Business Impact</span>
                    <p className="text-slate-300 text-xs">{f.business_impact}</p>
                  </div>
                  <div className="p-2.5 rounded bg-slate-900/70 border border-slate-800/80 space-y-1">
                    <span className="text-[10px] text-emerald-400 uppercase font-bold">Recommendation</span>
                    <p className="text-slate-300 text-xs">{f.recommendation}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* TAB 5: COMPLIANCE MATRIX */}
      {activeTab === 'COMPLIANCE' && (
        <Card className="p-5 bg-slate-900/90 border-slate-800 space-y-4 font-mono">
          <div className="border-b border-slate-800 pb-3">
            <span className="text-xs font-bold text-white">Compliance Evidence Matrix ({complianceItems.length})</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-[10px] uppercase text-slate-500 border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">Framework</th>
                  <th className="py-2.5 px-3">Requirement</th>
                  <th className="py-2.5 px-3">Evidence Status</th>
                  <th className="py-2.5 px-3">Summary Findings</th>
                  <th className="py-2.5 px-3">Remediation Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40">
                {complianceItems.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-800/30">
                    <td className="py-3 px-3 font-bold text-blue-400">{item.framework}</td>
                    <td className="py-3 px-3">
                      <div className="font-bold text-white">{item.requirement_name}</div>
                      <div className="text-[10px] text-slate-500">{item.description}</div>
                    </td>
                    <td className="py-3 px-3">
                      {item.status === 'EVIDENCE_PRESENT' ? (
                        <Badge variant="success" size="sm">EVIDENCE PRESENT</Badge>
                      ) : item.status === 'POTENTIAL_GAP' ? (
                        <Badge variant="danger" size="sm">POTENTIAL GAP</Badge>
                      ) : (
                        <Badge variant="warning" size="sm">REQUIRES REVIEW</Badge>
                      )}
                    </td>
                    <td className="py-3 px-3 text-slate-300 text-[10px]">{item.evidence_summary}</td>
                    <td className="py-3 px-3 text-slate-400 text-[10px]">{item.remediation_action || 'None required'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* EVIDENCE DRAWER MODAL */}
      {isEvidenceDrawerOpen && selectedClauseForEvidence && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn font-mono text-xs">
          <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-xl shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <FileCheck2 className="w-4 h-4 text-emerald-400" />
                Verified Legal Citation
              </h3>
              <button onClick={() => setIsEvidenceDrawerOpen(false)} className="text-slate-400 hover:text-white">
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <span className="text-[10px] text-slate-500 uppercase block">Clause Title</span>
                <span className="text-white font-bold">{selectedClauseForEvidence.clause_title}</span>
              </div>

              <div>
                <span className="text-[10px] text-slate-500 uppercase block">Document Context</span>
                <span className="text-slate-300">
                  {selectedClauseForEvidence.section_reference || 'General Section'} • Page {selectedClauseForEvidence.page_number || 1}
                </span>
              </div>

              <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg space-y-1">
                <span className="text-[10px] text-emerald-400 uppercase font-bold block">Verbatim Source Quote</span>
                <p className="text-slate-200 text-xs italic">&ldquo;{selectedClauseForEvidence.clause_text}&rdquo;</p>
              </div>

              <div className="flex items-center justify-between text-[10px] pt-2 border-t border-slate-800 text-slate-500">
                <span>Fingerprint: {selectedClauseForEvidence.fingerprint.slice(0, 16)}...</span>
                <span className="text-emerald-400 font-bold">Confidence: {selectedClauseForEvidence.confidence}</span>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                type="button"
                onClick={() => setIsEvidenceDrawerOpen(false)}
                className="px-4 py-1.5 rounded bg-slate-800 text-white font-bold"
              >
                Close Drawer
              </button>
            </div>
          </div>
        </div>
      )}

      {/* REGISTER CONTRACT MODAL */}
      {isRegisterContractOpen && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn font-mono text-xs">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-xl shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white">Register Contract Agreement</h3>
              <button onClick={() => setIsRegisterContractOpen(false)} className="text-slate-400 hover:text-white">
                <XCircle className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleRegisterContract} className="space-y-3">
              <div>
                <label className="text-[10px] uppercase text-slate-400 block mb-1">Contract Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Master Services Agreement"
                  value={cTitle}
                  onChange={(e) => setCTitle(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-white"
                />
              </div>

              <div>
                <label className="text-[10px] uppercase text-slate-400 block mb-1">Counterparty *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Acme Corporation"
                  value={cCounterparty}
                  onChange={(e) => setCCounterparty(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] uppercase text-slate-400 block mb-1">Contract Type</label>
                  <select
                    value={cType}
                    onChange={(e) => setCType(e.target.value)}
                    className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-200"
                  >
                    <option value="CUSTOMER_MSA">CUSTOMER_MSA</option>
                    <option value="VENDOR_SAAS">VENDOR_SAAS</option>
                    <option value="EMPLOYMENT">EMPLOYMENT</option>
                    <option value="IP_ASSIGNMENT">IP_ASSIGNMENT</option>
                    <option value="PARTNERSHIP">PARTNERSHIP</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] uppercase text-slate-400 block mb-1">Annual Value ($)</label>
                  <input
                    type="number"
                    value={cAnnualValue}
                    onChange={(e) => setCAnnualValue(parseFloat(e.target.value) || 0)}
                    className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-200"
                  />
                </div>
              </div>

              <div>
                <label className="text-[10px] uppercase text-slate-400 block mb-1">Governing Law</label>
                <input
                  type="text"
                  value={cGoverningLaw}
                  onChange={(e) => setCGoverningLaw(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-200"
                />
              </div>

              <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
                <button type="button" onClick={() => setIsRegisterContractOpen(false)} className="px-3 py-1.5 rounded bg-slate-800 text-slate-300">
                  Cancel
                </button>
                <button type="submit" className="px-4 py-1.5 rounded bg-emerald-600 text-white font-bold">
                  Save Contract
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
