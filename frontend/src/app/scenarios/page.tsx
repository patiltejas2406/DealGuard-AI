'use client';

/**
 * DealGuard AI — Phase 9: What-If Deal Simulation & Monte Carlo Scenario Intelligence Lab
 */

import React, { useEffect, useState } from 'react';
import {
  Sliders,
  TrendingUp,
  AlertTriangle,
  DollarSign,
  Shield,
  RefreshCw,
  Sparkles,
  PieChart,
  Layers,
  Save,
  Trash2,
  Play,
  CheckCircle2,
  XCircle,
  Building2,
  BarChart3,
  Scale,
  ArrowRight,
  Info,
  ChevronRight,
  Table,
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { api } from '@/lib/api';
import {
  Deal,
  MonteCarloResponseItem,
  ScenarioItem,
  SensitivityMatrixResponse,
} from '@/types';

type ActiveTab = 'WHAT_IF' | 'SENSITIVITY' | 'MONTE_CARLO' | 'COMPARISON';

const DEFAULT_ASSUMPTIONS: Record<string, number> = {
  revenue_growth_pct: 0.0,
  ebitda_margin_pct: 25.0,
  wacc_pct: 10.0,
  terminal_growth_rate_pct: 2.5,
  purchase_price: 70000000.0,
  churn_rate_pct: 5.0,
  customer_concentration_pct: 15.0,
  synergy_value: 0.0,
  synergy_realization_rate_pct: 100.0,
  integration_cost: 0.0,
};

export default function ScenariosPage() {
  // Deals State
  const [deals, setDeals] = useState<Deal[]>([]);
  const [selectedDealId, setSelectedDealId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<ActiveTab>('WHAT_IF');

  // What-If State
  const [assumptions, setAssumptions] = useState<Record<string, number>>(DEFAULT_ASSUMPTIONS);
  const [whatIfResult, setWhatIfResult] = useState<any | null>(null);
  const [savedScenarios, setSavedScenarios] = useState<ScenarioItem[]>([]);
  const [scenarioName, setScenarioName] = useState<string>('');
  const [scenarioType, setScenarioType] = useState<string>('WHAT_IF');

  // Sensitivity State
  const [rowVar, setRowVar] = useState<string>('revenue_growth_pct');
  const [colVar, setColVar] = useState<string>('ebitda_margin_pct');
  const [sensitivityResult, setSensitivityResult] = useState<SensitivityMatrixResponse | null>(null);

  // Monte Carlo State
  const [mcIterations, setMcIterations] = useState<number>(1000);
  const [mcSeed, setMcSeed] = useState<number>(42);
  const [mcResult, setMcResult] = useState<MonteCarloResponseItem | null>(null);

  // UI Feedback State
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isComputing, setIsComputing] = useState<boolean>(false);
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

  // 2. Load Scenarios and Compute Initial Base What-If whenever deal changes
  useEffect(() => {
    if (!selectedDealId) return;
    loadDealScenarios(selectedDealId);
    runLiveWhatIf(selectedDealId, assumptions);
  }, [selectedDealId]);

  async function loadDealScenarios(dealId: string) {
    setIsLoading(true);
    try {
      const list = await api.getScenarios(dealId);
      setSavedScenarios(list);
    } catch (err: any) {
      console.error('Failed to load scenarios:', err);
    } finally {
      setIsLoading(false);
    }
  }

  // 3. Live What-If Evaluation
  async function runLiveWhatIf(dealId: string, currentAssumptions: Record<string, number>) {
    try {
      const res = await api.runSensitivity(dealId, {
        variable_name: 'revenue_growth_pct',
        steps: [currentAssumptions.revenue_growth_pct || 0.0],
      });
      // Also get initial What-If evaluation by creating a mock or test endpoint
      const preview = await api.createScenario(dealId, {
        name: 'Live Scratch Preview',
        scenario_type: 'WHAT_IF',
        assumptions: currentAssumptions,
      });
      setWhatIfResult(preview.results);
      // Clean up scratch scenario
      if (preview.id) {
        await api.deleteScenario(dealId, preview.id);
      }
    } catch (err: any) {
      // Fallback
    }
  }

  function handleAssumptionChange(field: string, val: number) {
    const updated = { ...assumptions, [field]: val };
    setAssumptions(updated);
    if (selectedDealId) {
      runLiveWhatIf(selectedDealId, updated);
    }
  }

  function resetAssumptions() {
    setAssumptions(DEFAULT_ASSUMPTIONS);
    if (selectedDealId) {
      runLiveWhatIf(selectedDealId, DEFAULT_ASSUMPTIONS);
    }
  }

  // 4. Save Persistent Scenario
  async function handleSaveScenario() {
    if (!selectedDealId || !scenarioName) {
      setError('Please enter a scenario name.');
      return;
    }
    setIsComputing(true);
    setError(null);
    try {
      const created = await api.createScenario(selectedDealId, {
        name: scenarioName,
        scenario_type: scenarioType,
        assumptions: assumptions,
      });
      setSavedScenarios([created, ...savedScenarios]);
      setSuccessMessage(`Scenario '${scenarioName}' successfully saved.`);
      setScenarioName('');
    } catch (err: any) {
      setError(err?.message || 'Failed to save scenario.');
    } finally {
      setIsComputing(false);
    }
  }

  async function handleDeleteScenario(id: string) {
    if (!selectedDealId) return;
    try {
      await api.deleteScenario(selectedDealId, id);
      setSavedScenarios(savedScenarios.filter((s) => s.id !== id));
      setSuccessMessage('Scenario deleted.');
    } catch (err: any) {
      setError(err?.message || 'Failed to delete scenario.');
    }
  }

  // 5. Run 2D Sensitivity Matrix
  async function handleRunSensitivity() {
    if (!selectedDealId) return;
    setIsComputing(true);
    setError(null);
    try {
      const res = await api.runSensitivity(selectedDealId, {
        row_variable: rowVar,
        row_steps: [-15.0, -10.0, -5.0, 0.0, 5.0, 10.0, 15.0],
        col_variable: colVar,
        col_steps: [15.0, 20.0, 25.0, 30.0, 35.0],
      });
      setSensitivityResult(res);
      setSuccessMessage('2D Sensitivity matrix and tipping-point inflection thresholds computed.');
    } catch (err: any) {
      setError(err?.message || 'Sensitivity calculation failed.');
    } finally {
      setIsComputing(false);
    }
  }

  // 6. Run Monte Carlo Simulation
  async function handleRunMonteCarlo() {
    if (!selectedDealId) return;
    setIsComputing(true);
    setError(null);
    try {
      const res = await api.runMonteCarlo(selectedDealId, {
        iterations: mcIterations,
        random_seed: mcSeed,
        variable_distributions: {
          revenue_growth_pct: {
            distribution_type: 'TRIANGULAR',
            min_val: -15.0,
            mode_val: 5.0,
            max_val: 20.0,
          },
          ebitda_margin_pct: {
            distribution_type: 'NORMAL',
            mean: 26.0,
            std_dev: 3.5,
          },
          wacc_pct: {
            distribution_type: 'TRIANGULAR',
            min_val: 8.0,
            mode_val: 10.0,
            max_val: 13.0,
          },
          churn_rate_pct: {
            distribution_type: 'TRIANGULAR',
            min_val: 2.0,
            mode_val: 6.0,
            max_val: 15.0,
          },
        },
      });
      setMcResult(res);
      setSuccessMessage(`Monte Carlo simulation (${res.iterations_completed} iterations) completed with seed ${mcSeed}.`);
    } catch (err: any) {
      setError(err?.message || 'Monte Carlo simulation failed.');
    } finally {
      setIsComputing(false);
    }
  }

  const getBandBadge = (band: string) => {
    switch (band) {
      case 'STRONG':
        return <Badge variant="success" size="sm">STRONG</Badge>;
      case 'FAVORABLE':
        return <Badge variant="info" size="sm">FAVORABLE</Badge>;
      case 'CAUTION':
        return <Badge variant="warning" size="sm">CAUTION</Badge>;
      case 'HIGH_RISK':
        return <Badge variant="danger" size="sm">HIGH RISK</Badge>;
      case 'AVOID':
        return <Badge variant="danger" size="sm">AVOID</Badge>;
      default:
        return <Badge variant="default" size="sm">{band}</Badge>;
    }
  };

  return (
    <div className="min-h-screen bg-surface-base text-slate-100 p-6 space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 border-b border-slate-800 pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <Sliders className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2 font-mono">
                DealGuard Scenario Lab
                <Badge variant="success" size="sm">Phase 9 Engine v1.0</Badge>
              </h1>
              <p className="text-xs text-slate-400">
                Deterministic What-If Simulation, 2D Sensitivity Heatmaps & Statistical Monte Carlo Uncertainty Analysis
              </p>
            </div>
          </div>
        </div>

        {/* Workspace Selector & Tab Navigation */}
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
            onClick={() => selectedDealId && loadDealScenarios(selectedDealId)}
            className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
            title="Refresh Scenarios"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2 text-xs font-mono">
        <button
          onClick={() => setActiveTab('WHAT_IF')}
          className={`px-3.5 py-1.5 rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === 'WHAT_IF'
              ? 'bg-emerald-600 text-white font-bold shadow'
              : 'text-slate-400 hover:text-white hover:bg-slate-900'
          }`}
        >
          <Sliders className="w-3.5 h-3.5" />
          What-If Builder
        </button>
        <button
          onClick={() => setActiveTab('SENSITIVITY')}
          className={`px-3.5 py-1.5 rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === 'SENSITIVITY'
              ? 'bg-emerald-600 text-white font-bold shadow'
              : 'text-slate-400 hover:text-white hover:bg-slate-900'
          }`}
        >
          <BarChart3 className="w-3.5 h-3.5" />
          2D Sensitivity Matrix
        </button>
        <button
          onClick={() => setActiveTab('MONTE_CARLO')}
          className={`px-3.5 py-1.5 rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === 'MONTE_CARLO'
              ? 'bg-emerald-600 text-white font-bold shadow'
              : 'text-slate-400 hover:text-white hover:bg-slate-900'
          }`}
        >
          <PieChart className="w-3.5 h-3.5" />
          Monte Carlo Simulation
        </button>
        <button
          onClick={() => setActiveTab('COMPARISON')}
          className={`px-3.5 py-1.5 rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === 'COMPARISON'
              ? 'bg-emerald-600 text-white font-bold shadow'
              : 'text-slate-400 hover:text-white hover:bg-slate-900'
          }`}
        >
          <Table className="w-3.5 h-3.5" />
          Scenario Comparison ({savedScenarios.length})
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

      {/* TAB 1: WHAT-IF BUILDER */}
      {activeTab === 'WHAT_IF' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Assumption Controls Column */}
          <Card className="lg:col-span-6 p-5 bg-slate-900/90 border-slate-800 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-sm font-semibold text-white font-mono flex items-center gap-2">
                <Sliders className="w-4 h-4 text-emerald-400" />
                Scenario Assumption Controls
              </h2>
              <button
                onClick={resetAssumptions}
                className="text-[11px] font-mono text-slate-400 hover:text-white underline"
              >
                Reset to Base Case
              </button>
            </div>

            <div className="space-y-4 text-xs font-mono">
              {/* Revenue Growth Slider */}
              <div className="space-y-1.5 p-3 rounded-lg bg-slate-950 border border-slate-850">
                <div className="flex justify-between">
                  <span className="text-slate-300">Revenue Growth Rate (%):</span>
                  <span className="text-emerald-400 font-bold">{assumptions.revenue_growth_pct > 0 ? `+${assumptions.revenue_growth_pct}%` : `${assumptions.revenue_growth_pct}%`}</span>
                </div>
                <input
                  type="range"
                  min="-50"
                  max="50"
                  step="1"
                  value={assumptions.revenue_growth_pct}
                  onChange={(e) => handleAssumptionChange('revenue_growth_pct', parseFloat(e.target.value))}
                  className="w-full accent-emerald-500 cursor-pointer"
                />
              </div>

              {/* EBITDA Margin Slider */}
              <div className="space-y-1.5 p-3 rounded-lg bg-slate-950 border border-slate-850">
                <div className="flex justify-between">
                  <span className="text-slate-300">Target EBITDA Margin (%):</span>
                  <span className="text-emerald-400 font-bold">{assumptions.ebitda_margin_pct}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="60"
                  step="1"
                  value={assumptions.ebitda_margin_pct}
                  onChange={(e) => handleAssumptionChange('ebitda_margin_pct', parseFloat(e.target.value))}
                  className="w-full accent-emerald-500 cursor-pointer"
                />
              </div>

              {/* Discount Rate / WACC */}
              <div className="space-y-1.5 p-3 rounded-lg bg-slate-950 border border-slate-850">
                <div className="flex justify-between">
                  <span className="text-slate-300">Discount Rate / WACC (%):</span>
                  <span className="text-white font-bold">{assumptions.wacc_pct}%</span>
                </div>
                <input
                  type="range"
                  min="6"
                  max="20"
                  step="0.5"
                  value={assumptions.wacc_pct}
                  onChange={(e) => handleAssumptionChange('wacc_pct', parseFloat(e.target.value))}
                  className="w-full accent-emerald-500 cursor-pointer"
                />
              </div>

              {/* Customer Churn Spike */}
              <div className="space-y-1.5 p-3 rounded-lg bg-slate-950 border border-slate-850">
                <div className="flex justify-between">
                  <span className="text-slate-300">Customer Churn Rate (%):</span>
                  <span className="text-amber-400 font-bold">{assumptions.churn_rate_pct}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="40"
                  step="1"
                  value={assumptions.churn_rate_pct}
                  onChange={(e) => handleAssumptionChange('churn_rate_pct', parseFloat(e.target.value))}
                  className="w-full accent-amber-500 cursor-pointer"
                />
              </div>

              {/* Purchase Price (Target EV) */}
              <div className="space-y-1.5 p-3 rounded-lg bg-slate-950 border border-slate-850">
                <div className="flex justify-between">
                  <span className="text-slate-300">Purchase Price / Target EV:</span>
                  <span className="text-white font-bold">${(assumptions.purchase_price / 1e6).toFixed(1)}M</span>
                </div>
                <input
                  type="range"
                  min="20000000"
                  max="150000000"
                  step="5000000"
                  value={assumptions.purchase_price}
                  onChange={(e) => handleAssumptionChange('purchase_price', parseFloat(e.target.value))}
                  className="w-full accent-emerald-500 cursor-pointer"
                />
              </div>
            </div>

            {/* Save Scenario Form */}
            <div className="pt-4 border-t border-slate-800 space-y-3">
              <span className="text-[11px] font-mono uppercase text-slate-400">Save Scenario to Deal Ledger</span>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  placeholder="e.g. Bear Case Churn Shock"
                  value={scenarioName}
                  onChange={(e) => setScenarioName(e.target.value)}
                  className="flex-1 px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-white focus:outline-none focus:border-emerald-500"
                />
                <select
                  value={scenarioType}
                  onChange={(e) => setScenarioType(e.target.value)}
                  className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-slate-300 focus:outline-none"
                >
                  <option value="WHAT_IF">What-If</option>
                  <option value="DOWNSIDE">Downside</option>
                  <option value="UPSIDE">Upside</option>
                  <option value="STRESS_TEST">Stress Test</option>
                </select>
                <button
                  type="button"
                  onClick={handleSaveScenario}
                  disabled={isComputing || !scenarioName}
                  className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-lg text-xs font-mono font-semibold flex items-center gap-1.5 transition-colors"
                >
                  <Save className="w-3.5 h-3.5" />
                  Save
                </button>
              </div>
            </div>
          </Card>

          {/* Live Outcome Comparison Column */}
          <div className="lg:col-span-6 space-y-4">
            {whatIfResult ? (
              <>
                {/* Live Deltas Hero Card */}
                <Card className="p-5 bg-slate-900/90 border-slate-800 space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                    <span className="text-xs font-mono uppercase tracking-wider text-slate-400">Live Outcome Trajectory</span>
                    <span className="text-[11px] font-mono text-emerald-400">Deterministic Lineage</span>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    {/* Implied EV Comparison */}
                    <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1 font-mono">
                      <span className="text-[10px] text-slate-500 uppercase">Implied Enterprise Value</span>
                      <div className="flex items-baseline gap-2">
                        <span className="text-xl font-bold text-white">
                          ${(whatIfResult.scenario_case.implied_ev / 1e6).toFixed(1)}M
                        </span>
                        <span
                          className={`text-xs font-bold ${
                            whatIfResult.deltas.valuation_delta_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'
                          }`}
                        >
                          {whatIfResult.deltas.valuation_delta_pct >= 0 ? '+' : ''}
                          {whatIfResult.deltas.valuation_delta_pct.toFixed(1)}%
                        </span>
                      </div>
                      <span className="text-[10px] text-slate-500 block">
                        Base: ${(whatIfResult.base_case.implied_ev / 1e6).toFixed(1)}M
                      </span>
                    </div>

                    {/* Decision Score Comparison */}
                    <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1 font-mono">
                      <span className="text-[10px] text-slate-500 uppercase">Decision Score</span>
                      <div className="flex items-baseline gap-2">
                        <span className="text-xl font-bold text-white">
                          {whatIfResult.scenario_case.decision_score.toFixed(1)}
                        </span>
                        <span
                          className={`text-xs font-bold ${
                            whatIfResult.deltas.decision_score_delta >= 0 ? 'text-emerald-400' : 'text-rose-400'
                          }`}
                        >
                          {whatIfResult.deltas.decision_score_delta >= 0 ? '+' : ''}
                          {whatIfResult.deltas.decision_score_delta.toFixed(1)} pts
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5 pt-0.5">
                        <span className="text-[10px] text-slate-500">Band:</span>
                        {getBandBadge(whatIfResult.scenario_case.decision_band)}
                      </div>
                    </div>
                  </div>

                  {/* Revenue & EBITDA Comparison */}
                  <div className="grid grid-cols-2 gap-4 text-xs font-mono">
                    <div className="p-2.5 rounded bg-slate-950/80 border border-slate-800">
                      <span className="text-[10px] text-slate-500">Simulated Revenue:</span>
                      <p className="text-slate-200 font-bold mt-0.5">
                        ${(whatIfResult.scenario_case.revenue / 1e6).toFixed(1)}M
                        <span className="text-[10px] text-slate-400 ml-1">
                          ({whatIfResult.deltas.revenue_delta_pct.toFixed(1)}%)
                        </span>
                      </p>
                    </div>
                    <div className="p-2.5 rounded bg-slate-950/80 border border-slate-800">
                      <span className="text-[10px] text-slate-500">Simulated EBITDA:</span>
                      <p className="text-slate-200 font-bold mt-0.5">
                        ${(whatIfResult.scenario_case.ebitda / 1e6).toFixed(1)}M
                        <span className="text-[10px] text-slate-400 ml-1">
                          ({whatIfResult.scenario_case.ebitda_margin_pct.toFixed(0)}% margin)
                        </span>
                      </p>
                    </div>
                  </div>
                </Card>

                {/* Scenario Recommendations */}
                {whatIfResult.recommendations && (
                  <Card className="p-4 bg-slate-900/90 border-slate-800 space-y-2 text-xs font-mono">
                    <span className="text-[10px] uppercase text-emerald-400 font-bold">Scenario Diligence Covenants</span>
                    <div className="space-y-1.5 pt-1">
                      {whatIfResult.recommendations.map((rec: string, i: number) => (
                        <div key={i} className="p-2 rounded bg-slate-950 border border-slate-800 text-slate-300 font-sans text-xs">
                          {rec}
                        </div>
                      ))}
                    </div>
                  </Card>
                )}
              </>
            ) : (
              <Card className="p-8 bg-slate-900/90 border-slate-800 text-center text-xs font-mono text-slate-500">
                Adjust assumptions to observe live deterministic financial and decision score changes.
              </Card>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: 2D SENSITIVITY MATRIX */}
      {activeTab === 'SENSITIVITY' && (
        <div className="space-y-5">
          <Card className="p-5 bg-slate-900/90 border-slate-800 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
              <div>
                <h2 className="text-sm font-semibold text-white font-mono flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-emerald-400" />
                  2D Cross-Parameter Sensitivity Surface
                </h2>
                <p className="text-xs text-slate-400">
                  Analyze valuation and decision score elasticity across simultaneous parameter shifts.
                </p>
              </div>

              <div className="flex items-center gap-2 text-xs font-mono">
                <select
                  value={rowVar}
                  onChange={(e) => setRowVar(e.target.value)}
                  className="px-2.5 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-200"
                >
                  <option value="revenue_growth_pct">Row: Revenue Growth (%)</option>
                  <option value="wacc_pct">Row: Discount Rate / WACC (%)</option>
                </select>

                <span className="text-slate-500 font-bold">×</span>

                <select
                  value={colVar}
                  onChange={(e) => setColVar(e.target.value)}
                  className="px-2.5 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-200"
                >
                  <option value="ebitda_margin_pct">Col: EBITDA Margin (%)</option>
                  <option value="terminal_growth_rate_pct">Col: Terminal Growth (%)</option>
                  <option value="churn_rate_pct">Col: Churn Rate (%)</option>
                </select>

                <button
                  type="button"
                  onClick={handleRunSensitivity}
                  disabled={isComputing}
                  className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-semibold flex items-center gap-1.5 shadow"
                >
                  <Play className="w-3.5 h-3.5" />
                  Compute Matrix
                </button>
              </div>
            </div>

            {/* Matrix Heatmap Table */}
            {sensitivityResult && sensitivityResult.data.matrix_grid && (
              <div className="overflow-x-auto space-y-4">
                <table className="w-full text-center text-xs font-mono border-collapse">
                  <thead>
                    <tr>
                      <th className="p-2.5 border border-slate-800 bg-slate-950 text-slate-400 text-left">
                        {rowVar} ↓ \ {colVar} →
                      </th>
                      {sensitivityResult.data.col_steps?.map((c, i) => (
                        <th key={i} className="p-2.5 border border-slate-800 bg-slate-950 text-emerald-400 font-bold">
                          {c}%
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {sensitivityResult.data.matrix_grid.map((row, rIdx) => (
                      <tr key={rIdx}>
                        <td className="p-2.5 border border-slate-800 bg-slate-950 text-slate-300 font-bold text-left">
                          {sensitivityResult.data.row_steps?.[rIdx]}%
                        </td>
                        {row.map((cell, cIdx) => (
                          <td
                            key={cIdx}
                            className={`p-2.5 border border-slate-800 transition-colors ${
                              cell.decision_score >= 80
                                ? 'bg-emerald-950/40 text-emerald-300'
                                : cell.decision_score >= 65
                                ? 'bg-blue-950/40 text-blue-300'
                                : cell.decision_score >= 50
                                ? 'bg-amber-950/40 text-amber-300'
                                : 'bg-rose-950/40 text-rose-300'
                            }`}
                          >
                            <div className="font-bold text-sm">${(cell.implied_ev / 1e6).toFixed(1)}M</div>
                            <div className="text-[10px] opacity-80">{cell.decision_score.toFixed(0)} pts ({cell.decision_band})</div>
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>

                {/* Tipping Points Callout */}
                {sensitivityResult.data.tipping_points && sensitivityResult.data.tipping_points.length > 0 && (
                  <div className="p-3.5 rounded-lg bg-rose-950/30 border border-rose-900/60 text-xs font-mono space-y-1.5">
                    <span className="text-rose-400 font-bold uppercase flex items-center gap-1.5">
                      <AlertTriangle className="w-3.5 h-3.5" />
                      Critical Tipping-Point Inflections Detected:
                    </span>
                    {sensitivityResult.data.tipping_points.map((tp, idx) => (
                      <p key={idx} className="text-rose-200">
                        • {tp.issue} at {rowVar}={tp[rowVar]}% & {colVar}={tp[colVar]}% (EV: ${(tp.implied_ev / 1e6).toFixed(1)}M, Score: {tp.decision_score.toFixed(1)})
                      </p>
                    ))}
                  </div>
                )}
              </div>
            )}
          </Card>
        </div>
      )}

      {/* TAB 3: MONTE CARLO SIMULATION */}
      {activeTab === 'MONTE_CARLO' && (
        <div className="space-y-5">
          <Card className="p-5 bg-slate-900/90 border-slate-800 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
              <div>
                <h2 className="text-sm font-semibold text-white font-mono flex items-center gap-2">
                  <PieChart className="w-4 h-4 text-emerald-400" />
                  Monte Carlo Stochastic Uncertainty Engine
                </h2>
                <p className="text-xs text-slate-400">
                  Simulate thousands of correlated outcomes with statistical confidence bounds and Value-at-Risk.
                </p>
              </div>

              <div className="flex items-center gap-2.5 text-xs font-mono">
                <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1">
                  <span className="text-slate-400">Iterations:</span>
                  <select
                    value={mcIterations}
                    onChange={(e) => setMcIterations(parseInt(e.target.value))}
                    className="bg-transparent text-white font-bold focus:outline-none"
                  >
                    <option value={500} className="bg-slate-900">500 draws</option>
                    <option value={1000} className="bg-slate-900">1,000 draws</option>
                    <option value={5000} className="bg-slate-900">5,000 draws</option>
                    <option value={10000} className="bg-slate-900">10,000 draws</option>
                  </select>
                </div>

                <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1">
                  <span className="text-slate-400">Seed:</span>
                  <input
                    type="number"
                    value={mcSeed}
                    onChange={(e) => setMcSeed(parseInt(e.target.value) || 42)}
                    className="w-12 bg-transparent text-emerald-400 font-bold focus:outline-none"
                  />
                </div>

                <button
                  type="button"
                  onClick={handleRunMonteCarlo}
                  disabled={isComputing}
                  className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-semibold flex items-center gap-1.5 shadow"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  Run Monte Carlo
                </button>
              </div>
            </div>

            {/* Monte Carlo Results Display */}
            {mcResult && (
              <div className="space-y-6 pt-2">
                {/* Statistical Overview Grid */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 font-mono text-xs">
                  <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800">
                    <span className="text-[10px] text-slate-500 uppercase">Median Enterprise Value</span>
                    <p className="text-xl font-bold text-white mt-1">
                      ${(mcResult.valuation_statistics.median / 1e6).toFixed(1)}M
                    </p>
                    <span className="text-[10px] text-slate-400">
                      Mean: ${(mcResult.valuation_statistics.mean / 1e6).toFixed(1)}M (σ: ${(mcResult.valuation_statistics.std_dev / 1e6).toFixed(1)}M)
                    </span>
                  </div>

                  <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800">
                    <span className="text-[10px] text-slate-500 uppercase">Median Decision Score</span>
                    <p className="text-xl font-bold text-emerald-400 mt-1">
                      {mcResult.decision_score_statistics.median.toFixed(1)} pts
                    </p>
                    <span className="text-[10px] text-slate-400">
                      Range: {mcResult.decision_score_statistics.min.toFixed(0)} - {mcResult.decision_score_statistics.max.toFixed(0)} pts
                    </span>
                  </div>

                  <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800">
                    <span className="text-[10px] text-slate-500 uppercase">Prob. of Downside / High Risk</span>
                    <p className="text-xl font-bold text-rose-400 mt-1">
                      {mcResult.downside_metrics.prob_high_risk_pct}%
                    </p>
                    <span className="text-[10px] text-slate-400">
                      P(EV &lt; Target): {mcResult.downside_metrics.prob_below_target_ev_pct}%
                    </span>
                  </div>

                  <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800">
                    <span className="text-[10px] text-slate-500 uppercase">Value-at-Risk (VaR 95%)</span>
                    <p className="text-xl font-bold text-amber-400 mt-1">
                      ${(mcResult.downside_metrics.value_at_risk_95 / 1e6).toFixed(1)}M
                    </p>
                    <span className="text-[10px] text-slate-400">95% Confidence Tail Cushion</span>
                  </div>
                </div>

                {/* Percentile Table */}
                <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-3 font-mono text-xs">
                  <span className="text-[11px] font-bold text-white uppercase">Valuation & Decision Score Percentiles</span>
                  <div className="overflow-x-auto">
                    <table className="w-full text-center">
                      <thead className="text-[10px] text-slate-500 border-b border-slate-800">
                        <tr>
                          <th className="py-1.5 text-left">Metric</th>
                          <th>P5 (Bear)</th>
                          <th>P10</th>
                          <th>P25</th>
                          <th>P50 (Median)</th>
                          <th>P75</th>
                          <th>P90</th>
                          <th>P95 (Bull)</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 text-slate-200">
                        <tr>
                          <td className="py-2 text-left font-bold text-slate-400">Implied EV ($M)</td>
                          <td className="text-rose-400 font-bold">${(mcResult.valuation_statistics.percentiles.p5 / 1e6).toFixed(1)}M</td>
                          <td>${(mcResult.valuation_statistics.percentiles.p10 / 1e6).toFixed(1)}M</td>
                          <td>${(mcResult.valuation_statistics.percentiles.p25 / 1e6).toFixed(1)}M</td>
                          <td className="text-white font-bold">${(mcResult.valuation_statistics.percentiles.p50 / 1e6).toFixed(1)}M</td>
                          <td>${(mcResult.valuation_statistics.percentiles.p75 / 1e6).toFixed(1)}M</td>
                          <td>${(mcResult.valuation_statistics.percentiles.p90 / 1e6).toFixed(1)}M</td>
                          <td className="text-emerald-400 font-bold">${(mcResult.valuation_statistics.percentiles.p95 / 1e6).toFixed(1)}M</td>
                        </tr>
                        <tr>
                          <td className="py-2 text-left font-bold text-slate-400">Decision Score</td>
                          <td className="text-rose-400 font-bold">{mcResult.decision_score_statistics.percentiles.p5.toFixed(1)}</td>
                          <td>{mcResult.decision_score_statistics.percentiles.p10.toFixed(1)}</td>
                          <td>{mcResult.decision_score_statistics.percentiles.p25.toFixed(1)}</td>
                          <td className="text-white font-bold">{mcResult.decision_score_statistics.percentiles.p50.toFixed(1)}</td>
                          <td>{mcResult.decision_score_statistics.percentiles.p75.toFixed(1)}</td>
                          <td>{mcResult.decision_score_statistics.percentiles.p90.toFixed(1)}</td>
                          <td className="text-emerald-400 font-bold">{mcResult.decision_score_statistics.percentiles.p95.toFixed(1)}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Decision Band Probability Distribution Bar */}
                <div className="space-y-2 font-mono text-xs">
                  <span className="text-[11px] font-bold text-slate-300 uppercase">Decision Band Outcome Probabilities</span>
                  <div className="grid grid-cols-5 gap-2">
                    {Object.entries(mcResult.band_probabilities).map(([band, prob]) => (
                      <div key={band} className="p-2.5 rounded bg-slate-950 border border-slate-800 text-center">
                        <span className="text-[10px] text-slate-500 block">{band}</span>
                        <span className="text-base font-bold text-white mt-0.5 block">{prob}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </Card>
        </div>
      )}

      {/* TAB 4: SCENARIO COMPARISON */}
      {activeTab === 'COMPARISON' && (
        <Card className="p-5 bg-slate-900/90 border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-sm font-semibold text-white font-mono flex items-center gap-2">
              <Table className="w-4 h-4 text-emerald-400" />
              Saved Deal Scenarios Comparative Ledger
            </h2>
            <span className="text-xs font-mono text-slate-400">{savedScenarios.length} Scenarios</span>
          </div>

          {savedScenarios.length === 0 ? (
            <p className="text-xs font-mono text-slate-500 py-6 text-center">
              No saved scenarios for this deal workspace. Use the What-If Builder to create and save scenarios.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="text-[10px] uppercase text-slate-500 border-b border-slate-800">
                  <tr>
                    <th className="py-2 px-3">Scenario Name</th>
                    <th className="py-2 px-3">Type</th>
                    <th className="py-2 px-3">Simulated Revenue</th>
                    <th className="py-2 px-3">Simulated EBITDA</th>
                    <th className="py-2 px-3">Implied EV</th>
                    <th className="py-2 px-3">Score</th>
                    <th className="py-2 px-3">Band</th>
                    <th className="py-2 px-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/40">
                  {savedScenarios.map((scen) => {
                    const scCase = scen.results?.scenario_case;
                    return (
                      <tr key={scen.id} className="hover:bg-slate-800/30">
                        <td className="py-2.5 px-3 font-bold text-white">{scen.name}</td>
                        <td className="py-2.5 px-3">
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                            {scen.scenario_type}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-200">
                          {scCase ? `$${(scCase.revenue / 1e6).toFixed(1)}M` : 'N/A'}
                        </td>
                        <td className="py-2.5 px-3 text-slate-200">
                          {scCase ? `$${(scCase.ebitda / 1e6).toFixed(1)}M` : 'N/A'}
                        </td>
                        <td className="py-2.5 px-3 font-bold text-emerald-400">
                          {scCase ? `$${(scCase.implied_ev / 1e6).toFixed(1)}M` : 'N/A'}
                        </td>
                        <td className="py-2.5 px-3 font-bold text-white">
                          {scCase ? scCase.decision_score.toFixed(1) : 'N/A'}
                        </td>
                        <td className="py-2.5 px-3">
                          {scCase ? getBandBadge(scCase.decision_band) : 'N/A'}
                        </td>
                        <td className="py-2.5 px-3 text-right">
                          <button
                            onClick={() => handleDeleteScenario(scen.id)}
                            className="p-1 rounded hover:bg-rose-950 text-slate-500 hover:text-rose-400 transition-colors"
                            title="Delete Scenario"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
