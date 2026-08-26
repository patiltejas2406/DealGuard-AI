'use client';

/**
 * DealGuard AI — Phase 10: Synergy Realization & Value Creation Intelligence Console
 */

import React, { useEffect, useState } from 'react';
import {
  Sparkles,
  DollarSign,
  TrendingUp,
  TrendingDown,
  Layers,
  FileCheck2,
  RefreshCw,
  Plus,
  Trash2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Building2,
  PieChart,
  BarChart3,
  Scale,
  Calendar,
  Clock,
  ArrowRight,
  Shield,
  ChevronRight,
  Sliders,
  Filter,
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { api } from '@/lib/api';
import {
  Deal,
  RealizationScheduleResponse,
  SynergyItem,
  SynergySummaryResponse,
  ValueBridgeResponse,
} from '@/types';

type ActiveTab = 'REGISTER' | 'WATERFALL' | 'SCHEDULE';

const SYNERGY_CATEGORIES: Record<string, string[]> = {
  REVENUE: [
    'CROSS_SELLING',
    'UPSELLING',
    'PRICING',
    'CUSTOMER_RETENTION',
    'GEOGRAPHIC_EXPANSION',
    'PRODUCT_BUNDLING',
    'CHANNEL_EXPANSION',
  ],
  COST: [
    'PROCUREMENT',
    'HEADCOUNT',
    'TECHNOLOGY',
    'INFRASTRUCTURE',
    'FACILITIES',
    'VENDOR_CONSOLIDATION',
    'SHARED_SERVICES',
    'PROCESS_AUTOMATION',
  ],
  OPERATIONAL: [
    'WORKING_CAPITAL',
    'CAPEX_OPTIMIZATION',
    'PROCESS_EFFICIENCY',
  ],
};

export default function SynergiesPage() {
  // Deals State
  const [deals, setDeals] = useState<Deal[]>([]);
  const [selectedDealId, setSelectedDealId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<ActiveTab>('REGISTER');

  // Synergy Data State
  const [synergies, setSynergies] = useState<SynergyItem[]>([]);
  const [summary, setSummary] = useState<SynergySummaryResponse | null>(null);
  const [valueBridge, setValueBridge] = useState<ValueBridgeResponse | null>(null);
  const [scheduleData, setScheduleData] = useState<RealizationScheduleResponse | null>(null);

  // Filters State
  const [filterType, setFilterType] = useState<string>('ALL');

  // Modals State
  const [isCreateOpen, setIsCreateOpen] = useState<boolean>(false);
  const [isLogActualOpen, setIsLogActualOpen] = useState<boolean>(false);
  const [activeSynergyForLog, setActiveSynergyForLog] = useState<SynergyItem | null>(null);

  // Create Form State
  const [newName, setNewName] = useState<string>('');
  const [newDescription, setNewDescription] = useState<string>('');
  const [newType, setNewType] = useState<'REVENUE' | 'COST' | 'OPERATIONAL'>('COST');
  const [newCategory, setNewCategory] = useState<string>('PROCUREMENT');
  const [newConfidence, setNewConfidence] = useState<'HIGH' | 'MEDIUM' | 'LOW'>('MEDIUM');
  const [newBaseline, setNewBaseline] = useState<number>(10000000);
  const [newTarget, setNewTarget] = useState<number>(7500000);
  const [newRealizationRate, setNewRealizationRate] = useState<number>(90);
  const [newProbability, setNewProbability] = useState<number>(85);
  const [newIntegrationCost, setNewIntegrationCost] = useState<number>(300000);
  const [newOwner, setNewOwner] = useState<string>('');

  // Log Actual Form State
  const [logPeriod, setLogPeriod] = useState<string>('Q1-2024');
  const [logPlanned, setLogPlanned] = useState<number>(500000);
  const [logActual, setLogActual] = useState<number>(550000);
  const [logNotes, setLogNotes] = useState<string>('');

  // UI Feedback State
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
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

  // 2. Load Synergy Data whenever deal changes
  useEffect(() => {
    if (!selectedDealId) return;
    loadAllSynergyData(selectedDealId);
  }, [selectedDealId]);

  async function loadAllSynergyData(dealId: string) {
    setIsLoading(true);
    setError(null);
    try {
      const [synList, sumRes, bridgeRes, schedRes] = await Promise.all([
        api.getSynergies(dealId),
        api.getSynergySummary(dealId),
        api.getSynergyValueBridge(dealId),
        api.getSynergyRealizationSchedule(dealId),
      ]);
      setSynergies(synList);
      setSummary(sumRes);
      setValueBridge(bridgeRes);
      setScheduleData(schedRes);
    } catch (err: any) {
      setError(err?.message || 'Failed to load value creation data.');
    } finally {
      setIsLoading(false);
    }
  }

  // 3. Create Synergy Handler
  async function handleCreateSynergy(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedDealId || !newName) {
      setError('Please provide a synergy name.');
      return;
    }
    setIsSubmitting(true);
    setError(null);
    try {
      await api.createSynergy(selectedDealId, {
        name: newName,
        description: newDescription,
        synergy_type: newType,
        category: newCategory,
        confidence: newConfidence,
        baseline_value: newBaseline,
        target_value: newTarget,
        realization_rate_pct: newRealizationRate,
        probability_pct: newProbability,
        one_time_integration_cost: newIntegrationCost,
        owner: newOwner,
      });
      setSuccessMessage(`Synergy '${newName}' registered.`);
      setIsCreateOpen(false);
      resetCreateForm();
      loadAllSynergyData(selectedDealId);
    } catch (err: any) {
      setError(err?.message || 'Failed to create synergy.');
    } finally {
      setIsSubmitting(false);
    }
  }

  function resetCreateForm() {
    setNewName('');
    setNewDescription('');
    setNewBaseline(10000000);
    setNewTarget(7500000);
    setNewRealizationRate(90);
    setNewProbability(85);
    setNewIntegrationCost(300000);
    setNewOwner('');
  }

  // 4. Update Synergy Status Handler
  async function handleStatusChange(synergyId: string, targetStatus: string) {
    if (!selectedDealId) return;
    try {
      await api.updateSynergyStatus(selectedDealId, synergyId, { status: targetStatus });
      setSuccessMessage('Synergy lifecycle status updated.');
      loadAllSynergyData(selectedDealId);
    } catch (err: any) {
      setError(err?.message || 'Status update failed.');
    }
  }

  // 5. Log Actual Realization Handler
  async function handleLogActual(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedDealId || !activeSynergyForLog) return;
    setIsSubmitting(true);
    try {
      await api.logSynergyActual(selectedDealId, activeSynergyForLog.id, {
        fiscal_period: logPeriod,
        planned_value: logPlanned,
        actual_value: logActual,
        notes: logNotes,
      });
      setSuccessMessage(`Performance logged for ${logPeriod}.`);
      setIsLogActualOpen(false);
      setActiveSynergyForLog(null);
      loadAllSynergyData(selectedDealId);
    } catch (err: any) {
      setError(err?.message || 'Failed to log realization.');
    } finally {
      setIsSubmitting(false);
    }
  }

  // 6. Delete Synergy
  async function handleDeleteSynergy(id: string) {
    if (!selectedDealId) return;
    try {
      await api.deleteSynergy(selectedDealId, id);
      setSuccessMessage('Synergy opportunity deleted.');
      loadAllSynergyData(selectedDealId);
    } catch (err: any) {
      setError(err?.message || 'Delete failed.');
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'REALIZED':
        return <Badge variant="success" size="sm">REALIZED</Badge>;
      case 'PARTIALLY_REALIZED':
        return <Badge variant="info" size="sm">PARTIALLY REALIZED</Badge>;
      case 'IN_PROGRESS':
        return <Badge variant="info" size="sm">IN PROGRESS</Badge>;
      case 'PLANNED':
        return <Badge variant="warning" size="sm">PLANNED</Badge>;
      case 'VALIDATED':
        return <Badge variant="default" size="sm">VALIDATED</Badge>;
      case 'AT_RISK':
        return <Badge variant="danger" size="sm">AT RISK</Badge>;
      case 'ABANDONED':
        return <Badge variant="danger" size="sm">ABANDONED</Badge>;
      default:
        return <Badge variant="default" size="sm">{status}</Badge>;
    }
  };

  const filteredSynergies = synergies.filter((s) =>
    filterType === 'ALL' ? true : s.synergy_type === filterType
  );

  return (
    <div className="min-h-screen bg-surface-base text-slate-100 p-6 space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 border-b border-slate-800 pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2 font-mono">
                Synergy Realization & Value Creation
                <Badge variant="success" size="sm">Phase 10 Engine v1.0</Badge>
              </h1>
              <p className="text-xs text-slate-400">
                Deterministic Synergy Waterfall Bridges, 5-Year Realization Curves & Closed-Loop Planned vs. Actual Tracking
              </p>
            </div>
          </div>
        </div>

        {/* Workspace Selector & Actions */}
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
            onClick={() => setIsCreateOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow font-mono transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            Add Synergy
          </button>

          <button
            type="button"
            onClick={() => selectedDealId && loadAllSynergyData(selectedDealId)}
            className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Summary KPI Cards Grid */}
      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3 font-mono">
          <Card className="p-3.5 bg-slate-900/90 border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-500 uppercase">Total Potential Value</span>
            <p className="text-xl font-bold text-white">
              ${(summary.total_potential_annual_value / 1e6).toFixed(1)}M
            </p>
            <span className="text-[10px] text-slate-400">{summary.total_opportunities_count} Opportunities</span>
          </Card>

          <Card className="p-3.5 bg-slate-900/90 border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-500 uppercase">Expected Annual Synergy</span>
            <p className="text-xl font-bold text-emerald-400">
              ${(summary.total_expected_annual_value / 1e6).toFixed(1)}M
            </p>
            <span className="text-[10px] text-slate-400">Risk-Weighted</span>
          </Card>

          <Card className="p-3.5 bg-slate-900/90 border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-500 uppercase">Realized Annual Value</span>
            <p className="text-xl font-bold text-blue-400">
              ${(summary.total_realized_annual_value / 1e6).toFixed(1)}M
            </p>
            <span className="text-[10px] text-slate-400">Captured in P&L</span>
          </Card>

          <Card className="p-3.5 bg-slate-900/90 border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-500 uppercase">One-Time Integration</span>
            <p className="text-xl font-bold text-amber-400">
              ${(summary.total_one_time_integration_cost / 1e6).toFixed(1)}M
            </p>
            <span className="text-[10px] text-slate-400">Upfront Investment</span>
          </Card>

          <Card className="p-3.5 bg-slate-900/90 border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-500 uppercase">Net Annual Value</span>
            <p className="text-xl font-bold text-white">
              ${(summary.net_annual_expected_value / 1e6).toFixed(1)}M
            </p>
            <span className="text-[10px] text-slate-400">Expected - Amortized Cost</span>
          </Card>

          <Card className="p-3.5 bg-slate-900/90 border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-500 uppercase">Value Capture Rate</span>
            <p className="text-xl font-bold text-emerald-400">
              {summary.overall_value_capture_rate_pct}%
            </p>
            <div className="w-full h-1 bg-slate-950 rounded-full overflow-hidden mt-1">
              <div
                className="h-full bg-emerald-500 rounded-full"
                style={{ width: `${Math.min(100, summary.overall_value_capture_rate_pct)}%` }}
              />
            </div>
          </Card>
        </div>
      )}

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2 text-xs font-mono">
        <button
          onClick={() => setActiveTab('REGISTER')}
          className={`px-3.5 py-1.5 rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === 'REGISTER'
              ? 'bg-emerald-600 text-white font-bold shadow'
              : 'text-slate-400 hover:text-white hover:bg-slate-900'
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          Synergy Register ({synergies.length})
        </button>
        <button
          onClick={() => setActiveTab('WATERFALL')}
          className={`px-3.5 py-1.5 rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === 'WATERFALL'
              ? 'bg-emerald-600 text-white font-bold shadow'
              : 'text-slate-400 hover:text-white hover:bg-slate-900'
          }`}
        >
          <BarChart3 className="w-3.5 h-3.5" />
          Value Creation Waterfall Bridge
        </button>
        <button
          onClick={() => setActiveTab('SCHEDULE')}
          className={`px-3.5 py-1.5 rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === 'SCHEDULE'
              ? 'bg-emerald-600 text-white font-bold shadow'
              : 'text-slate-400 hover:text-white hover:bg-slate-900'
          }`}
        >
          <Calendar className="w-3.5 h-3.5" />
          5-Year Realization Phasing
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

      {/* TAB 1: SYNERGY REGISTER */}
      {activeTab === 'REGISTER' && (
        <Card className="p-5 bg-slate-900/90 border-slate-800 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-slate-400">Filter Type:</span>
              {['ALL', 'COST', 'REVENUE', 'OPERATIONAL'].map((t) => (
                <button
                  key={t}
                  onClick={() => setFilterType(t)}
                  className={`px-2.5 py-1 rounded text-xs font-mono transition-colors ${
                    filterType === t
                      ? 'bg-emerald-600 text-white font-bold'
                      : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>

            <span className="text-xs font-mono text-slate-400">
              Showing {filteredSynergies.length} of {synergies.length}
            </span>
          </div>

          {filteredSynergies.length === 0 ? (
            <div className="py-12 text-center text-xs font-mono text-slate-500 space-y-2">
              <Sparkles className="w-8 h-8 mx-auto text-slate-600" />
              <p>No synergy opportunities found for this filter. Click &apos;Add Synergy&apos; to register one.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="text-[10px] uppercase text-slate-500 border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Opportunity</th>
                    <th className="py-2.5 px-3">Type / Category</th>
                    <th className="py-2.5 px-3">Potential</th>
                    <th className="py-2.5 px-3">Expected</th>
                    <th className="py-2.5 px-3">Realized (Actual)</th>
                    <th className="py-2.5 px-3">Capture %</th>
                    <th className="py-2.5 px-3">Confidence</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/40">
                  {filteredSynergies.map((syn) => (
                    <tr key={syn.id} className="hover:bg-slate-800/30">
                      <td className="py-3 px-3">
                        <div className="font-bold text-white">{syn.name}</div>
                        {syn.owner && <span className="text-[10px] text-slate-500">Lead: {syn.owner}</span>}
                      </td>
                      <td className="py-3 px-3">
                        <div className="text-slate-200">{syn.synergy_type}</div>
                        <div className="text-[10px] text-slate-500">{syn.category}</div>
                      </td>
                      <td className="py-3 px-3 font-bold text-white">
                        ${(syn.potential_annual_value / 1e6).toFixed(2)}M
                      </td>
                      <td className="py-3 px-3 font-bold text-emerald-400">
                        ${(syn.expected_annual_value / 1e6).toFixed(2)}M
                        <div className="text-[10px] text-slate-500 font-normal">
                          {syn.realization_rate_pct}% real. × {syn.probability_pct}% prob.
                        </div>
                      </td>
                      <td className="py-3 px-3 font-bold text-blue-400">
                        ${(syn.realized_annual_value / 1e6).toFixed(2)}M
                      </td>
                      <td className="py-3 px-3">
                        <span className="font-bold text-slate-200">{syn.value_capture_rate_pct}%</span>
                        <div className="w-16 h-1 bg-slate-950 rounded-full overflow-hidden mt-1">
                          <div
                            className="h-full bg-blue-500 rounded-full"
                            style={{ width: `${Math.min(100, syn.value_capture_rate_pct)}%` }}
                          />
                        </div>
                      </td>
                      <td className="py-3 px-3">
                        <span
                          className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                            syn.confidence === 'HIGH'
                              ? 'bg-emerald-950 text-emerald-400 border border-emerald-800/60'
                              : syn.confidence === 'MEDIUM'
                              ? 'bg-amber-950 text-amber-400 border border-amber-800/60'
                              : 'bg-slate-800 text-slate-400'
                          }`}
                        >
                          {syn.confidence}
                        </span>
                      </td>
                      <td className="py-3 px-3">
                        <select
                          value={syn.status}
                          onChange={(e) => handleStatusChange(syn.id, e.target.value)}
                          className="bg-slate-950 border border-slate-800 rounded px-1.5 py-0.5 text-[10px] text-slate-300 focus:outline-none cursor-pointer"
                        >
                          <option value="IDENTIFIED">IDENTIFIED</option>
                          <option value="VALIDATED">VALIDATED</option>
                          <option value="PLANNED">PLANNED</option>
                          <option value="IN_PROGRESS">IN_PROGRESS</option>
                          <option value="PARTIALLY_REALIZED">PARTIALLY_REALIZED</option>
                          <option value="REALIZED">REALIZED</option>
                          <option value="AT_RISK">AT_RISK</option>
                          <option value="ABANDONED">ABANDONED</option>
                        </select>
                      </td>
                      <td className="py-3 px-3 text-right space-x-1.5">
                        <button
                          onClick={() => {
                            setActiveSynergyForLog(syn);
                            setIsLogActualOpen(true);
                          }}
                          className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-[10px] text-blue-300 font-semibold"
                          title="Log Performance"
                        >
                          Log Actual
                        </button>
                        <button
                          onClick={() => handleDeleteSynergy(syn.id)}
                          className="p-1 rounded hover:bg-rose-950 text-slate-500 hover:text-rose-400 transition-colors"
                          title="Delete"
                        >
                          <Trash2 className="w-3.5 h-3.5 inline" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {/* TAB 2: WATERFALL BRIDGE */}
      {activeTab === 'WATERFALL' && valueBridge && (
        <div className="space-y-5">
          <Card className="p-5 bg-slate-900/90 border-slate-800 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h2 className="text-sm font-semibold text-white font-mono flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-emerald-400" />
                  Value Creation Waterfall Bridge
                </h2>
                <p className="text-xs text-slate-400 font-mono">
                  Intrinsic Standalone Valuation + Discounted Net Synergies - Integration Drag = Synergy-Adjusted EV
                </p>
              </div>

              {/* Decision Score Impact Badge */}
              <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 font-mono text-xs text-right">
                <span className="text-slate-500 text-[10px] uppercase block">Decision Score Accretion</span>
                <span className="text-white font-bold">
                  {valueBridge.base_decision_score.toFixed(1)} ({valueBridge.base_decision_band}) →{' '}
                  <span className="text-emerald-400">
                    {valueBridge.synergy_adjusted_decision_score.toFixed(1)} ({valueBridge.synergy_adjusted_decision_band})
                  </span>
                </span>
                <span className="text-emerald-400 font-bold ml-1.5">
                  (+{valueBridge.score_delta.toFixed(1)} pts)
                </span>
              </div>
            </div>

            {/* Waterfall Visual Cards */}
            <div className="grid grid-cols-1 md:grid-cols-6 gap-3 font-mono text-xs">
              {valueBridge.waterfall_steps.map((step, idx) => (
                <div
                  key={idx}
                  className={`p-3.5 rounded-lg border flex flex-col justify-between space-y-2 ${
                    step.type === 'BASE'
                      ? 'bg-slate-950 border-slate-800 text-slate-200'
                      : step.type === 'ADDITION'
                      ? 'bg-emerald-950/30 border-emerald-800/80 text-emerald-300'
                      : step.type === 'SUBTRACTION'
                      ? 'bg-rose-950/30 border-rose-800/80 text-rose-300'
                      : 'bg-blue-950/40 border-blue-800/80 text-blue-200 font-bold'
                  }`}
                >
                  <span className="text-[10px] uppercase opacity-80">{step.label}</span>
                  <p className="text-lg font-bold">
                    {step.amount >= 0 ? `$${(step.amount / 1e6).toFixed(1)}M` : `-$${(Math.abs(step.amount) / 1e6).toFixed(1)}M`}
                  </p>
                </div>
              ))}
            </div>

            {/* Net Value Creation Callout */}
            <div className="p-4 rounded-lg bg-emerald-950/30 border border-emerald-800/60 font-mono text-xs flex items-center justify-between">
              <div>
                <span className="text-emerald-400 font-bold uppercase">Net Risk-Adjusted Value Created:</span>
                <span className="text-white font-bold ml-2 text-base">
                  +${(valueBridge.net_value_created / 1e6).toFixed(1)}M
                </span>
                <span className="text-emerald-400 ml-1.5">
                  (+{valueBridge.value_creation_pct.toFixed(1)}% vs. Standalone)
                </span>
              </div>
              <span className="text-slate-400 text-[10px]">
                Discounted at 10.0% WACC over 5-Year Horizon
              </span>
            </div>
          </Card>
        </div>
      )}

      {/* TAB 3: 5-YEAR REALIZATION PHASING */}
      {activeTab === 'SCHEDULE' && scheduleData && (
        <Card className="p-5 bg-slate-900/90 border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h2 className="text-sm font-semibold text-white font-mono flex items-center gap-2">
                <Calendar className="w-4 h-4 text-emerald-400" />
                5-Year Phased Synergy Trajectory
              </h2>
              <p className="text-xs text-slate-400 font-mono">
                Projected annual revenue and cost synergy realization ramps, EBITDA accretion, and net cash flow impact.
              </p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-center text-xs font-mono border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-[10px] text-slate-500 bg-slate-950 uppercase">
                  <th className="py-2.5 px-3 text-left">Period</th>
                  <th className="py-2.5 px-3">Expected Revenue Synergy</th>
                  <th className="py-2.5 px-3">Expected Cost Synergy</th>
                  <th className="py-2.5 px-3">Total Expected Synergy</th>
                  <th className="py-2.5 px-3">Integration Cost Drag</th>
                  <th className="py-2.5 px-3 text-emerald-400">EBITDA Impact</th>
                  <th className="py-2.5 px-3 text-white">Net Cash Flow Impact</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40 text-slate-200">
                {scheduleData.schedule.map((row) => (
                  <tr key={row.year} className="hover:bg-slate-800/30">
                    <td className="py-3 px-3 font-bold text-white text-left">{row.period}</td>
                    <td className="py-3 px-3">${(row.expected_revenue_synergy / 1e6).toFixed(2)}M</td>
                    <td className="py-3 px-3">${(row.expected_cost_synergy / 1e6).toFixed(2)}M</td>
                    <td className="py-3 px-3 font-bold text-slate-100">${(row.total_expected / 1e6).toFixed(2)}M</td>
                    <td className="py-3 px-3 text-rose-400">-${(row.integration_cost / 1e6).toFixed(2)}M</td>
                    <td className="py-3 px-3 font-bold text-emerald-400">${(row.ebitda_impact / 1e6).toFixed(2)}M</td>
                    <td className="py-3 px-3 font-bold text-white">${(row.net_cash_flow_impact / 1e6).toFixed(2)}M</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* CREATE SYNERGY MODAL */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn font-mono text-xs">
          <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-xl shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white">Register Synergy Opportunity</h3>
              <button onClick={() => setIsCreateOpen(false)} className="text-slate-400 hover:text-white">
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateSynergy} className="space-y-3">
              <div>
                <label className="text-[10px] uppercase text-slate-400 block mb-1">Opportunity Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. ERP License Consolidation"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] uppercase text-slate-400 block mb-1">Synergy Type</label>
                  <select
                    value={newType}
                    onChange={(e: any) => {
                      setNewType(e.target.value);
                      setNewCategory(SYNERGY_CATEGORIES[e.target.value][0]);
                    }}
                    className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-200"
                  >
                    <option value="COST">Cost Synergy</option>
                    <option value="REVENUE">Revenue Synergy</option>
                    <option value="OPERATIONAL">Operational Improvement</option>
                  </select>
                </div>

                <div>
                  <label className="text-[10px] uppercase text-slate-400 block mb-1">Category</label>
                  <select
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-200"
                  >
                    {SYNERGY_CATEGORIES[newType].map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] uppercase text-slate-400 block mb-1">Baseline Spend / Rev ($)</label>
                  <input
                    type="number"
                    value={newBaseline}
                    onChange={(e) => setNewBaseline(parseFloat(e.target.value) || 0)}
                    className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-200"
                  />
                </div>
                <div>
                  <label className="text-[10px] uppercase text-slate-400 block mb-1">Target Spend / Rev ($) *</label>
                  <input
                    type="number"
                    required
                    value={newTarget}
                    onChange={(e) => setNewTarget(parseFloat(e.target.value) || 0)}
                    className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-200"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-[10px] uppercase text-slate-400 block mb-1">Realization Rate (%)</label>
                  <input
                    type="number"
                    value={newRealizationRate}
                    onChange={(e) => setNewRealizationRate(parseFloat(e.target.value) || 0)}
                    className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-200"
                  />
                </div>
                <div>
                  <label className="text-[10px] uppercase text-slate-400 block mb-1">Probability (%)</label>
                  <input
                    type="number"
                    value={newProbability}
                    onChange={(e) => setNewProbability(parseFloat(e.target.value) || 0)}
                    className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-200"
                  />
                </div>
                <div>
                  <label className="text-[10px] uppercase text-slate-400 block mb-1">Integration Cost ($)</label>
                  <input
                    type="number"
                    value={newIntegrationCost}
                    onChange={(e) => setNewIntegrationCost(parseFloat(e.target.value) || 0)}
                    className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-200"
                  />
                </div>
              </div>

              <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsCreateOpen(false)}
                  className="px-3.5 py-1.5 rounded-lg bg-slate-800 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold"
                >
                  {isSubmitting ? 'Saving...' : 'Register Opportunity'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* LOG ACTUAL MODAL */}
      {isLogActualOpen && activeSynergyForLog && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn font-mono text-xs">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-xl shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white">Log Performance: {activeSynergyForLog.name}</h3>
              <button onClick={() => setIsLogActualOpen(false)} className="text-slate-400 hover:text-white">
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleLogActual} className="space-y-3">
              <div>
                <label className="text-[10px] uppercase text-slate-400 block mb-1">Fiscal Period</label>
                <input
                  type="text"
                  value={logPeriod}
                  onChange={(e) => setLogPeriod(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] uppercase text-slate-400 block mb-1">Planned Target ($)</label>
                  <input
                    type="number"
                    value={logPlanned}
                    onChange={(e) => setLogPlanned(parseFloat(e.target.value) || 0)}
                    className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-200"
                  />
                </div>
                <div>
                  <label className="text-[10px] uppercase text-slate-400 block mb-1">Actual Captured ($) *</label>
                  <input
                    type="number"
                    required
                    value={logActual}
                    onChange={(e) => setLogActual(parseFloat(e.target.value) || 0)}
                    className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-emerald-400 font-bold"
                  />
                </div>
              </div>

              <div>
                <label className="text-[10px] uppercase text-slate-400 block mb-1">Variance / Commentary</label>
                <textarea
                  rows={2}
                  value={logNotes}
                  onChange={(e) => setLogNotes(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-200 focus:outline-none"
                  placeholder="Notes on execution timing, rate variance..."
                />
              </div>

              <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsLogActualOpen(false)}
                  className="px-3.5 py-1.5 rounded-lg bg-slate-800 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold"
                >
                  {isSubmitting ? 'Logging...' : 'Save Actual'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
