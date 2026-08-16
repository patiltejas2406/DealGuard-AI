'use client';

/**
 * DealGuard AI — Financial Statement Modeling, Quality of Earnings (QoE) & Ratios Console
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
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import {
  CagrAnalysisItem,
  Deal,
  FinancialMetricItem,
  FinancialStatementItem,
  FinancialValidationItem,
  QoEAdjustmentItem,
  QoEBridgeItem,
} from '@/types';

export default function FinancialsPage() {
  const { isAuthenticated } = useAuth();

  const [deals, setDeals] = useState<Deal[]>([]);
  const [selectedDealId, setSelectedDealId] = useState<string | null>(null);

  // Financial Data State
  const [statements, setStatements] = useState<FinancialStatementItem[]>([]);
  const [metrics, setMetrics] = useState<FinancialMetricItem[]>([]);
  const [cagr, setCagr] = useState<CagrAnalysisItem | null>(null);
  const [qoeBridge, setQoEBridge] = useState<QoEBridgeItem | null>(null);
  const [validation, setValidation] = useState<FinancialValidationItem | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState<string>('FY2023');
  const [statementTab, setStatementTab] = useState<'INCOME_STATEMENT' | 'BALANCE_SHEET' | 'CASH_FLOW'>('INCOME_STATEMENT');

  const [loading, setLoading] = useState(false);

  // New Adjustment Modal State
  const [showAdjModal, setShowAdjModal] = useState(false);
  const [newCategory, setNewCategory] = useState('LEGAL_NON_RECURRING');
  const [newDesc, setNewDesc] = useState('');
  const [newAmount, setNewAmount] = useState('');
  const [newTreatment, setNewTreatment] = useState<'ADD_BACK' | 'DEDUCTION'>('ADD_BACK');
  const [submittingAdj, setSubmittingAdj] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      loadDeals();
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (selectedDealId) {
      loadFinancialData(selectedDealId, selectedPeriod);
    }
  }, [selectedDealId, selectedPeriod]);

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

  const loadFinancialData = async (dealId: string, period: string) => {
    setLoading(true);
    try {
      const [stmtsRes, metricsRes, cagrRes, qoeRes, valRes] = await Promise.all([
        api.getFinancialStatements(dealId).catch(() => []),
        api.getFinancialMetrics(dealId).catch(() => []),
        api.getDealCagr(dealId).catch(() => null),
        api.getQoEBridge(dealId, period).catch(() => null),
        api.getFinancialValidation(dealId).catch(() => null),
      ]);
      setStatements(stmtsRes);
      setMetrics(metricsRes);
      setCagr(cagrRes);
      setQoEBridge(qoeRes);
      setValidation(valRes);
    } catch (err) {
      console.error('Failed to load financial data', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddAdjustment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDealId || !newDesc.trim() || !newAmount) return;

    setSubmittingAdj(true);
    try {
      await api.createQoEAdjustment(selectedDealId, {
        category: newCategory,
        description: newDesc,
        amount: parseFloat(newAmount),
        period: selectedPeriod,
        treatment: newTreatment,
        status: 'APPROVED',
      });
      setShowAdjModal(false);
      setNewDesc('');
      setNewAmount('');
      if (selectedDealId) {
        loadFinancialData(selectedDealId, selectedPeriod);
      }
    } catch (err) {
      console.error('Failed to create adjustment', err);
    } finally {
      setSubmittingAdj(false);
    }
  };

  const handleDeleteAdjustment = async (adjustmentId: string) => {
    if (!selectedDealId) return;
    try {
      await api.deleteQoEAdjustment(selectedDealId, adjustmentId);
      loadFinancialData(selectedDealId, selectedPeriod);
    } catch (err) {
      console.error('Failed to delete adjustment', err);
    }
  };

  // Group statements by period for tabular columns
  const activeStatements = statements.filter((s) => s.statement_type === statementTab);
  const periods = Array.from(new Set(statements.map((s) => s.fiscal_period))).sort();

  return (
    <div className="mx-auto max-w-7xl space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-surface-border pb-6">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white font-mono">
              3-Statement Financial Modeling & QoE Console
            </h1>
            <Badge variant="success" size="sm">Deterministic Engine</Badge>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Exact Decimal arithmetic, EBITDA Quality of Earnings normalization bridge, and automated accounting reconciliation.
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
          <h2 className="text-lg font-semibold text-white">Sign In to Access Financial Intelligence</h2>
          <p className="text-sm text-slate-400 max-w-md mx-auto">
            Review 3-statement models, QoE adjustments, and multi-year CAGR metrics.
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
          {/* Key Metrics Strip */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[11px] font-mono text-slate-400 uppercase">Revenue</span>
              <div className="text-lg font-bold text-white font-mono mt-1">
                {metrics.find((m) => m.metric_name === 'REVENUE')?.value
                  ? `$${(metrics.find((m) => m.metric_name === 'REVENUE')!.value / 1e6).toFixed(1)}M`
                  : '—'}
              </div>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[11px] font-mono text-slate-400 uppercase">Gross Margin</span>
              <div className="text-lg font-bold text-emerald-400 font-mono mt-1">
                {metrics.find((m) => m.metric_name === 'GROSS_MARGIN')?.value
                  ? `${metrics.find((m) => m.metric_name === 'GROSS_MARGIN')!.value.toFixed(1)}%`
                  : '—'}
              </div>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[11px] font-mono text-slate-400 uppercase">EBITDA Margin</span>
              <div className="text-lg font-bold text-sky-400 font-mono mt-1">
                {metrics.find((m) => m.metric_name === 'EBITDA_MARGIN')?.value
                  ? `${metrics.find((m) => m.metric_name === 'EBITDA_MARGIN')!.value.toFixed(1)}%`
                  : '—'}
              </div>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[11px] font-mono text-slate-400 uppercase">Net Debt</span>
              <div className="text-lg font-bold text-slate-200 font-mono mt-1">
                {metrics.find((m) => m.metric_name === 'NET_DEBT')?.value
                  ? `$${(metrics.find((m) => m.metric_name === 'NET_DEBT')!.value / 1e6).toFixed(1)}M`
                  : '—'}
              </div>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[11px] font-mono text-slate-400 uppercase">Revenue CAGR</span>
              <div className="text-lg font-bold text-purple-400 font-mono mt-1">
                {cagr?.revenue_cagr ? `${cagr.revenue_cagr.toFixed(1)}%` : '—'}
              </div>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[11px] font-mono text-slate-400 uppercase">Accounting Status</span>
              <div className="mt-1">
                <Badge
                  variant={validation?.status === 'HEALTHY' ? 'success' : 'warning'}
                  size="sm"
                >
                  {validation?.status === 'HEALTHY' ? 'Balanced' : 'Discrepancies'}
                </Badge>
              </div>
            </div>
          </div>

          {/* Quality of Earnings (QoE) Bridge Section */}
          <Card className="p-6 bg-slate-900/90 border-slate-800 space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <div className="flex items-center gap-2">
                  <Scale className="w-4 h-4 text-emerald-400" />
                  <h2 className="text-sm font-semibold text-white uppercase tracking-wider font-mono">
                    Quality of Earnings (QoE) EBITDA Normalization Bridge
                  </h2>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Adjust reported EBITDA for non-recurring litigation, founder expenses, and pro-forma adjustments.
                </p>
              </div>

              <button
                onClick={() => setShowAdjModal(true)}
                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-xs transition-colors self-start sm:self-auto"
              >
                <Plus className="w-3.5 h-3.5" />
                Add QoE Adjustment
              </button>
            </div>

            {/* Bridge Summary Cards */}
            {qoeBridge && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-xl bg-slate-950/80 border border-slate-800/80">
                <div>
                  <span className="text-[10px] font-mono text-slate-500 uppercase">Reported EBITDA</span>
                  <div className="text-base font-bold text-white font-mono mt-0.5">
                    {qoeBridge.bridge.reported_ebitda
                      ? `$${(qoeBridge.bridge.reported_ebitda / 1e6).toFixed(2)}M`
                      : '—'}
                  </div>
                </div>
                <div>
                  <span className="text-[10px] font-mono text-emerald-500 uppercase">+ Total Add-Backs</span>
                  <div className="text-base font-bold text-emerald-400 font-mono mt-0.5">
                    +${(qoeBridge.bridge.total_add_backs / 1e6).toFixed(2)}M
                  </div>
                </div>
                <div>
                  <span className="text-[10px] font-mono text-rose-500 uppercase">- Total Deductions</span>
                  <div className="text-base font-bold text-rose-400 font-mono mt-0.5">
                    -${(qoeBridge.bridge.total_deductions / 1e6).toFixed(2)}M
                  </div>
                </div>
                <div>
                  <span className="text-[10px] font-mono text-sky-400 uppercase">= Adjusted EBITDA</span>
                  <div className="text-base font-bold text-sky-400 font-mono mt-0.5">
                    {qoeBridge.bridge.adjusted_ebitda
                      ? `$${(qoeBridge.bridge.adjusted_ebitda / 1e6).toFixed(2)}M`
                      : '—'}
                  </div>
                </div>
              </div>
            )}

            {/* Adjustments Table */}
            {qoeBridge && qoeBridge.adjustments.length > 0 && (
              <div className="space-y-2">
                <div className="text-[11px] font-mono uppercase text-slate-400">
                  Approved & Proposed Adjustments ({qoeBridge.adjustments.length})
                </div>
                <div className="divide-y divide-slate-800/80 rounded-xl border border-slate-800 overflow-hidden bg-slate-950/40">
                  {qoeBridge.adjustments.map((adj) => (
                    <div key={adj.id} className="p-3.5 flex items-center justify-between gap-4 text-xs">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-white truncate">{adj.description}</span>
                          <Badge variant={adj.treatment === 'ADD_BACK' ? 'success' : 'danger'} size="sm">
                            {adj.treatment === 'ADD_BACK' ? '+ Add-Back' : '- Deduction'}
                          </Badge>
                          <Badge variant={adj.status === 'APPROVED' ? 'default' : 'warning'} size="sm">
                            {adj.status}
                          </Badge>
                        </div>
                        <div className="text-[10px] font-mono text-slate-500 mt-0.5">
                          Category: {adj.category} • Period: {adj.period}
                        </div>
                      </div>

                      <div className="flex items-center gap-4 shrink-0 font-mono">
                        <span className={`font-bold ${adj.treatment === 'ADD_BACK' ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {adj.treatment === 'ADD_BACK' ? '+' : '-'}${adj.amount.toLocaleString()}
                        </span>
                        <button
                          onClick={() => handleDeleteAdjustment(adj.id)}
                          className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>

          {/* 3-Statement Modeling Matrix Section */}
          <Card className="p-6 bg-slate-900/90 border-slate-800 space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-4">
              {/* Statement Tabs */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setStatementTab('INCOME_STATEMENT')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold font-mono transition-colors ${
                    statementTab === 'INCOME_STATEMENT'
                      ? 'bg-emerald-500 text-slate-950'
                      : 'text-slate-400 hover:text-white bg-slate-950'
                  }`}
                >
                  Income Statement
                </button>
                <button
                  onClick={() => setStatementTab('BALANCE_SHEET')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold font-mono transition-colors ${
                    statementTab === 'BALANCE_SHEET'
                      ? 'bg-emerald-500 text-slate-950'
                      : 'text-slate-400 hover:text-white bg-slate-950'
                  }`}
                >
                  Balance Sheet
                </button>
                <button
                  onClick={() => setStatementTab('CASH_FLOW')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold font-mono transition-colors ${
                    statementTab === 'CASH_FLOW'
                      ? 'bg-emerald-500 text-slate-950'
                      : 'text-slate-400 hover:text-white bg-slate-950'
                  }`}
                >
                  Cash Flow
                </button>
              </div>

              <div className="text-[11px] font-mono text-slate-400">
                Amounts in USD • Audited & Deterministic Derivations
              </div>
            </div>

            {/* Table Matrix */}
            {activeStatements.length === 0 ? (
              <div className="p-12 text-center text-xs text-slate-500 font-mono">
                No statement records found for {statementTab}.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-mono">
                      <th className="py-2.5 px-3">Line Item</th>
                      {activeStatements.map((s) => (
                        <th key={s.id} className="py-2.5 px-3 text-right">
                          {s.fiscal_period} {s.is_audited ? '✓' : ''}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    {/* Render Line Items Dynamically */}
                    {Object.keys(activeStatements[0].line_items || {})
                      .filter((k) => !['is_balanced', 'balance_discrepancy'].includes(k))
                      .map((key) => (
                        <tr key={key} className="hover:bg-slate-950/40 transition-colors">
                          <td className="py-2 px-3 text-slate-300 font-medium capitalize">
                            {key.replace(/_/g, ' ')}
                          </td>
                          {activeStatements.map((s) => {
                            const val = s.line_items[key];
                            return (
                              <td key={s.id} className="py-2 px-3 text-right text-slate-200">
                                {typeof val === 'number'
                                  ? val < 0
                                    ? `($${Math.abs(val).toLocaleString()})`
                                    : `$${val.toLocaleString()}`
                                  : val ?? '—'}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </>
      )}

      {/* QoE Add-Back Modal */}
      {showAdjModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-white font-mono">Add QoE Normalization Item</h3>
            <form onSubmit={handleAddAdjustment} className="space-y-3">
              <div>
                <label className="block text-[11px] font-mono uppercase text-slate-400 mb-1">
                  Description
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. One-time legal dispute settlement"
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-mono uppercase text-slate-400 mb-1">
                    Amount ($)
                  </label>
                  <input
                    type="number"
                    step="any"
                    required
                    placeholder="450000"
                    value={newAmount}
                    onChange={(e) => setNewAmount(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-mono uppercase text-slate-400 mb-1">
                    Treatment
                  </label>
                  <select
                    value={newTreatment}
                    onChange={(e) => setNewTreatment(e.target.value as any)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                  >
                    <option value="ADD_BACK">+ Add-Back (Expense)</option>
                    <option value="DEDUCTION">- Deduction (Income)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-mono uppercase text-slate-400 mb-1">
                  Category
                </label>
                <select
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                >
                  <option value="LEGAL_NON_RECURRING">Non-Recurring Legal Fees</option>
                  <option value="ONE_TIME_EXPENSE">One-Time Advisory / Audit Expense</option>
                  <option value="RESTRUCTURING">Severance / Restructuring Costs</option>
                  <option value="OWNER_PERSONAL">Owner / Founder Personal Expenses</option>
                  <option value="PRO_FORMA">Pro-Forma / Run-Rate Synergy</option>
                  <option value="ONE_TIME_INCOME">Non-Operating Income Gain</option>
                  <option value="OTHER">Other Adjustment</option>
                </select>
              </div>

              <div className="flex justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setShowAdjModal(false)}
                  className="px-4 py-2 text-xs text-slate-400 hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingAdj}
                  className="px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-xs rounded-lg transition-colors"
                >
                  {submittingAdj ? 'Saving...' : 'Save Adjustment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
