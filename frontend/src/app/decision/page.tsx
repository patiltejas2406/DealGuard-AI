'use client';

/**
 * DealGuard AI — Phase 8: Composite Decision Score & Explainable Decision Intelligence Console
 */

import React, { useEffect, useState } from 'react';
import {
  Shield,
  AlertTriangle,
  TrendingUp,
  DollarSign,
  Layers,
  FileCheck2,
  RefreshCw,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Building2,
  Sliders,
  ChevronRight,
  PieChart,
  BarChart3,
  Scale,
  Clock,
  Info,
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import {
  Deal,
  DecisionScoreHistoryItem,
  DecisionScoreResponse,
  ScoreComponentDetail,
} from '@/types';

const COMPONENT_TITLES: Record<string, { label: string; icon: React.ComponentType<{ className?: string }> }> = {
  FINANCIAL_HEALTH: { label: 'Financial Health & QoE', icon: TrendingUp },
  VALUATION_ATTRACTIVENESS: { label: 'Valuation Attractiveness', icon: DollarSign },
  RISK_EXPOSURE: { label: '17-Pillar Risk Exposure', icon: AlertTriangle },
  REVENUE_QUALITY: { label: 'Revenue Quality & Churn', icon: PieChart },
  EVIDENCE_CONFIDENCE: { label: 'Evidence & Citation Depth', icon: FileCheck2 },
  DEAL_COMPLEXITY: { label: 'Deal & Integration Complexity', icon: Layers },
};

export default function DecisionScorePage() {
  const { isAuthenticated } = useAuth();

  // Deals State
  const [deals, setDeals] = useState<Deal[]>([]);
  const [selectedDealId, setSelectedDealId] = useState<string | null>(null);

  // Score Data State
  const [scoreData, setScoreData] = useState<DecisionScoreResponse | null>(null);
  const [history, setHistory] = useState<DecisionScoreHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isCalculating, setIsCalculating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Selected Component for Deep-Dive Modal
  const [selectedComponent, setSelectedComponent] = useState<ScoreComponentDetail | null>(null);

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

  // 2. Load Decision Score & History whenever deal changes
  useEffect(() => {
    if (!selectedDealId) return;
    loadDecisionData(selectedDealId);
  }, [selectedDealId]);

  async function loadDecisionData(dealId: string) {
    setIsLoading(true);
    setError(null);
    try {
      const [scoreRes, histRes] = await Promise.all([
        api.getDecisionScore(dealId),
        api.getDecisionScoreHistory(dealId),
      ]);
      setScoreData(scoreRes);
      setHistory(histRes.history || []);
    } catch (err: any) {
      setError(err?.message || 'Failed to load composite decision score.');
    } finally {
      setIsLoading(false);
    }
  }

  // 3. Trigger Explicit Score Recalculation
  async function handleRecalculate() {
    if (!selectedDealId) return;
    setIsCalculating(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const calculated = await api.calculateDecisionScore(selectedDealId);
      setScoreData(calculated);
      setSuccessMessage('Composite decision score successfully recalculated and synchronized with deal register.');
      const histRes = await api.getDecisionScoreHistory(selectedDealId);
      setHistory(histRes.history || []);
    } catch (err: any) {
      setError(err?.message || 'Recalculation failed.');
    } finally {
      setIsCalculating(false);
    }
  }

  // Helper for Decision Band Aesthetics
  const getBandBadge = (band: string) => {
    switch (band) {
      case 'STRONG':
        return <Badge variant="success" size="md">STRONG CANDIDATE</Badge>;
      case 'FAVORABLE':
        return <Badge variant="info" size="md">FAVORABLE</Badge>;
      case 'CAUTION':
        return <Badge variant="warning" size="md">CAUTION</Badge>;
      case 'HIGH_RISK':
        return <Badge variant="danger" size="md">HIGH RISK</Badge>;
      case 'AVOID':
        return <Badge variant="danger" size="md">AVOID</Badge>;
      default:
        return <Badge variant="default" size="md">{band}</Badge>;
    }
  };

  const getBandColor = (band: string) => {
    switch (band) {
      case 'STRONG':
        return 'text-emerald-400 border-emerald-800/80 bg-emerald-950/30';
      case 'FAVORABLE':
        return 'text-blue-400 border-blue-800/80 bg-blue-950/30';
      case 'CAUTION':
        return 'text-amber-400 border-amber-800/80 bg-amber-950/30';
      case 'HIGH_RISK':
        return 'text-rose-400 border-rose-800/80 bg-rose-950/30';
      case 'AVOID':
        return 'text-red-500 border-red-800/80 bg-red-950/30';
      default:
        return 'text-slate-300 border-slate-800 bg-slate-900';
    }
  };

  const currentDeal = deals.find((d) => d.id === selectedDealId);

  return (
    <div className="min-h-screen bg-surface-base text-slate-100 p-6 space-y-6">
      {/* Top Header Bar */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 border-b border-slate-800 pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2 font-mono">
                Composite DealGuard Decision Score
                <Badge variant="success" size="sm">Phase 8 Engine v1.0</Badge>
              </h1>
              <p className="text-xs text-slate-400">
                Explainable Multi-Domain Decision Intelligence, Deterministic Mathematical Lineage & Risk-Adjusted Scoring
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

          {/* Recalculate Button */}
          <button
            type="button"
            onClick={handleRecalculate}
            disabled={isCalculating || !selectedDealId}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-semibold shadow-lg shadow-emerald-950 transition-colors font-mono"
          >
            <Sparkles className={`w-3.5 h-3.5 ${isCalculating ? 'animate-spin' : ''}`} />
            {isCalculating ? 'Computing Cross-Domain Math...' : 'Recalculate Decision Score'}
          </button>

          {/* Refresh Button */}
          <button
            type="button"
            onClick={() => selectedDealId && loadDecisionData(selectedDealId)}
            className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
            title="Refresh Score"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
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

      {/* Hero Decision Score & Band Card */}
      {scoreData && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Main Score Hero Card */}
          <Card className={`lg:col-span-4 p-6 border flex flex-col justify-between ${getBandColor(scoreData.decision_band)}`}>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono uppercase tracking-wider text-slate-400">Composite Score</span>
                <span className="text-[11px] font-mono text-slate-400">v{scoreData.scoring_version}</span>
              </div>

              {/* Large Score Display */}
              <div className="flex items-baseline gap-2">
                <span className="text-6xl font-black font-mono tracking-tight text-white">
                  {scoreData.overall_score.toFixed(1)}
                </span>
                <span className="text-xl font-mono text-slate-400">/ 100</span>
              </div>

              {/* Decision Band Badge */}
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  {getBandBadge(scoreData.decision_band)}
                </div>
                <p className="text-xs text-slate-300 leading-relaxed pt-1">
                  {scoreData.decision_band_description}
                </p>
              </div>
            </div>

            {/* Confidence & Oversight Callout */}
            <div className="pt-5 mt-5 border-t border-slate-800/80 space-y-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-slate-400">Diligence Confidence:</span>
                <span className="font-bold text-white">{(scoreData.confidence_score * 100).toFixed(0)}%</span>
              </div>
              <div className="w-full h-1.5 bg-slate-950 rounded-full overflow-hidden">
                <div
                  className="h-full bg-emerald-500 rounded-full"
                  style={{ width: `${scoreData.confidence_score * 100}%` }}
                />
              </div>
              <p className="text-[10px] text-slate-500 font-mono italic pt-1">
                *Decision Support Only — Final transaction authority rests with the Investment Committee.
              </p>
            </div>
          </Card>

          {/* 6-Component Breakdown Cards Grid */}
          <div className="lg:col-span-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {Object.entries(scoreData.components).map(([key, comp]) => {
              const meta = COMPONENT_TITLES[key] || { label: key, icon: Shield };
              const Icon = meta.icon;

              return (
                <Card
                  key={key}
                  onClick={() => setSelectedComponent(comp)}
                  className="p-4 bg-slate-900/90 border-slate-800 hover:border-slate-700 transition-all cursor-pointer group flex flex-col justify-between space-y-3"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-xs font-medium text-slate-300 font-mono">
                        <Icon className="w-4 h-4 text-emerald-400" />
                        <span className="truncate">{meta.label}</span>
                      </div>
                      <span
                        className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${
                          comp.status === 'AVAILABLE'
                            ? 'bg-emerald-950 text-emerald-400 border border-emerald-800/60'
                            : comp.status === 'PARTIAL'
                            ? 'bg-amber-950 text-amber-400 border border-amber-800/60'
                            : 'bg-rose-950 text-rose-400 border border-rose-800/60'
                        }`}
                      >
                        {comp.status}
                      </span>
                    </div>

                    <div className="flex items-baseline justify-between pt-1">
                      <span className="text-2xl font-bold font-mono text-white group-hover:text-emerald-300 transition-colors">
                        {comp.score.toFixed(1)}
                      </span>
                      <span className="text-[11px] font-mono text-slate-400">
                        {(comp.weight * 100).toFixed(0)}% wt ({comp.weighted_contribution.toFixed(1)} pts)
                      </span>
                    </div>

                    <div className="w-full h-1 bg-slate-950 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-emerald-500 rounded-full transition-all"
                        style={{ width: `${comp.score}%` }}
                      />
                    </div>
                  </div>

                  <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-400 font-mono">
                    <span className="truncate">{comp.explanation}</span>
                    <ChevronRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-white transition-colors" />
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* Strategic Drivers Section */}
      {scoreData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Positive Value Drivers */}
          <Card className="p-5 bg-slate-900/90 border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-sm font-semibold text-white font-mono flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                Positive Deal Drivers ({scoreData.positive_drivers.length})
              </h2>
              <span className="text-[11px] font-mono text-emerald-400">Value Accretive</span>
            </div>

            <div className="space-y-2">
              {scoreData.positive_drivers.length === 0 ? (
                <p className="text-xs text-slate-500 font-mono italic">No primary positive drivers recorded.</p>
              ) : (
                scoreData.positive_drivers.map((drv, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-lg bg-emerald-950/20 border border-emerald-900/40 text-xs flex items-center justify-between gap-2 font-mono text-emerald-200"
                  >
                    <span className="flex-1">{drv.driver}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-900/40 border border-emerald-700/60 font-bold uppercase">
                      {drv.impact}
                    </span>
                  </div>
                ))
              )}
            </div>
          </Card>

          {/* Downside Risks & Vulnerabilities */}
          <Card className="p-5 bg-slate-900/90 border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-sm font-semibold text-white font-mono flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-400" />
                Downside Risks & Drag Factors ({scoreData.negative_drivers.length})
              </h2>
              <span className="text-[11px] font-mono text-rose-400">Value Dilutive</span>
            </div>

            <div className="space-y-2">
              {scoreData.negative_drivers.length === 0 ? (
                <p className="text-xs text-slate-500 font-mono italic">No major downside risk drivers flagged.</p>
              ) : (
                scoreData.negative_drivers.map((drv, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-lg bg-rose-950/20 border border-rose-900/40 text-xs flex items-center justify-between gap-2 font-mono text-rose-200"
                  >
                    <span className="flex-1">{drv.driver}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-rose-900/40 border border-rose-700/60 font-bold uppercase">
                      {drv.impact}
                    </span>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>
      )}

      {/* Recommendations & Missing Information Gaps */}
      {scoreData && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Institutional Recommendations */}
          <Card className="lg:col-span-7 p-5 bg-slate-900/90 border-slate-800 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-sm font-semibold text-white font-mono flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-emerald-400" />
                Investment Committee Diligence Guidance
              </h2>
              <span className="text-[11px] font-mono text-slate-400">Action Plan</span>
            </div>

            <div className="space-y-2 pt-1">
              {scoreData.recommendations.map((rec, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-lg bg-slate-950 border border-slate-800/80 text-xs text-slate-200 flex items-start gap-2.5 font-sans leading-relaxed"
                >
                  <span className="font-mono text-emerald-400 font-bold">{idx + 1}.</span>
                  <span>{rec}</span>
                </div>
              ))}
            </div>
          </Card>

          {/* Missing Data Diligence Gaps */}
          <Card className="lg:col-span-5 p-5 bg-slate-900/90 border-slate-800 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-sm font-semibold text-white font-mono flex items-center gap-2">
                <Info className="w-4 h-4 text-amber-400" />
                Data Room Gaps & Missing Inputs
              </h2>
              <span className="text-[11px] font-mono text-slate-400">Coverage</span>
            </div>

            <div className="space-y-2 pt-1">
              {scoreData.missing_information.length === 0 ? (
                <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-900/40 text-xs text-emerald-300 font-mono">
                  Full coverage across financial, valuation, risk, and data room evidence pillars.
                </div>
              ) : (
                scoreData.missing_information.map((gap, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-lg bg-amber-950/20 border border-amber-900/40 text-xs text-amber-200 font-mono flex items-center gap-2"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                    <span>{gap}</span>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>
      )}

      {/* Historical Score Calculation Timeline */}
      {history.length > 0 && (
        <Card className="p-5 bg-slate-900/90 border-slate-800 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-sm font-semibold text-white font-mono flex items-center gap-2">
              <Clock className="w-4 h-4 text-slate-400" />
              Score Calculation History ({history.length})
            </h2>
            <span className="text-[11px] font-mono text-slate-400">Audit Trail</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="text-[10px] uppercase text-slate-500 border-b border-slate-800">
                <tr>
                  <th className="py-2 px-3">Calculation Timestamp</th>
                  <th className="py-2 px-3">Score</th>
                  <th className="py-2 px-3">Band</th>
                  <th className="py-2 px-3">Confidence</th>
                  <th className="py-2 px-3">Version</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40">
                {history.map((h) => (
                  <tr key={h.id} className="hover:bg-slate-800/30">
                    <td className="py-2 px-3 text-slate-300">
                      {new Date(h.created_at).toLocaleString()}
                    </td>
                    <td className="py-2 px-3 font-bold text-white">{h.overall_score.toFixed(1)}</td>
                    <td className="py-2 px-3">
                      <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-800">
                        {h.decision_band}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-slate-300">{(h.confidence_score * 100).toFixed(0)}%</td>
                    <td className="py-2 px-3 text-slate-400">v{h.scoring_version}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Component Deep-Dive Inspection Modal */}
      {selectedComponent && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn">
          <div className="w-full max-w-xl bg-slate-900 border border-slate-800 rounded-xl shadow-2xl p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <span className="text-[10px] font-mono uppercase text-emerald-400">Component Lineage</span>
                <h3 className="text-base font-bold text-white font-mono mt-0.5">
                  {COMPONENT_TITLES[selectedComponent.name]?.label || selectedComponent.name}
                </h3>
              </div>
              <button
                onClick={() => setSelectedComponent(null)}
                className="text-slate-400 hover:text-white"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4 text-xs font-mono">
              {/* Score & Contribution */}
              <div className="grid grid-cols-3 gap-2 p-3 bg-slate-950 rounded-lg border border-slate-800">
                <div>
                  <span className="text-[10px] text-slate-500 uppercase">Score (0-100)</span>
                  <p className="text-emerald-400 font-bold text-base mt-0.5">
                    {selectedComponent.score.toFixed(1)}
                  </p>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 uppercase">Weight Allocation</span>
                  <p className="text-white font-bold text-base mt-0.5">
                    {(selectedComponent.weight * 100).toFixed(0)}%
                  </p>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 uppercase">Contribution</span>
                  <p className="text-emerald-400 font-bold text-base mt-0.5">
                    {selectedComponent.weighted_contribution.toFixed(1)} pts
                  </p>
                </div>
              </div>

              {/* Explanation */}
              <div className="space-y-1">
                <span className="text-slate-400 text-[10px] uppercase">Calculation Lineage</span>
                <p className="p-3 rounded-lg bg-slate-950 border border-slate-800/80 text-slate-200 leading-relaxed font-sans text-xs">
                  {selectedComponent.explanation}
                </p>
              </div>

              {/* Raw Evaluated Inputs */}
              <div className="space-y-1">
                <span className="text-slate-400 text-[10px] uppercase">Raw Evaluated Inputs</span>
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-[11px] overflow-x-auto">
                  <pre className="text-slate-300 font-mono">
                    {JSON.stringify(selectedComponent.raw_inputs, null, 2)}
                  </pre>
                </div>
              </div>

              {/* Specific Drivers */}
              {selectedComponent.drivers && selectedComponent.drivers.length > 0 && (
                <div className="space-y-1">
                  <span className="text-slate-400 text-[10px] uppercase">Associated Drivers</span>
                  <div className="space-y-1.5">
                    {selectedComponent.drivers.map((d, i) => (
                      <div
                        key={i}
                        className={`p-2 rounded border text-[11px] flex items-center justify-between ${
                          d.type === 'POSITIVE'
                            ? 'bg-emerald-950/30 border-emerald-900 text-emerald-200'
                            : 'bg-rose-950/30 border-rose-900 text-rose-200'
                        }`}
                      >
                        <span>{d.driver}</span>
                        <span className="text-[9px] font-bold uppercase">{d.impact}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="pt-3 border-t border-slate-800 flex justify-end">
              <button
                type="button"
                onClick={() => setSelectedComponent(null)}
                className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono transition-colors"
              >
                Close Lineage
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
