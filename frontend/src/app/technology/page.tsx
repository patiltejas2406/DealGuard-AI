'use client';

/**
 * DealGuard AI — Phase 13: Operational, Technology & Product Architecture Diligence Console
 */

import React, { useEffect, useState } from 'react';
import {
  Cpu,
  Server,
  Cloud,
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
  Layers,
  Database,
  Activity,
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { api } from '@/lib/api';
import {
  Deal,
  OperationalMetricResponse,
  TechnologyDependencyResponse,
  TechnologyFindingResponse,
  TechnologySummaryResponse,
} from '@/types';

type ActiveTab = 'FINDINGS' | 'DEPENDENCIES' | 'CLOUD' | 'RELIABILITY';

const TECH_CATEGORIES = [
  'ALL',
  'TECHNOLOGY_DEBT',
  'LEGACY_ARCHITECTURE',
  'SCALABILITY',
  'CLOUD_INFRASTRUCTURE',
  'CLOUD_COST',
  'API_DEPENDENCIES',
  'SINGLE_POINT_OF_FAILURE',
  'DISASTER_RECOVERY',
  'SLA_PERFORMANCE',
  'SECURITY_ARCHITECTURE',
  'PRODUCT_ARCHITECTURE',
  'ROADMAP_RISK',
];

export default function TechnologyDiligencePage() {
  // Deal & Tab State
  const [deals, setDeals] = useState<Deal[]>([]);
  const [selectedDealId, setSelectedDealId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<ActiveTab>('FINDINGS');

  // Tech Data State
  const [summary, setSummary] = useState<TechnologySummaryResponse | null>(null);
  const [findings, setFindings] = useState<TechnologyFindingResponse[]>([]);
  const [dependencies, setDependencies] = useState<TechnologyDependencyResponse[]>([]);
  const [cloudMetrics, setCloudMetrics] = useState<OperationalMetricResponse[]>([]);
  const [reliabilityMetrics, setReliabilityMetrics] = useState<OperationalMetricResponse[]>([]);

  // Filter State
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');

  // Modals & Drawers
  const [isCreateFindingOpen, setIsCreateFindingOpen] = useState<boolean>(false);
  const [isEvidenceDrawerOpen, setIsEvidenceDrawerOpen] = useState<boolean>(false);
  const [selectedFindingForEvidence, setSelectedFindingForEvidence] = useState<TechnologyFindingResponse | null>(null);

  // Form State: Create Finding
  const [fTitle, setFTitle] = useState<string>('');
  const [fCategory, setFCategory] = useState<string>('TECHNOLOGY_DEBT');
  const [fFact, setFFact] = useState<string>('');
  const [fImpact, setFImpact] = useState<string>('');
  const [fRec, setFRec] = useState<string>('');
  const [fSeverity, setFSeverity] = useState<string>('HIGH');
  const [fExposure, setFExposure] = useState<number>(250000);

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

  // 2. Load Tech Data whenever deal changes
  useEffect(() => {
    if (!selectedDealId) return;
    loadAllTechData(selectedDealId);
  }, [selectedDealId]);

  async function loadAllTechData(dealId: string) {
    setIsLoading(true);
    setError(null);
    try {
      const [sumRes, fList, dList, cList, rList] = await Promise.all([
        api.getTechnologySummary(dealId),
        api.getTechnologyFindings(dealId),
        api.getTechnologyDependencies(dealId),
        api.getInfrastructureMetrics(dealId),
        api.getReliabilityMetrics(dealId),
      ]);
      setSummary(sumRes);
      setFindings(fList);
      setDependencies(dList);
      setCloudMetrics(cList);
      setReliabilityMetrics(rList);
    } catch (err: any) {
      setError(err?.message || 'Failed to load technology diligence data.');
    } finally {
      setIsLoading(false);
    }
  }

  // 3. Trigger Technology Scan
  async function handleTriggerScan() {
    if (!selectedDealId) return;
    setIsScanning(true);
    setError(null);
    try {
      const res = await api.scanTechnologyDocuments(selectedDealId);
      setSuccessMessage(res.message);
      loadAllTechData(selectedDealId);
    } catch (err: any) {
      setError(err?.message || 'Technology scan failed.');
    } finally {
      setIsScanning(false);
    }
  }

  // 4. Create Custom Finding
  async function handleCreateFinding(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedDealId || !fTitle || !fFact) return;
    try {
      await api.createTechnologyFinding(selectedDealId, {
        title: fTitle,
        category: fCategory,
        technical_fact: fFact,
        business_impact: fImpact,
        recommendation: fRec,
        severity: fSeverity,
        monetary_exposure: fExposure,
      });
      setSuccessMessage(`Technology finding '${fTitle}' created.`);
      setIsCreateFindingOpen(false);
      setFTitle('');
      setFFact('');
      loadAllTechData(selectedDealId);
    } catch (err: any) {
      setError(err?.message || 'Failed to create finding.');
    }
  }

  // 5. Update Finding Status
  async function handleUpdateFindingStatus(findingId: string, newStatus: string) {
    if (!selectedDealId) return;
    try {
      await api.updateTechnologyFindingStatus(selectedDealId, findingId, {
        status: newStatus,
        notes: 'Status updated via Tech Diligence Console',
      });
      setSuccessMessage('Finding status updated.');
      loadAllTechData(selectedDealId);
    } catch (err: any) {
      setError(err?.message || 'Failed to update status.');
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

  const filteredFindings = findings.filter((f) =>
    categoryFilter === 'ALL' ? true : f.category === categoryFilter
  );

  return (
    <div className="min-h-screen bg-surface-base text-slate-100 p-6 space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 border-b border-slate-800 pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2 font-mono">
                Technology & Operations Diligence Console
                <Badge variant="success" size="sm">Phase 13 v1.0</Badge>
              </h1>
              <p className="text-xs text-slate-400">
                30-Category Tech Debt Scanner, Single Points of Failure (SPOF), Cloud Spend & SLA Reliability
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
            {isScanning ? 'Scanning Data Room...' : 'Run Tech Diligence Scan'}
          </button>

          <button
            type="button"
            onClick={() => setIsCreateFindingOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold border border-slate-700 font-mono transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            Add Finding
          </button>

          <button
            type="button"
            onClick={() => selectedDealId && loadAllTechData(selectedDealId)}
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
            <span className="text-[10px] text-slate-500 uppercase">Tech Risk Score</span>
            <p className="text-xl font-bold text-amber-400">{summary.technology_risk_score} / 100</p>
            <span className="text-[10px] text-slate-400">Risk Band: {summary.risk_band}</span>
          </Card>

          <Card className="p-3.5 bg-slate-900/90 border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-500 uppercase">Cloud Infrastructure</span>
            <p className="text-xl font-bold text-blue-400">{formatCurrency(summary.annual_cloud_spend)}/yr</p>
            <span className="text-[10px] text-slate-400">{formatCurrency(summary.monthly_run_rate)}/mo Run-Rate</span>
          </Card>

          <Card className="p-3.5 bg-slate-900/90 border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-500 uppercase">Uptime & Reliability</span>
            <p className="text-xl font-bold text-emerald-400">{summary.average_uptime_pct}%</p>
            <span className="text-[10px] text-slate-400">{summary.sla_breaches_count} SLA Deviations</span>
          </Card>

          <Card className="p-3.5 bg-slate-900/90 border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-500 uppercase">Single Points of Failure</span>
            <p className="text-xl font-bold text-rose-400">{summary.spof_count} Critical SPOFs</p>
            <span className="text-[10px] text-slate-400">Infrastructure & Key Persons</span>
          </Card>

          <Card className="p-3.5 bg-slate-900/90 border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-500 uppercase">Technical Findings</span>
            <p className="text-xl font-bold text-white">{summary.total_findings_count}</p>
            <span className="text-[10px] text-rose-400 font-bold">{summary.critical_findings_count} Critical / {summary.high_findings_count} High</span>
          </Card>

          <Card className="p-3.5 bg-slate-900/90 border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-500 uppercase">Remediation Exposure</span>
            <p className="text-xl font-bold text-white">{formatCurrency(summary.total_monetary_exposure)}</p>
            <span className="text-[10px] text-slate-400">Estimated Tech Debt Cost</span>
          </Card>
        </div>
      )}

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2 text-xs font-mono">
        <button
          onClick={() => setActiveTab('FINDINGS')}
          className={`px-3.5 py-1.5 rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === 'FINDINGS'
              ? 'bg-emerald-600 text-white font-bold shadow'
              : 'text-slate-400 hover:text-white hover:bg-slate-900'
          }`}
        >
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
          Technical & Debt Findings ({findings.length})
        </button>
        <button
          onClick={() => setActiveTab('DEPENDENCIES')}
          className={`px-3.5 py-1.5 rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === 'DEPENDENCIES'
              ? 'bg-emerald-600 text-white font-bold shadow'
              : 'text-slate-400 hover:text-white hover:bg-slate-900'
          }`}
        >
          <Server className="w-3.5 h-3.5 text-blue-400" />
          Dependencies & SPOFs ({dependencies.length})
        </button>
        <button
          onClick={() => setActiveTab('CLOUD')}
          className={`px-3.5 py-1.5 rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === 'CLOUD'
              ? 'bg-emerald-600 text-white font-bold shadow'
              : 'text-slate-400 hover:text-white hover:bg-slate-900'
          }`}
        >
          <Cloud className="w-3.5 h-3.5 text-indigo-400" />
          Cloud Spend & Infra ({cloudMetrics.length})
        </button>
        <button
          onClick={() => setActiveTab('RELIABILITY')}
          className={`px-3.5 py-1.5 rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === 'RELIABILITY'
              ? 'bg-emerald-600 text-white font-bold shadow'
              : 'text-slate-400 hover:text-white hover:bg-slate-900'
          }`}
        >
          <Activity className="w-3.5 h-3.5 text-emerald-400" />
          Reliability & SLAs ({reliabilityMetrics.length})
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

      {/* TAB 1: TECHNICAL FINDINGS */}
      {activeTab === 'FINDINGS' && (
        <Card className="p-5 bg-slate-900/90 border-slate-800 space-y-4 font-mono">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-400">Filter Category:</span>
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-slate-200 focus:outline-none cursor-pointer"
              >
                {TECH_CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <span className="text-xs text-slate-400">
              Showing {filteredFindings.length} of {findings.length} Findings
            </span>
          </div>

          <div className="space-y-3">
            {filteredFindings.map((f) => (
              <div key={f.id} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-white">{f.title}</span>
                      <Badge variant="default" size="sm">{f.category}</Badge>
                      {getSeverityBadge(f.severity)}
                    </div>
                    <div className="text-[10px] text-slate-400 mt-1">{f.technical_fact}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <select
                      value={f.status}
                      onChange={(e) => handleUpdateFindingStatus(f.id, e.target.value)}
                      className="bg-slate-900 border border-slate-800 rounded px-2 py-1 text-[10px] text-slate-200 focus:outline-none cursor-pointer"
                    >
                      <option value="IDENTIFIED">IDENTIFIED</option>
                      <option value="REQUIRES_REVIEW">REQUIRES_REVIEW</option>
                      <option value="REMEDIATION_PLANNED">REMEDIATION_PLANNED</option>
                      <option value="MITIGATED">MITIGATED</option>
                      <option value="ACCEPTED">ACCEPTED</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  <div className="p-2.5 rounded bg-slate-900/70 border border-slate-800/80 space-y-1">
                    <span className="text-[10px] text-slate-500 uppercase font-bold">Business & Integration Impact</span>
                    <p className="text-slate-300 text-xs">{f.business_impact}</p>
                  </div>
                  <div className="p-2.5 rounded bg-slate-900/70 border border-slate-800/80 space-y-1">
                    <span className="text-[10px] text-emerald-400 uppercase font-bold">Recommended Architecture Remediation</span>
                    <p className="text-slate-300 text-xs">{f.recommendation}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* TAB 2: DEPENDENCIES & SPOFs */}
      {activeTab === 'DEPENDENCIES' && (
        <Card className="p-5 bg-slate-900/90 border-slate-800 space-y-4 font-mono">
          <div className="border-b border-slate-800 pb-3">
            <span className="text-xs font-bold text-white">External Dependencies & Single Points of Failure ({dependencies.length})</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-[10px] uppercase text-slate-500 border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">Dependency</th>
                  <th className="py-2.5 px-3">Type</th>
                  <th className="py-2.5 px-3">Provider</th>
                  <th className="py-2.5 px-3">Criticality</th>
                  <th className="py-2.5 px-3">SPOF?</th>
                  <th className="py-2.5 px-3">Failure Impact</th>
                  <th className="py-2.5 px-3">Annual Cost</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40">
                {dependencies.map((d) => (
                  <tr key={d.id} className="hover:bg-slate-800/30">
                    <td className="py-3 px-3 font-bold text-white">{d.dependency_name}</td>
                    <td className="py-3 px-3 text-slate-400">{d.dependency_type}</td>
                    <td className="py-3 px-3 text-slate-300 font-bold">{d.provider}</td>
                    <td className="py-3 px-3">{getSeverityBadge(d.criticality)}</td>
                    <td className="py-3 px-3">
                      {d.is_single_point_of_failure ? (
                        <Badge variant="danger" size="sm">YES (SPOF)</Badge>
                      ) : (
                        <span className="text-[10px] text-slate-500">Redundant</span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-slate-300 text-[10px] max-w-xs">{d.failure_impact}</td>
                    <td className="py-3 px-3 font-bold text-white">{formatCurrency(d.annual_cost)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* TAB 3: CLOUD SPEND */}
      {activeTab === 'CLOUD' && (
        <Card className="p-5 bg-slate-900/90 border-slate-800 space-y-4 font-mono">
          <div className="border-b border-slate-800 pb-3">
            <span className="text-xs font-bold text-white">Cloud Infrastructure & Compute Spend Intelligence</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {cloudMetrics.map((m) => (
              <div key={m.id} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">{m.metric_name}</span>
                  <Badge variant="success" size="sm">{m.status}</Badge>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-bold text-blue-400">{formatCurrency(m.observed_value)}</span>
                  <span className="text-xs text-slate-500">{m.unit}</span>
                </div>
                <p className="text-xs text-slate-400">{m.evidence_summary}</p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* TAB 4: RELIABILITY & SLAS */}
      {activeTab === 'RELIABILITY' && (
        <Card className="p-5 bg-slate-900/90 border-slate-800 space-y-4 font-mono">
          <div className="border-b border-slate-800 pb-3">
            <span className="text-xs font-bold text-white">Service Level Agreement (SLA) & Uptime Adherence</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {reliabilityMetrics.map((r) => (
              <div key={r.id} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">{r.metric_name}</span>
                  {r.status === 'DEVIATION' ? (
                    <Badge variant="warning" size="sm">DEVIATION</Badge>
                  ) : (
                    <Badge variant="success" size="sm">ON TARGET</Badge>
                  )}
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-bold text-emerald-400">{r.observed_value}%</span>
                  <span className="text-xs text-slate-500">Target: {r.target_value}%</span>
                </div>
                <p className="text-xs text-slate-400">{r.evidence_summary}</p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* CREATE FINDING MODAL */}
      {isCreateFindingOpen && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn font-mono text-xs">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-xl shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white">Add Technology Finding</h3>
              <button onClick={() => setIsCreateFindingOpen(false)} className="text-slate-400 hover:text-white">
                <XCircle className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleCreateFinding} className="space-y-3">
              <div>
                <label className="text-[10px] uppercase text-slate-400 block mb-1">Finding Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Unreplicated Primary Database"
                  value={fTitle}
                  onChange={(e) => setFTitle(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] uppercase text-slate-400 block mb-1">Category</label>
                  <select
                    value={fCategory}
                    onChange={(e) => setFCategory(e.target.value)}
                    className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-200"
                  >
                    <option value="TECHNOLOGY_DEBT">TECHNOLOGY_DEBT</option>
                    <option value="SINGLE_POINT_OF_FAILURE">SINGLE_POINT_OF_FAILURE</option>
                    <option value="CLOUD_INFRASTRUCTURE">CLOUD_INFRASTRUCTURE</option>
                    <option value="SLA_PERFORMANCE">SLA_PERFORMANCE</option>
                    <option value="DISASTER_RECOVERY">DISASTER_RECOVERY</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] uppercase text-slate-400 block mb-1">Severity</label>
                  <select
                    value={fSeverity}
                    onChange={(e) => setFSeverity(e.target.value)}
                    className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-200"
                  >
                    <option value="CRITICAL">CRITICAL</option>
                    <option value="HIGH">HIGH</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="LOW">LOW</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-[10px] uppercase text-slate-400 block mb-1">Technical Fact *</label>
                <textarea
                  required
                  rows={2}
                  value={fFact}
                  onChange={(e) => setFFact(e.target.value)}
                  placeholder="Observed technical reality from architecture review..."
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-white"
                />
              </div>

              <div>
                <label className="text-[10px] uppercase text-slate-400 block mb-1">Business Impact</label>
                <input
                  type="text"
                  value={fImpact}
                  onChange={(e) => setFImpact(e.target.value)}
                  placeholder="Consequence on scale or revenue..."
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-white"
                />
              </div>

              <div>
                <label className="text-[10px] uppercase text-slate-400 block mb-1">Remediation Recommendation</label>
                <input
                  type="text"
                  value={fRec}
                  onChange={(e) => setFRec(e.target.value)}
                  placeholder="Post-acquisition engineering fix..."
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-white"
                />
              </div>

              <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
                <button type="button" onClick={() => setIsCreateFindingOpen(false)} className="px-3 py-1.5 rounded bg-slate-800 text-slate-300">
                  Cancel
                </button>
                <button type="submit" className="px-4 py-1.5 rounded bg-emerald-600 text-white font-bold">
                  Save Finding
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
