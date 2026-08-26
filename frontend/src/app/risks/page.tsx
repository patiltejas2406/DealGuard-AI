'use client';

/**
 * DealGuard AI — Phase 7: 17-Pillar Deal Risk Intelligence & Automated Detection Console
 */

import React, { useEffect, useState, useMemo } from 'react';
import {
  AlertTriangle,
  Shield,
  Search,
  Filter,
  RefreshCw,
  Sparkles,
  Plus,
  FileText,
  CheckCircle2,
  XCircle,
  Eye,
  ArrowUpDown,
  ChevronRight,
  TrendingDown,
  Building2,
  Layers,
  HelpCircle,
  Clock,
  Briefcase,
  Sliders,
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import { Deal, RiskCategoryInfo, RiskItem, RiskMatrixResponse } from '@/types';

// Human-readable labels for the 17 Diligence Pillars
const CATEGORY_NAMES: Record<string, string> = {
  CUSTOMER_CONCENTRATION: 'Customer Concentration',
  KEY_PERSON: 'Key Person & Founder',
  LEGAL_LITIGATION: 'Legal & Litigation',
  REGULATORY: 'Regulatory Compliance',
  CYBERSECURITY: 'Cybersecurity & Privacy',
  TECHNOLOGY_DEBT: 'Technology Debt',
  ESG: 'ESG & Environmental',
  RESTATEMENT: 'Restatement & Controls',
  SUPPLY_CHAIN: 'Supply Chain & Vendors',
  IP_INFRINGEMENT: 'IP & Patent Rights',
  TAX: 'Tax & Transfer Pricing',
  MACRO_FX: 'Macroeconomic & FX',
  LABOR_WORKFORCE: 'Labor & Workforce',
  CHANGE_OF_CONTROL: 'Change of Control',
  DEBT_COVENANTS: 'Debt & Solvency',
  REVENUE_QUALITY: 'Revenue Quality & Churn',
  INTEGRATION_COMPLEXITY: 'Integration Complexity',
};

const SEVERITY_LABELS: Record<number, string> = {
  1: '1 - Negligible',
  2: '2 - Minor',
  3: '3 - Moderate',
  4: '4 - Major',
  5: '5 - Catastrophic',
};

const LIKELIHOOD_LABELS: Record<number, string> = {
  1: '1 - Rare',
  2: '2 - Unlikely',
  3: '3 - Possible',
  4: '4 - Likely',
  5: '5 - Almost Certain',
};

export default function RiskIntelligencePage() {
  const { isAuthenticated } = useAuth();

  // Deals State
  const [deals, setDeals] = useState<Deal[]>([]);
  const [selectedDealId, setSelectedDealId] = useState<string | null>(null);

  // Risks Data State
  const [risks, setRisks] = useState<RiskItem[]>([]);
  const [matrixData, setMatrixData] = useState<RiskMatrixResponse | null>(null);
  const [categories, setCategories] = useState<RiskCategoryInfo[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [scanResult, setScanResult] = useState<{ detected: number; created: number; skipped: number } | null>(null);

  // Filters & Sorting State
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [selectedLevel, setSelectedLevel] = useState<string>('ALL');
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [activeMatrixCell, setActiveMatrixCell] = useState<{ s: number; l: number } | null>(null);
  const [sortBy, setSortBy] = useState<string>('score');
  const [sortDesc, setSortDesc] = useState<boolean>(true);

  // Modal / Drawer State
  const [selectedRisk, setSelectedRisk] = useState<RiskItem | null>(null);
  const [isDetailDrawerOpen, setIsDetailDrawerOpen] = useState<boolean>(false);
  const [isAddModalOpen, setIsAddModalOpen] = useState<boolean>(false);

  // Form State for Adding Risk
  const [newCategory, setNewCategory] = useState<string>('CUSTOMER_CONCENTRATION');
  const [newTitle, setNewTitle] = useState<string>('');
  const [newDescription, setNewDescription] = useState<string>('');
  const [newSeverity, setNewSeverity] = useState<number>(3);
  const [newLikelihood, setNewLikelihood] = useState<number>(3);
  const [newMitigation, setNewMitigation] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  // 1. Load Deals on mount
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

  // 2. Load Risks, Matrix & Categories whenever selected deal changes
  useEffect(() => {
    if (!selectedDealId) return;
    loadRiskData(selectedDealId);
  }, [selectedDealId, selectedCategory, selectedLevel, selectedStatus, sortBy, sortDesc]);

  async function loadRiskData(dealId: string) {
    setIsLoading(true);
    setError(null);
    try {
      const [riskListRes, matrixRes, catRes] = await Promise.all([
        api.listRisks(dealId, {
          category: selectedCategory !== 'ALL' ? selectedCategory : undefined,
          risk_level: selectedLevel !== 'ALL' ? selectedLevel : undefined,
          status: selectedStatus !== 'ALL' ? selectedStatus : undefined,
          sort_by: sortBy,
          sort_desc: sortDesc,
        }),
        api.getRiskMatrix(dealId),
        api.getRiskCategories(dealId),
      ]);

      setRisks(riskListRes.items || []);
      setMatrixData(matrixRes);
      setCategories(catRes || []);
    } catch (err: any) {
      setError(err?.message || 'Failed to load risk intelligence data.');
    } finally {
      setIsLoading(false);
    }
  }

  // 3. Trigger Automated Document Risk Scan
  async function handleRunRiskScan() {
    if (!selectedDealId) return;
    setIsScanning(true);
    setScanResult(null);
    try {
      const res = await api.detectRisks(selectedDealId, { min_confidence: 0.55 });
      setScanResult({
        detected: res.detected_count,
        created: res.created_count,
        skipped: res.duplicates_skipped,
      });
      await loadRiskData(selectedDealId);
    } catch (err: any) {
      setError(err?.message || 'Automated risk scan encountered an issue.');
    } finally {
      setIsScanning(false);
    }
  }

  // 4. Create Manual Risk Item
  async function handleCreateRisk(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedDealId || !newTitle || !newDescription) return;

    setIsSubmitting(true);
    try {
      await api.createRisk(selectedDealId, {
        category: newCategory,
        title: newTitle,
        description: newDescription,
        severity: newSeverity,
        likelihood: newLikelihood,
        status: 'IDENTIFIED',
        mitigation_strategy: newMitigation || undefined,
      });
      setIsAddModalOpen(false);
      setNewTitle('');
      setNewDescription('');
      setNewMitigation('');
      await loadRiskData(selectedDealId);
    } catch (err: any) {
      setError(err?.message || 'Failed to create risk item.');
    } finally {
      setIsSubmitting(false);
    }
  }

  // 5. Update Risk Workflow Status
  async function handleUpdateStatus(riskId: string, status: string) {
    if (!selectedDealId) return;
    try {
      const updated = await api.updateRiskStatus(selectedDealId, riskId, {
        status,
        rationale: `Status marked as ${status} in Risk Intelligence Console.`,
      });
      setRisks((prev) => prev.map((r) => (r.id === riskId ? updated : r)));
      if (selectedRisk && selectedRisk.id === riskId) {
        setSelectedRisk(updated);
      }
      const updatedMatrix = await api.getRiskMatrix(selectedDealId);
      setMatrixData(updatedMatrix);
    } catch (err: any) {
      setError(err?.message || 'Failed to update risk status.');
    }
  }

  // Filter risks by search query and matrix cell
  const filteredRisks = useMemo(() => {
    return risks.filter((r) => {
      if (activeMatrixCell) {
        if (r.severity !== activeMatrixCell.s || r.likelihood !== activeMatrixCell.l) {
          return false;
        }
      }
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        return (
          r.title.toLowerCase().includes(query) ||
          r.description.toLowerCase().includes(query) ||
          (CATEGORY_NAMES[r.category] || r.category).toLowerCase().includes(query)
        );
      }
      return true;
    });
  }, [risks, activeMatrixCell, searchQuery]);

  // Selected Deal Object
  const currentDeal = deals.find((d) => d.id === selectedDealId);

  // Helper for Level Badges
  const getLevelVariant = (level: string) => {
    switch (level) {
      case 'CRITICAL':
        return 'danger';
      case 'HIGH':
        return 'warning';
      case 'MODERATE':
        return 'default';
      case 'LOW':
        return 'success';
      default:
        return 'default';
    }
  };

  // Helper for Status Pill
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ACCEPTED':
        return 'bg-emerald-950/80 text-emerald-400 border-emerald-800';
      case 'REVIEWED':
        return 'bg-blue-950/80 text-blue-400 border-blue-800';
      case 'MITIGATED':
        return 'bg-purple-950/80 text-purple-400 border-purple-800';
      case 'REJECTED':
        return 'bg-rose-950/80 text-rose-400 border-rose-800';
      default:
        return 'bg-amber-950/80 text-amber-400 border-amber-800';
    }
  };

  // Matrix cell background color calculation
  const getCellBg = (severity: number, likelihood: number) => {
    const score = severity * likelihood;
    if (score >= 15) return 'bg-rose-950/40 hover:bg-rose-900/60 border-rose-800/60 text-rose-300';
    if (score >= 10) return 'bg-amber-950/40 hover:bg-amber-900/60 border-amber-800/60 text-amber-300';
    if (score >= 5) return 'bg-yellow-950/30 hover:bg-yellow-900/50 border-yellow-800/50 text-yellow-300';
    return 'bg-emerald-950/30 hover:bg-emerald-900/50 border-emerald-800/40 text-emerald-300';
  };

  return (
    <div className="min-h-screen bg-surface-base text-slate-100 p-6 space-y-6">
      {/* Top Header Bar */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 border-b border-slate-800 pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2 font-mono">
                17-Pillar Deal Risk Intelligence
                <Badge variant="success" size="sm">Deterministic 5x5 Engine</Badge>
              </h1>
              <p className="text-xs text-slate-400">
                Institutional M&A Risk Detection, Grounded Evidence Citations & Actionable Mitigation Matrix
              </p>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Deal Workspace Selector */}
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs font-mono">
            <Building2 className="w-4 h-4 text-emerald-400" />
            <select
              value={selectedDealId || ''}
              onChange={(e) => {
                setSelectedDealId(e.target.value);
                setActiveMatrixCell(null);
              }}
              className="bg-transparent text-slate-200 focus:outline-none cursor-pointer"
            >
              {deals.map((d) => (
                <option key={d.id} value={d.id} className="bg-slate-900 text-slate-200">
                  {d.title} ({d.currency})
                </option>
              ))}
            </select>
          </div>

          {/* Automated Document Risk Scanner Trigger */}
          <button
            type="button"
            onClick={handleRunRiskScan}
            disabled={isScanning || !selectedDealId}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-semibold shadow-lg shadow-emerald-950 transition-colors font-mono"
          >
            <Sparkles className={`w-3.5 h-3.5 ${isScanning ? 'animate-spin' : ''}`} />
            {isScanning ? 'Scanning Data Room...' : 'Run Automated Risk Scan'}
          </button>

          {/* Add Manual Risk Button */}
          <button
            type="button"
            onClick={() => setIsAddModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors font-mono"
          >
            <Plus className="w-3.5 h-3.5" />
            Add Risk Item
          </button>

          {/* Refresh Button */}
          <button
            type="button"
            onClick={() => selectedDealId && loadRiskData(selectedDealId)}
            className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
            title="Refresh Risk Register"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Alert / Notification Feedback */}
      {scanResult && (
        <div className="p-3 rounded-lg bg-emerald-950/50 border border-emerald-800/80 text-emerald-300 text-xs flex items-center justify-between font-mono animate-fadeIn">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>
              Risk Scan Complete: <strong>{scanResult.detected}</strong> potential risk signals detected in Data Room chunks (
              <strong>{scanResult.created}</strong> new risk records created, <strong>{scanResult.skipped}</strong> duplicates skipped).
            </span>
          </div>
          <button onClick={() => setScanResult(null)} className="text-slate-400 hover:text-white">
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

      {/* KPI Metric Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <Card className="p-4 bg-slate-900/90 border-slate-800">
          <p className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">Total Risks</p>
          <p className="text-2xl font-bold text-white font-mono mt-1">{matrixData?.total_risks ?? 0}</p>
          <p className="text-[10px] text-slate-500 mt-1">Across 17 Pillars</p>
        </Card>

        <Card className="p-4 bg-rose-950/20 border-rose-900/40">
          <p className="text-[11px] font-mono text-rose-400 uppercase tracking-wider">Critical (15-25)</p>
          <p className="text-2xl font-bold text-rose-400 font-mono mt-1">{matrixData?.level_counts.CRITICAL ?? 0}</p>
          <p className="text-[10px] text-rose-400/60 mt-1">Immediate Escalation</p>
        </Card>

        <Card className="p-4 bg-amber-950/20 border-amber-900/40">
          <p className="text-[11px] font-mono text-amber-400 uppercase tracking-wider">High (10-14)</p>
          <p className="text-2xl font-bold text-amber-400 font-mono mt-1">{matrixData?.level_counts.HIGH ?? 0}</p>
          <p className="text-[10px] text-amber-400/60 mt-1">Escrow / Indemnity</p>
        </Card>

        <Card className="p-4 bg-yellow-950/20 border-yellow-900/40">
          <p className="text-[11px] font-mono text-yellow-400 uppercase tracking-wider">Moderate (5-9)</p>
          <p className="text-2xl font-bold text-yellow-400 font-mono mt-1">{matrixData?.level_counts.MODERATE ?? 0}</p>
          <p className="text-[10px] text-yellow-400/60 mt-1">Targeted Monitoring</p>
        </Card>

        <Card className="p-4 bg-emerald-950/20 border-emerald-900/40">
          <p className="text-[11px] font-mono text-emerald-400 uppercase tracking-wider">Low (1-4)</p>
          <p className="text-2xl font-bold text-emerald-400 font-mono mt-1">{matrixData?.level_counts.LOW ?? 0}</p>
          <p className="text-[10px] text-emerald-400/60 mt-1">Acceptable Exposure</p>
        </Card>

        <Card className="p-4 bg-slate-900/90 border-slate-800">
          <p className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">Avg Score</p>
          <p className="text-2xl font-bold text-emerald-400 font-mono mt-1">
            {matrixData?.average_score ? `${matrixData.average_score} / 25` : '0.0'}
          </p>
          <p className="text-[10px] text-slate-500 mt-1">Deal Risk Quotient</p>
        </Card>
      </div>

      {/* Main Content Grid: Heatmap Matrix & Pillar Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* 5x5 Likelihood x Severity Risk Matrix */}
        <Card className="lg:col-span-7 p-5 bg-slate-900/90 border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h2 className="text-sm font-semibold text-white font-mono flex items-center gap-2">
                <Layers className="w-4 h-4 text-emerald-400" />
                5x5 Likelihood &times; Severity Heatmap Matrix
              </h2>
              <p className="text-[11px] text-slate-400">
                Click any cell to filter the Risk Register to exact coordinate items
              </p>
            </div>
            {activeMatrixCell && (
              <button
                onClick={() => setActiveMatrixCell(null)}
                className="text-[11px] font-mono text-slate-400 hover:text-white px-2 py-0.5 rounded bg-slate-800 border border-slate-700"
              >
                Clear Matrix Filter ({activeMatrixCell.s}&times;{activeMatrixCell.l})
              </button>
            )}
          </div>

          {/* 5x5 Grid Visualization */}
          <div className="space-y-2">
            {/* Y-Axis Label */}
            <div className="text-[10px] uppercase font-mono tracking-wider text-slate-400 flex items-center justify-between px-1">
              <span>Likelihood &uarr;</span>
              <span>Severity &rarr;</span>
            </div>

            <div className="space-y-1.5">
              {[5, 4, 3, 2, 1].map((likelihood) => (
                <div key={likelihood} className="grid grid-cols-6 gap-1.5 items-center">
                  <div className="text-[10px] font-mono text-slate-400 truncate text-right pr-2">
                    L{likelihood}
                  </div>
                  {[1, 2, 3, 4, 5].map((severity) => {
                    const cellRisks = matrixData?.matrix_grid?.[likelihood]?.[severity] || [];
                    const isSelected = activeMatrixCell?.s === severity && activeMatrixCell?.l === likelihood;
                    const cellScore = severity * likelihood;

                    return (
                      <button
                        key={`${likelihood}-${severity}`}
                        type="button"
                        onClick={() => {
                          if (isSelected) {
                            setActiveMatrixCell(null);
                          } else {
                            setActiveMatrixCell({ s: severity, l: likelihood });
                          }
                        }}
                        className={`h-12 rounded-lg border p-1 flex flex-col justify-between items-center transition-all ${getCellBg(
                          severity,
                          likelihood
                        )} ${isSelected ? 'ring-2 ring-white border-white scale-105 z-10 shadow-lg' : ''}`}
                      >
                        <span className="text-[9px] font-mono opacity-60">
                          {severity}&times;{likelihood}={cellScore}
                        </span>
                        {cellRisks.length > 0 ? (
                          <span className="text-xs font-bold font-mono px-1.5 py-0.2 rounded-full bg-slate-900/80 shadow">
                            {cellRisks.length}
                          </span>
                        ) : (
                          <span className="text-[10px] opacity-30 font-mono">-</span>
                        )}
                      </button>
                    );
                  })}
                </div>
              ))}
            </div>

            {/* X-Axis Header (Severity) */}
            <div className="grid grid-cols-6 gap-1.5 pt-1 text-center font-mono text-[10px] text-slate-400">
              <div></div>
              <div>S1 (Negligible)</div>
              <div>S2 (Minor)</div>
              <div>S3 (Moderate)</div>
              <div>S4 (Major)</div>
              <div>S5 (Catastrophic)</div>
            </div>
          </div>
        </Card>

        {/* 17 Diligence Pillars Quick Breakdown */}
        <Card className="lg:col-span-5 p-5 bg-slate-900/90 border-slate-800 space-y-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-sm font-semibold text-white font-mono flex items-center gap-2">
                <Shield className="w-4 h-4 text-emerald-400" />
                17-Pillar Category Breakdown
              </h2>
              <span className="text-[11px] font-mono text-slate-400">Distribution</span>
            </div>

            <div className="mt-3 grid grid-cols-2 gap-2 max-h-[300px] overflow-y-auto pr-1">
              {categories.map((cat) => {
                const count = matrixData?.category_counts?.[cat.id] || 0;
                const isCatSelected = selectedCategory === cat.id;

                return (
                  <button
                    key={cat.id}
                    type="button"
                    onClick={() => setSelectedCategory(isCatSelected ? 'ALL' : cat.id)}
                    className={`text-left p-2 rounded-lg border transition-all text-xs flex items-center justify-between ${
                      isCatSelected
                        ? 'bg-emerald-950/60 border-emerald-700 text-emerald-300 font-semibold'
                        : 'bg-slate-950/60 border-slate-800/80 text-slate-300 hover:border-slate-700'
                    }`}
                  >
                    <span className="truncate pr-1">{cat.name}</span>
                    <span
                      className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                        count > 0 ? 'bg-slate-800 text-white font-bold' : 'text-slate-500'
                      }`}
                    >
                      {count}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400 font-mono">
            <span>Filter by Pillar: {selectedCategory}</span>
            {selectedCategory !== 'ALL' && (
              <button onClick={() => setSelectedCategory('ALL')} className="text-emerald-400 hover:underline">
                Reset Filter
              </button>
            )}
          </div>
        </Card>
      </div>

      {/* Filter and Search Controls for Risk Register Table */}
      <Card className="p-4 bg-slate-900/90 border-slate-800 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          {/* Search Input */}
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search risks by title, description, or pillar..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500 font-mono"
            />
          </div>

          {/* Filter Dropdowns */}
          <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
            {/* Risk Level Filter */}
            <select
              value={selectedLevel}
              onChange={(e) => setSelectedLevel(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-300 focus:outline-none"
            >
              <option value="ALL">All Risk Levels</option>
              <option value="CRITICAL">Critical (15-25)</option>
              <option value="HIGH">High (10-14)</option>
              <option value="MODERATE">Moderate (5-9)</option>
              <option value="LOW">Low (1-4)</option>
            </select>

            {/* Status Filter */}
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-300 focus:outline-none"
            >
              <option value="ALL">All Statuses</option>
              <option value="IDENTIFIED">Identified</option>
              <option value="REVIEWED">Reviewed</option>
              <option value="ACCEPTED">Accepted</option>
              <option value="MITIGATED">Mitigated</option>
              <option value="REJECTED">Rejected</option>
            </select>

            {/* Sort Dropdown */}
            <select
              value={`${sortBy}_${sortDesc}`}
              onChange={(e) => {
                const [col, desc] = e.target.value.split('_');
                setSortBy(col);
                setSortDesc(desc === 'true');
              }}
              className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-300 focus:outline-none"
            >
              <option value="score_true">Highest Risk Score</option>
              <option value="score_false">Lowest Risk Score</option>
              <option value="severity_true">Highest Severity</option>
              <option value="likelihood_true">Highest Likelihood</option>
              <option value="created_at_true">Most Recent</option>
            </select>
          </div>
        </div>

        {/* Risk Register Table */}
        <div className="overflow-x-auto rounded-lg border border-slate-800">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 text-[10px] uppercase font-mono tracking-wider text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">Pillar & Finding</th>
                <th className="py-2.5 px-3">Severity</th>
                <th className="py-2.5 px-3">Likelihood</th>
                <th className="py-2.5 px-3">Score & Level</th>
                <th className="py-2.5 px-3">Evidence</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {filteredRisks.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500 font-mono text-xs">
                    {isLoading ? 'Loading risk items...' : 'No risk items found matching the selected filters.'}
                  </td>
                </tr>
              ) : (
                filteredRisks.map((risk) => {
                  const citCount = risk.evidence_items?.length || 0;

                  return (
                    <tr
                      key={risk.id}
                      className="hover:bg-slate-800/40 transition-colors group cursor-pointer"
                      onClick={() => {
                        setSelectedRisk(risk);
                        setIsDetailDrawerOpen(true);
                      }}
                    >
                      {/* Title & Category */}
                      <td className="py-3 px-3">
                        <div className="space-y-0.5">
                          <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/40 px-1.5 py-0.5 rounded border border-emerald-900/50">
                            {CATEGORY_NAMES[risk.category] || risk.category}
                          </span>
                          <p className="font-medium text-slate-100 group-hover:text-emerald-300 transition-colors line-clamp-1">
                            {risk.title}
                          </p>
                          <p className="text-[11px] text-slate-400 line-clamp-1">{risk.description}</p>
                        </div>
                      </td>

                      {/* Severity */}
                      <td className="py-3 px-3 font-mono text-slate-300 whitespace-nowrap">
                        <span className="text-amber-400 font-bold">{risk.severity}</span> / 5
                      </td>

                      {/* Likelihood */}
                      <td className="py-3 px-3 font-mono text-slate-300 whitespace-nowrap">
                        <span className="text-blue-400 font-bold">{risk.likelihood}</span> / 5
                      </td>

                      {/* Score & Risk Level */}
                      <td className="py-3 px-3 whitespace-nowrap">
                        <div className="flex items-center gap-1.5">
                          <span className="font-mono font-bold text-white text-xs">{risk.score}</span>
                          <Badge variant={getLevelVariant(risk.risk_level)} size="sm">
                            {risk.risk_level}
                          </Badge>
                        </div>
                      </td>

                      {/* Evidence Citations */}
                      <td className="py-3 px-3 whitespace-nowrap">
                        {citCount > 0 ? (
                          <span className="flex items-center gap-1 text-[11px] font-mono text-slate-300 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                            <FileText className="w-3 h-3 text-emerald-400" />
                            {citCount} {citCount === 1 ? 'Citation' : 'Citations'}
                          </span>
                        ) : (
                          <span className="text-[11px] font-mono text-slate-500">Manual Entry</span>
                        )}
                      </td>

                      {/* Status */}
                      <td className="py-3 px-3 whitespace-nowrap">
                        <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${getStatusColor(risk.status)}`}>
                          {risk.status}
                        </span>
                      </td>

                      {/* Action Button */}
                      <td className="py-3 px-3 text-right whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                        <button
                          type="button"
                          onClick={() => {
                            setSelectedRisk(risk);
                            setIsDetailDrawerOpen(true);
                          }}
                          className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono transition-colors"
                        >
                          Details &rarr;
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Risk Detail & Citation Provenance Drawer / Modal */}
      {isDetailDrawerOpen && selectedRisk && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex justify-end animate-fadeIn">
          <div className="w-full max-w-2xl bg-slate-900 border-l border-slate-800 h-full overflow-y-auto p-6 space-y-6 flex flex-col justify-between">
            <div className="space-y-5">
              {/* Header */}
              <div className="flex items-start justify-between border-b border-slate-800 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-mono text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-900/50">
                      {CATEGORY_NAMES[selectedRisk.category] || selectedRisk.category}
                    </span>
                    <Badge variant={getLevelVariant(selectedRisk.risk_level)} size="sm">
                      {selectedRisk.risk_level} ({selectedRisk.score} / 25)
                    </Badge>
                  </div>
                  <h3 className="text-lg font-bold text-white mt-2">{selectedRisk.title}</h3>
                </div>
                <button
                  onClick={() => setIsDetailDrawerOpen(false)}
                  className="p-1 rounded-lg bg-slate-800 text-slate-400 hover:text-white"
                >
                  <XCircle className="w-5 h-5" />
                </button>
              </div>

              {/* Assessment Metrics Bar */}
              <div className="grid grid-cols-3 gap-3 p-3 bg-slate-950 rounded-lg border border-slate-800 font-mono text-xs">
                <div>
                  <span className="text-slate-500 text-[10px] uppercase">Severity</span>
                  <p className="text-amber-400 font-bold text-sm mt-0.5">{SEVERITY_LABELS[selectedRisk.severity] || selectedRisk.severity}</p>
                </div>
                <div>
                  <span className="text-slate-500 text-[10px] uppercase">Likelihood</span>
                  <p className="text-blue-400 font-bold text-sm mt-0.5">{LIKELIHOOD_LABELS[selectedRisk.likelihood] || selectedRisk.likelihood}</p>
                </div>
                <div>
                  <span className="text-slate-500 text-[10px] uppercase">Detection Source</span>
                  <p className="text-slate-200 font-bold text-sm mt-0.5">{selectedRisk.detection_source}</p>
                </div>
              </div>

              {/* Risk Description */}
              <div className="space-y-1.5">
                <h4 className="text-xs font-mono uppercase tracking-wider text-slate-400">Detailed Risk Finding</h4>
                <p className="text-xs text-slate-200 leading-relaxed bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
                  {selectedRisk.description}
                </p>
              </div>

              {/* Institutional Recommendation */}
              <div className="space-y-1.5">
                <h4 className="text-xs font-mono uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                  <Shield className="w-3.5 h-3.5" />
                  Recommended Institutional Mitigation Strategy
                </h4>
                <div className="p-3 bg-emerald-950/30 border border-emerald-800/50 rounded-lg text-xs text-emerald-200 leading-relaxed">
                  {selectedRisk.recommendation || selectedRisk.mitigation_strategy || 'No specific mitigation strategy recorded.'}
                </div>
              </div>

              {/* Verifiable Evidence Citations */}
              <div className="space-y-2">
                <h4 className="text-xs font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-primary-400" />
                  Grounded Evidence Provenance ({selectedRisk.evidence_items?.length || 0})
                </h4>

                {selectedRisk.evidence_items && selectedRisk.evidence_items.length > 0 ? (
                  <div className="space-y-2">
                    {selectedRisk.evidence_items.map((ev, idx) => {
                      const cit = ev.citation;
                      return (
                        <div key={ev.id || idx} className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
                          <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
                            <span className="text-emerald-400 font-semibold">{cit?.document_name || 'Diligence Document'}</span>
                            <span>Page {cit?.page_number || 'N/A'}</span>
                          </div>
                          {cit?.exact_quote && (
                            <div className="p-2.5 rounded bg-slate-900 border-l-2 border-emerald-500 text-xs font-mono text-slate-200 italic">
                              &ldquo;{cit.exact_quote}&rdquo;
                            </div>
                          )}
                          {ev.relevance_explanation && (
                            <p className="text-[11px] text-slate-400">{ev.relevance_explanation}</p>
                          )}
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 font-mono italic">
                    No document chunk citations linked. This risk was entered manually.
                  </p>
                )}
              </div>
            </div>

            {/* Workflow Action Bar */}
            <div className="pt-4 border-t border-slate-800 flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-1.5 text-xs font-mono">
                <span className="text-slate-400">Change Status:</span>
                {['IDENTIFIED', 'REVIEWED', 'ACCEPTED', 'MITIGATED', 'REJECTED'].map((st) => (
                  <button
                    key={st}
                    type="button"
                    onClick={() => handleUpdateStatus(selectedRisk.id, st)}
                    className={`px-2 py-1 rounded text-[10px] font-mono border transition-all ${
                      selectedRisk.status === st
                        ? 'bg-emerald-600 text-white border-emerald-500 font-bold'
                        : 'bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700'
                    }`}
                  >
                    {st}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add Risk Item Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn">
          <div className="w-full max-w-xl bg-slate-900 border border-slate-800 rounded-xl shadow-2xl p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
                <Plus className="w-4 h-4 text-emerald-400" />
                Add Institutional Risk Item
              </h3>
              <button onClick={() => setIsAddModalOpen(false)} className="text-slate-400 hover:text-white">
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateRisk} className="space-y-4 text-xs font-mono">
              {/* Category */}
              <div>
                <label className="block text-slate-400 mb-1">Diligence Pillar</label>
                <select
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:outline-none focus:border-emerald-500"
                >
                  {Object.entries(CATEGORY_NAMES).map(([key, name]) => (
                    <option key={key} value={key}>
                      {name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Title */}
              <div>
                <label className="block text-slate-400 mb-1">Risk Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Top 3 Customers Account for 42% ARR"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:outline-none focus:border-emerald-500 font-sans text-xs"
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-slate-400 mb-1">Description & Evidence Summary</label>
                <textarea
                  required
                  rows={3}
                  placeholder="Detailed summary of the potential risk exposure..."
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:outline-none focus:border-emerald-500 font-sans text-xs"
                />
              </div>

              {/* Severity & Likelihood Controls */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Severity (1 to 5)</label>
                  <select
                    value={newSeverity}
                    onChange={(e) => setNewSeverity(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:outline-none focus:border-emerald-500"
                  >
                    {[1, 2, 3, 4, 5].map((val) => (
                      <option key={val} value={val}>
                        {SEVERITY_LABELS[val]}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-slate-400 mb-1">Likelihood (1 to 5)</label>
                  <select
                    value={newLikelihood}
                    onChange={(e) => setNewLikelihood(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:outline-none focus:border-emerald-500"
                  >
                    {[1, 2, 3, 4, 5].map((val) => (
                      <option key={val} value={val}>
                        {LIKELIHOOD_LABELS[val]}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Calculated Score Preview */}
              <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between text-xs font-mono">
                <span className="text-slate-400">Calculated Score & Level:</span>
                <span className="font-bold text-emerald-400">
                  {newSeverity * newLikelihood} / 25 ({newSeverity * newLikelihood >= 15 ? 'CRITICAL' : newSeverity * newLikelihood >= 10 ? 'HIGH' : newSeverity * newLikelihood >= 5 ? 'MODERATE' : 'LOW'})
                </span>
              </div>

              {/* Mitigation Strategy */}
              <div>
                <label className="block text-slate-400 mb-1">Recommended Mitigation Strategy (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. Structure 15% earnout retention escrow"
                  value={newMitigation}
                  onChange={(e) => setNewMitigation(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:outline-none focus:border-emerald-500 font-sans text-xs"
                />
              </div>

              {/* Submit Buttons */}
              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 transition-colors text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-semibold text-xs shadow transition-colors"
                >
                  {isSubmitting ? 'Saving...' : 'Add Risk to Register'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
