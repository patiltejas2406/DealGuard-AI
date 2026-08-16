'use client';

/**
 * DealGuard AI — Valuation Intelligence & Deal Valuation Engine Workspace
 */

import React, { useEffect, useState } from 'react';
import {
  TrendingUp,
  DollarSign,
  Plus,
  Trash2,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  PieChart,
  Shield,
  Layers,
  ArrowRight,
  Scale,
  Sparkles,
  Calculator,
  Sliders,
  BarChart3,
  FileSpreadsheet,
  HelpCircle,
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import {
  ComparableAnalysisItem,
  ComparableCompanyItem,
  DcfValuationItem,
  Deal,
  PrecedentAnalysisItem,
  PrecedentTransactionItem,
  SensitivityMatrixItem,
  ValuationAssumptionItem,
  ValuationItem,
  ValuationSummaryItem,
  ValuationValidationItem,
  WaccAnalysisItem,
} from '@/types';

export default function ValuationPage() {
  const { isAuthenticated } = useAuth();

  const [deals, setDeals] = useState<Deal[]>([]);
  const [selectedDealId, setSelectedDealId] = useState<string | null>(null);

  // Active Tab
  const [activeTab, setActiveTab] = useState<'SUMMARY' | 'DCF' | 'WACC' | 'COMPS' | 'PRECEDENTS' | 'SENSITIVITY' | 'ASSUMPTIONS'>('SUMMARY');

  // Valuation Data State
  const [valuation, setValuation] = useState<ValuationItem | null>(null);
  const [summary, setSummary] = useState<ValuationSummaryItem | null>(null);
  const [dcfData, setDcfData] = useState<DcfValuationItem | null>(null);
  const [waccData, setWaccData] = useState<WaccAnalysisItem | null>(null);
  const [compsData, setCompsData] = useState<ComparableAnalysisItem | null>(null);
  const [precedentsData, setPrecedentsData] = useState<PrecedentAnalysisItem | null>(null);
  const [sensitivityData, setSensitivityData] = useState<SensitivityMatrixItem | null>(null);
  const [assumptions, setAssumptions] = useState<ValuationAssumptionItem[]>([]);
  const [validation, setValidation] = useState<ValuationValidationItem | null>(null);

  const [terminalMethod, setTerminalMethod] = useState<'PERPETUITY_GROWTH' | 'EXIT_MULTIPLE'>('PERPETUITY_GROWTH');
  const [loading, setLoading] = useState(false);

  // Add Comp Modal State
  const [showCompModal, setShowCompModal] = useState(false);
  const [compName, setCompName] = useState('');
  const [compTicker, setCompTicker] = useState('');
  const [compRev, setCompRev] = useState('');
  const [compEbitda, setCompEbitda] = useState('');
  const [compEv, setCompEv] = useState('');

  // Add Precedent Modal State
  const [showTxModal, setShowTxModal] = useState(false);
  const [txTarget, setTxTarget] = useState('');
  const [txAcquirer, setTxAcquirer] = useState('');
  const [txDate, setTxDate] = useState('');
  const [txValue, setTxValue] = useState('');
  const [txRev, setTxRev] = useState('');
  const [txEbitda, setTxEbitda] = useState('');

  useEffect(() => {
    if (isAuthenticated) {
      loadDeals();
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (selectedDealId) {
      loadAllValuationData(selectedDealId);
    }
  }, [selectedDealId, terminalMethod]);

  const loadDeals = async () => {
    try {
      const dealList = await api.getDeals();
      setDeals(dealList);
      if (dealList.length > 0 && !selectedDealId) {
        setSelectedDealId(dealList[0].id);
      }
    } catch (err) {
      console.error('Failed to load deals', err);
    }
  };

  const loadAllValuationData = async (dealId: string) => {
    setLoading(true);
    try {
      const [
        valRes,
        sumRes,
        dcfRes,
        waccRes,
        compsRes,
        txRes,
        sensRes,
        assRes,
        valReportRes,
      ] = await Promise.all([
        api.getValuation(dealId).catch(() => null),
        api.getValuationSummary(dealId).catch(() => null),
        api.getDcfValuation(dealId, terminalMethod).catch(() => null),
        api.getWaccAnalysis(dealId).catch(() => null),
        api.getComparables(dealId).catch(() => null),
        api.getPrecedents(dealId).catch(() => null),
        api.getValuationSensitivity(dealId).catch(() => null),
        api.getValuationAssumptions(dealId).catch(() => []),
        api.getValuationValidation(dealId).catch(() => null),
      ]);

      setValuation(valRes);
      setSummary(sumRes);
      setDcfData(dcfRes);
      setWaccData(waccRes);
      setCompsData(compsRes);
      setPrecedentsData(txRes);
      setSensitivityData(sensRes);
      setAssumptions(assRes);
      setValidation(valReportRes);
    } catch (err) {
      console.error('Failed to load valuation data', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddComp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDealId || !compName.trim()) return;

    try {
      await api.createComparable(selectedDealId, {
        company_name: compName,
        ticker: compTicker || undefined,
        revenue: compRev ? parseFloat(compRev) * 1e6 : undefined,
        ebitda: compEbitda ? parseFloat(compEbitda) * 1e6 : undefined,
        enterprise_value: compEv ? parseFloat(compEv) * 1e6 : undefined,
        status: 'INCLUDED',
      });
      setShowCompModal(false);
      setCompName('');
      setCompTicker('');
      setCompRev('');
      setCompEbitda('');
      setCompEv('');
      loadAllValuationData(selectedDealId);
    } catch (err) {
      console.error('Failed to add comparable', err);
    }
  };

  const handleAddPrecedent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDealId || !txTarget.trim()) return;

    try {
      await api.createPrecedent(selectedDealId, {
        target_name: txTarget,
        acquirer_name: txAcquirer || undefined,
        announcement_date: txDate || undefined,
        transaction_value: txValue ? parseFloat(txValue) * 1e6 : undefined,
        enterprise_value: txValue ? parseFloat(txValue) * 1e6 : undefined,
        revenue: txRev ? parseFloat(txRev) * 1e6 : undefined,
        ebitda: txEbitda ? parseFloat(txEbitda) * 1e6 : undefined,
        status: 'INCLUDED',
      });
      setShowTxModal(false);
      setTxTarget('');
      setTxAcquirer('');
      setTxDate('');
      setTxValue('');
      setTxRev('');
      setTxEbitda('');
      loadAllValuationData(selectedDealId);
    } catch (err) {
      console.error('Failed to add precedent', err);
    }
  };

  const toggleCompStatus = async (comp: ComparableCompanyItem) => {
    if (!selectedDealId) return;
    const nextStatus = comp.status === 'INCLUDED' ? 'EXCLUDED' : 'INCLUDED';
    try {
      await api.updateComparable(selectedDealId, comp.id, { status: nextStatus });
      loadAllValuationData(selectedDealId);
    } catch (err) {
      console.error('Failed to toggle comp', err);
    }
  };

  const deleteComp = async (compId: string) => {
    if (!selectedDealId) return;
    try {
      await api.deleteComparable(selectedDealId, compId);
      loadAllValuationData(selectedDealId);
    } catch (err) {
      console.error('Failed to delete comp', err);
    }
  };

  return (
    <div className="mx-auto max-w-7xl space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-surface-border pb-6">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white font-mono">
              Valuation Intelligence & Deal Valuation Engine
            </h1>
            <Badge variant="success" size="sm">Phase 6 Multi-Methodology</Badge>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Deterministic DCF schedules, WACC CAPM modeling, Trading Peer Comparables, M&A Precedents, and Sensitivity Heatmaps.
          </p>
        </div>

        {/* Deal Selector Dropdown */}
        {deals.length > 0 && (
          <div className="flex items-center gap-3">
            <label className="text-xs font-mono text-slate-400 uppercase">Active Deal:</label>
            <select
              value={selectedDealId || ''}
              onChange={(e) => setSelectedDealId(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500 font-medium"
            >
              {deals.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.title}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {!isAuthenticated ? (
        <Card className="p-8 text-center bg-slate-900/60 border-slate-800 space-y-4">
          <Shield className="w-8 h-8 text-emerald-400 mx-auto" />
          <h2 className="text-lg font-semibold text-white">Sign In to Access Valuation Models</h2>
          <p className="text-sm text-slate-400 max-w-md mx-auto">
            Review DCF valuations, trading peer multiples, sensitivity analysis, and audit provenance.
          </p>
          <a
            href="/login"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-sm transition-colors"
          >
            Sign In Now
            <ArrowRight className="w-4 h-4" />
          </a>
        </Card>
      ) : (
        <>
          {/* Top Key Metrics Banner */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[11px] font-mono text-slate-400 uppercase">DCF Implied EV</span>
              <div className="text-lg font-bold text-emerald-400 font-mono mt-1">
                {dcfData?.dcf?.implied_enterprise_value
                  ? `$${(dcfData.dcf.implied_enterprise_value / 1e6).toFixed(1)}M`
                  : '—'}
              </div>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[11px] font-mono text-slate-400 uppercase">DCF Implied Equity</span>
              <div className="text-lg font-bold text-sky-400 font-mono mt-1">
                {dcfData?.dcf?.implied_equity_value
                  ? `$${(dcfData.dcf.implied_equity_value / 1e6).toFixed(1)}M`
                  : '—'}
              </div>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[11px] font-mono text-slate-400 uppercase">WACC</span>
              <div className="text-lg font-bold text-white font-mono mt-1">
                {waccData?.wacc ? `${waccData.wacc.toFixed(2)}%` : '—'}
              </div>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[11px] font-mono text-slate-400 uppercase">Peer Median EV/EBITDA</span>
              <div className="text-lg font-bold text-purple-400 font-mono mt-1">
                {compsData?.statistics?.ev_to_ebitda_stats?.median
                  ? `${compsData.statistics.ev_to_ebitda_stats.median.toFixed(1)}x`
                  : '—'}
              </div>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[11px] font-mono text-slate-400 uppercase">Precedent Median EV/Rev</span>
              <div className="text-lg font-bold text-amber-400 font-mono mt-1">
                {precedentsData?.statistics?.ev_to_revenue_stats?.median
                  ? `${precedentsData.statistics.ev_to_revenue_stats.median.toFixed(1)}x`
                  : '—'}
              </div>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[11px] font-mono text-slate-400 uppercase">Model Health</span>
              <div className="mt-1">
                <Badge
                  variant={validation?.status === 'HEALTHY' ? 'success' : 'warning'}
                  size="sm"
                >
                  {validation?.status === 'HEALTHY' ? 'Consistent' : 'Check Warnings'}
                </Badge>
              </div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-2 overflow-x-auto border-b border-slate-800 pb-2">
            {[
              { id: 'SUMMARY', label: 'Valuation Overview' },
              { id: 'DCF', label: 'DCF Model' },
              { id: 'WACC', label: 'WACC / CAPM' },
              { id: 'COMPS', label: 'Trading Peers (CCA)' },
              { id: 'PRECEDENTS', label: 'Precedents (PTA)' },
              { id: 'SENSITIVITY', label: 'Sensitivity Matrix' },
              { id: 'ASSUMPTIONS', label: 'Audit & Provenance' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold font-mono whitespace-nowrap transition-colors ${
                  activeTab === tab.id
                    ? 'bg-emerald-500 text-slate-950'
                    : 'text-slate-400 hover:text-white bg-slate-950/60'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab 1: Valuation Summary / Football Field */}
          {activeTab === 'SUMMARY' && summary && (
            <Card className="p-6 bg-slate-900/90 border-slate-800 space-y-6">
              <div>
                <h2 className="text-sm font-semibold text-white uppercase tracking-wider font-mono">
                  Methodology Comparison & Valuation Football Field
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  Implied Enterprise Value ranges across intrinsic DCF, trading peer multiples, and precedent M&A transactions.
                </p>
              </div>

              <div className="space-y-4">
                {summary.methodologies.map((m) => (
                  <div key={m.methodology} className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
                    <div className="flex items-center justify-between text-xs font-mono">
                      <span className="font-bold text-white">{m.label}</span>
                      <span className="text-emerald-400 font-bold">
                        Base EV: {m.ev_base ? `$${(m.ev_base / 1e6).toFixed(1)}M` : '—'}
                      </span>
                    </div>

                    {/* Range Bar Graphic */}
                    <div className="flex items-center gap-3 text-[11px] font-mono text-slate-400">
                      <span>Low: {m.ev_low ? `$${(m.ev_low / 1e6).toFixed(1)}M` : '—'}</span>
                      <div className="flex-1 h-3 rounded-full bg-slate-800 relative overflow-hidden">
                        <div className="absolute inset-y-0 left-1/4 right-1/4 bg-emerald-500/40 rounded-full" />
                        <div className="absolute inset-y-0 left-1/2 w-1 bg-emerald-400 -translate-x-1/2" />
                      </div>
                      <span>High: {m.ev_high ? `$${(m.ev_high / 1e6).toFixed(1)}M` : '—'}</span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Tab 2: DCF Model */}
          {activeTab === 'DCF' && dcfData && (
            <Card className="p-6 bg-slate-900/90 border-slate-800 space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-4">
                <div>
                  <h2 className="text-sm font-semibold text-white uppercase tracking-wider font-mono">
                    Discounted Cash Flow (DCF) Schedule & Enterprise Value Bridge
                  </h2>
                  <p className="text-xs text-slate-400 mt-1">
                    Unlevered Free Cash Flow (UFCF) projections and terminal value discounting.
                  </p>
                </div>

                {/* Terminal Method Selector */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setTerminalMethod('PERPETUITY_GROWTH')}
                    className={`px-2.5 py-1 rounded text-xs font-mono font-medium ${
                      terminalMethod === 'PERPETUITY_GROWTH'
                        ? 'bg-emerald-500 text-slate-950'
                        : 'bg-slate-950 text-slate-400'
                    }`}
                  >
                    Perpetuity Growth (3.0%)
                  </button>
                  <button
                    onClick={() => setTerminalMethod('EXIT_MULTIPLE')}
                    className={`px-2.5 py-1 rounded text-xs font-mono font-medium ${
                      terminalMethod === 'EXIT_MULTIPLE'
                        ? 'bg-emerald-500 text-slate-950'
                        : 'bg-slate-950 text-slate-400'
                    }`}
                  >
                    Exit Multiple (10.0x)
                  </button>
                </div>
              </div>

              {/* Schedule Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-mono">
                      <th className="py-2.5 px-3">Line Item ($)</th>
                      {dcfData.dcf.schedule.map((s) => (
                        <th key={s.period} className="py-2.5 px-3 text-right">
                          {s.period}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    <tr>
                      <td className="py-2 px-3 text-slate-300 font-medium">Revenue</td>
                      {dcfData.dcf.schedule.map((s) => (
                        <td key={s.period} className="py-2 px-3 text-right text-slate-200">
                          ${((s.revenue || 0) / 1e6).toFixed(1)}M
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="py-2 px-3 text-slate-300 font-medium">EBITDA</td>
                      {dcfData.dcf.schedule.map((s) => (
                        <td key={s.period} className="py-2 px-3 text-right text-slate-200">
                          ${((s.ebitda || 0) / 1e6).toFixed(1)}M
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="py-2 px-3 text-slate-300 font-medium">EBIT</td>
                      {dcfData.dcf.schedule.map((s) => (
                        <td key={s.period} className="py-2 px-3 text-right text-slate-200">
                          ${((s.ebit || 0) / 1e6).toFixed(1)}M
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="py-2 px-3 text-slate-300 font-medium">NOPAT (EBIT × (1 - t))</td>
                      {dcfData.dcf.schedule.map((s) => (
                        <td key={s.period} className="py-2 px-3 text-right text-slate-200">
                          ${((s.nopat || 0) / 1e6).toFixed(1)}M
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="py-2 px-3 text-slate-300 font-medium">+ D&A</td>
                      {dcfData.dcf.schedule.map((s) => (
                        <td key={s.period} className="py-2 px-3 text-right text-slate-200">
                          +${((s.depreciation_amortization || 0) / 1e6).toFixed(1)}M
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="py-2 px-3 text-slate-300 font-medium">- CapEx</td>
                      {dcfData.dcf.schedule.map((s) => (
                        <td key={s.period} className="py-2 px-3 text-right text-rose-400">
                          -${((s.capex || 0) / 1e6).toFixed(1)}M
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="py-2 px-3 text-slate-300 font-medium">- Δ Working Capital</td>
                      {dcfData.dcf.schedule.map((s) => (
                        <td key={s.period} className="py-2 px-3 text-right text-rose-400">
                          -${((s.working_capital_change || 0) / 1e6).toFixed(1)}M
                        </td>
                      ))}
                    </tr>
                    <tr className="bg-slate-950/40 font-bold">
                      <td className="py-2.5 px-3 text-emerald-400">= Unlevered Free Cash Flow</td>
                      {dcfData.dcf.schedule.map((s) => (
                        <td key={s.period} className="py-2.5 px-3 text-right text-emerald-400">
                          ${((s.ufcf || 0) / 1e6).toFixed(2)}M
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="py-2 px-3 text-slate-400">Discount Factor (1/(1+WACC)^t)</td>
                      {dcfData.dcf.schedule.map((s) => (
                        <td key={s.period} className="py-2 px-3 text-right text-slate-400">
                          {s.discount_factor?.toFixed(4)}
                        </td>
                      ))}
                    </tr>
                    <tr className="bg-slate-950/80 font-bold">
                      <td className="py-2.5 px-3 text-sky-400">PV of UFCF</td>
                      {dcfData.dcf.schedule.map((s) => (
                        <td key={s.period} className="py-2.5 px-3 text-right text-sky-400">
                          ${((s.pv_ufcf || 0) / 1e6).toFixed(2)}M
                        </td>
                      ))}
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* DCF Valuation & Bridge Summary */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 rounded-xl bg-slate-950/60 border border-slate-800">
                <div className="space-y-2 text-xs font-mono">
                  <div className="text-slate-400 uppercase font-semibold">DCF Valuation Summary</div>
                  <div className="flex justify-between py-1 border-b border-slate-800">
                    <span className="text-slate-400">PV of 5-Year Forecast FCFs:</span>
                    <span className="text-white font-bold">${(dcfData.dcf.pv_forecast_fcf / 1e6).toFixed(2)}M</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800">
                    <span className="text-slate-400">Terminal Value:</span>
                    <span className="text-white font-bold">${(dcfData.dcf.terminal_value / 1e6).toFixed(2)}M</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800">
                    <span className="text-slate-400">PV of Terminal Value:</span>
                    <span className="text-white font-bold">${(dcfData.dcf.pv_terminal_value / 1e6).toFixed(2)}M</span>
                  </div>
                  <div className="flex justify-between py-1.5 text-emerald-400 text-sm font-bold">
                    <span>Implied Enterprise Value:</span>
                    <span>${(dcfData.dcf.implied_enterprise_value / 1e6).toFixed(2)}M</span>
                  </div>
                </div>

                <div className="space-y-2 text-xs font-mono">
                  <div className="text-slate-400 uppercase font-semibold">EV to Equity Value Bridge</div>
                  <div className="flex justify-between py-1 border-b border-slate-800">
                    <span className="text-slate-400">Enterprise Value:</span>
                    <span className="text-white font-bold">${(dcfData.dcf.bridge.enterprise_value / 1e6).toFixed(2)}M</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800">
                    <span className="text-slate-400">+ Cash & Equivalents:</span>
                    <span className="text-emerald-400 font-bold">+${(dcfData.dcf.bridge.cash_and_equivalents / 1e6).toFixed(2)}M</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800">
                    <span className="text-slate-400">- Total Debt:</span>
                    <span className="text-rose-400 font-bold">-${(dcfData.dcf.bridge.total_debt / 1e6).toFixed(2)}M</span>
                  </div>
                  <div className="flex justify-between py-1.5 text-sky-400 text-sm font-bold">
                    <span>Implied Equity Value:</span>
                    <span>${(dcfData.dcf.bridge.equity_value / 1e6).toFixed(2)}M</span>
                  </div>
                </div>
              </div>
            </Card>
          )}

          {/* Tab 3: WACC Calculator */}
          {activeTab === 'WACC' && waccData && (
            <Card className="p-6 bg-slate-900/90 border-slate-800 space-y-6">
              <div>
                <h2 className="text-sm font-semibold text-white uppercase tracking-wider font-mono">
                  Weighted Average Cost of Capital (WACC) & CAPM Breakdown
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  Cost of Equity ($K_e = R_f + \beta \times ERP$) + After-Tax Cost of Debt ($K_d \times (1 - t)$).
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                  <span className="text-[11px] font-mono text-slate-400 uppercase">Cost of Equity (Ke)</span>
                  <div className="text-2xl font-bold text-emerald-400 font-mono">
                    {waccData.cost_of_equity?.toFixed(2)}%
                  </div>
                  <p className="text-[11px] font-mono text-slate-500">
                    Risk-Free 4.5% + (Beta 1.15 × ERP 5.5%)
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                  <span className="text-[11px] font-mono text-slate-400 uppercase">After-Tax Cost of Debt (Kd)</span>
                  <div className="text-2xl font-bold text-sky-400 font-mono">
                    {waccData.after_tax_cost_of_debt?.toFixed(2)}%
                  </div>
                  <p className="text-[11px] font-mono text-slate-500">
                    Pre-Tax 6.5% × (1 - Tax Rate 25.0%)
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                  <span className="text-[11px] font-mono text-slate-400 uppercase">Calculated WACC</span>
                  <div className="text-2xl font-bold text-purple-400 font-mono">
                    {waccData.wacc?.toFixed(2)}%
                  </div>
                  <p className="text-[11px] font-mono text-slate-500">
                    80.0% Equity + 20.0% Debt
                  </p>
                </div>
              </div>
            </Card>
          )}

          {/* Tab 4: Trading Peers (CCA) */}
          {activeTab === 'COMPS' && compsData && (
            <Card className="p-6 bg-slate-900/90 border-slate-800 space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h2 className="text-sm font-semibold text-white uppercase tracking-wider font-mono">
                    Trading Comparable Companies (CCA)
                  </h2>
                  <p className="text-xs text-slate-400 mt-1">
                    Public peer trading valuation multiples and implied target valuation range.
                  </p>
                </div>

                <button
                  onClick={() => setShowCompModal(true)}
                  className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-xs transition-colors self-start sm:self-auto font-mono"
                >
                  <Plus className="w-3.5 h-3.5" />
                  Add Peer Company
                </button>
              </div>

              {/* Peers Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-mono">
                      <th className="py-2 px-3">Company</th>
                      <th className="py-2 px-3">Ticker</th>
                      <th className="py-2 px-3 text-right">Revenue ($M)</th>
                      <th className="py-2 px-3 text-right">EBITDA ($M)</th>
                      <th className="py-2 px-3 text-right">EV ($M)</th>
                      <th className="py-2 px-3 text-right">EV/Rev</th>
                      <th className="py-2 px-3 text-right">EV/EBITDA</th>
                      <th className="py-2 px-3 text-center">Status</th>
                      <th className="py-2 px-3 text-center">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    {compsData.companies.map((c) => (
                      <tr key={c.id} className="hover:bg-slate-950/40 transition-colors">
                        <td className="py-2.5 px-3 text-white font-semibold">{c.company_name}</td>
                        <td className="py-2.5 px-3 text-slate-400">{c.ticker || '—'}</td>
                        <td className="py-2.5 px-3 text-right text-slate-200">
                          {c.revenue ? `$${(c.revenue / 1e6).toFixed(1)}` : '—'}
                        </td>
                        <td className="py-2.5 px-3 text-right text-slate-200">
                          {c.ebitda ? `$${(c.ebitda / 1e6).toFixed(1)}` : '—'}
                        </td>
                        <td className="py-2.5 px-3 text-right text-slate-200">
                          {c.enterprise_value ? `$${(c.enterprise_value / 1e6).toFixed(1)}` : '—'}
                        </td>
                        <td className="py-2.5 px-3 text-right text-emerald-400 font-bold">
                          {c.ev_to_revenue ? `${c.ev_to_revenue.toFixed(1)}x` : '—'}
                        </td>
                        <td className="py-2.5 px-3 text-right text-sky-400 font-bold">
                          {c.ev_to_ebitda ? `${c.ev_to_ebitda.toFixed(1)}x` : '—'}
                        </td>
                        <td className="py-2.5 px-3 text-center">
                          <button
                            onClick={() => toggleCompStatus(c)}
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              c.status === 'INCLUDED'
                                ? 'bg-emerald-500/20 text-emerald-400'
                                : 'bg-slate-800 text-slate-500'
                            }`}
                          >
                            {c.status}
                          </button>
                        </td>
                        <td className="py-2.5 px-3 text-center">
                          <button
                            onClick={() => deleteComp(c.id)}
                            className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {/* Tab 5: Precedents (PTA) */}
          {activeTab === 'PRECEDENTS' && precedentsData && (
            <Card className="p-6 bg-slate-900/90 border-slate-800 space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h2 className="text-sm font-semibold text-white uppercase tracking-wider font-mono">
                    M&A Precedent Transactions (PTA)
                  </h2>
                  <p className="text-xs text-slate-400 mt-1">
                    Historical transaction deal multiples and implied benchmark valuation.
                  </p>
                </div>

                <button
                  onClick={() => setShowTxModal(true)}
                  className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-xs transition-colors self-start sm:self-auto font-mono"
                >
                  <Plus className="w-3.5 h-3.5" />
                  Add Precedent Deal
                </button>
              </div>

              {/* Transactions Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-mono">
                      <th className="py-2 px-3">Target</th>
                      <th className="py-2 px-3">Acquirer</th>
                      <th className="py-2 px-3">Date</th>
                      <th className="py-2 px-3 text-right">Deal Value ($M)</th>
                      <th className="py-2 px-3 text-right">EV/Rev</th>
                      <th className="py-2 px-3 text-right">EV/EBITDA</th>
                      <th className="py-2 px-3 text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    {precedentsData.transactions.map((t) => (
                      <tr key={t.id} className="hover:bg-slate-950/40 transition-colors">
                        <td className="py-2.5 px-3 text-white font-semibold">{t.target_name}</td>
                        <td className="py-2.5 px-3 text-slate-400">{t.acquirer_name || '—'}</td>
                        <td className="py-2.5 px-3 text-slate-400">{t.announcement_date || '—'}</td>
                        <td className="py-2.5 px-3 text-right text-slate-200">
                          {t.transaction_value ? `$${(t.transaction_value / 1e6).toFixed(1)}` : '—'}
                        </td>
                        <td className="py-2.5 px-3 text-right text-emerald-400 font-bold">
                          {t.ev_to_revenue ? `${t.ev_to_revenue.toFixed(1)}x` : '—'}
                        </td>
                        <td className="py-2.5 px-3 text-right text-sky-400 font-bold">
                          {t.ev_to_ebitda ? `${t.ev_to_ebitda.toFixed(1)}x` : '—'}
                        </td>
                        <td className="py-2.5 px-3 text-center">
                          <Badge variant="default" size="sm">{t.status}</Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {/* Tab 6: Sensitivity Matrix */}
          {activeTab === 'SENSITIVITY' && sensitivityData && (
            <Card className="p-6 bg-slate-900/90 border-slate-800 space-y-6">
              <div>
                <h2 className="text-sm font-semibold text-white uppercase tracking-wider font-mono">
                  2D DCF Sensitivity Heatmap Matrix (Implied Enterprise Value $M)
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  Rows: WACC (%) • Columns: Terminal Growth Rate (%)
                </p>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-xs text-center border-collapse font-mono">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400">
                      <th className="py-2.5 px-3 text-left">WACC \ Growth</th>
                      {sensitivityData.column_values.map((col, idx) => (
                        <th
                          key={col}
                          className={`py-2.5 px-3 ${
                            idx === sensitivityData.base_column_index ? 'text-emerald-400 font-bold' : ''
                          }`}
                        >
                          {col.toFixed(2)}%
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {sensitivityData.row_values.map((rowVal, rIdx) => (
                      <tr key={rowVal} className="hover:bg-slate-950/40">
                        <td
                          className={`py-2.5 px-3 text-left font-bold ${
                            rIdx === sensitivityData.base_row_index ? 'text-emerald-400' : 'text-slate-300'
                          }`}
                        >
                          {rowVal.toFixed(2)}%
                        </td>
                        {sensitivityData.enterprise_value_matrix[rIdx].map((cell, cIdx) => (
                          <td
                            key={cIdx}
                            className={`py-2.5 px-3 ${
                              rIdx === sensitivityData.base_row_index && cIdx === sensitivityData.base_column_index
                                ? 'bg-emerald-500/20 text-emerald-300 font-bold ring-1 ring-emerald-500/40'
                                : cell
                                ? 'text-slate-200'
                                : 'text-slate-600'
                            }`}
                          >
                            {cell ? `$${(cell / 1e6).toFixed(1)}M` : 'N/A'}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {/* Tab 7: Assumptions & Provenance */}
          {activeTab === 'ASSUMPTIONS' && (
            <Card className="p-6 bg-slate-900/90 border-slate-800 space-y-6">
              <div>
                <h2 className="text-sm font-semibold text-white uppercase tracking-wider font-mono">
                  Valuation Assumptions & Audit Provenance
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  Every parameter links back to source documents, financial models, or analyst inputs.
                </p>
              </div>

              <div className="divide-y divide-slate-800/60 rounded-xl border border-slate-800 overflow-hidden bg-slate-950/40">
                {assumptions.map((a) => (
                  <div key={a.id} className="p-3.5 flex items-center justify-between text-xs font-mono">
                    <div>
                      <div className="font-bold text-white">{a.name}</div>
                      <div className="text-[10px] text-slate-500 mt-0.5">
                        Category: {a.category} • Source: {a.source_type}
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="font-bold text-emerald-400">
                        {a.value} {a.unit}
                      </span>
                      <Badge variant={a.is_analyst_entered ? 'default' : 'success'} size="sm">
                        {a.is_analyst_entered ? 'Analyst Input' : 'Sourced Document'}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </>
      )}

      {/* Add Comparable Peer Modal */}
      {showCompModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-white font-mono">Add Trading Peer Company</h3>
            <form onSubmit={handleAddComp} className="space-y-3 font-mono">
              <div>
                <label className="block text-[11px] uppercase text-slate-400 mb-1">Company Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. CrowdStrike Holdings"
                  value={compName}
                  onChange={(e) => setCompName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] uppercase text-slate-400 mb-1">Ticker</label>
                  <input
                    type="text"
                    placeholder="CRWD"
                    value={compTicker}
                    onChange={(e) => setCompTicker(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-[11px] uppercase text-slate-400 mb-1">EV ($M)</label>
                  <input
                    type="number"
                    step="any"
                    placeholder="65000"
                    value={compEv}
                    onChange={(e) => setCompEv(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] uppercase text-slate-400 mb-1">Revenue ($M)</label>
                  <input
                    type="number"
                    step="any"
                    placeholder="3000"
                    value={compRev}
                    onChange={(e) => setCompRev(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-[11px] uppercase text-slate-400 mb-1">EBITDA ($M)</label>
                  <input
                    type="number"
                    step="any"
                    placeholder="750"
                    value={compEbitda}
                    onChange={(e) => setCompEbitda(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setShowCompModal(false)}
                  className="px-4 py-2 text-xs text-slate-400 hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-xs rounded-lg transition-colors"
                >
                  Add Peer
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Precedent Modal */}
      {showTxModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-white font-mono">Add Precedent M&A Deal</h3>
            <form onSubmit={handleAddPrecedent} className="space-y-3 font-mono">
              <div>
                <label className="block text-[11px] uppercase text-slate-400 mb-1">Target Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Mandiant"
                  value={txTarget}
                  onChange={(e) => setTxTarget(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] uppercase text-slate-400 mb-1">Acquirer</label>
                  <input
                    type="text"
                    placeholder="Google"
                    value={txAcquirer}
                    onChange={(e) => setTxAcquirer(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-[11px] uppercase text-slate-400 mb-1">Deal Value ($M)</label>
                  <input
                    type="number"
                    step="any"
                    placeholder="5400"
                    value={txValue}
                    onChange={(e) => setTxValue(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] uppercase text-slate-400 mb-1">Revenue ($M)</label>
                  <input
                    type="number"
                    step="any"
                    placeholder="500"
                    value={txRev}
                    onChange={(e) => setTxRev(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-[11px] uppercase text-slate-400 mb-1">EBITDA ($M)</label>
                  <input
                    type="number"
                    step="any"
                    placeholder="100"
                    value={txEbitda}
                    onChange={(e) => setTxEbitda(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setShowTxModal(false)}
                  className="px-4 py-2 text-xs text-slate-400 hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-xs rounded-lg transition-colors"
                >
                  Add Transaction
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
