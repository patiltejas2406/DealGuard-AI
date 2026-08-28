'use client';

import React, { useState, useEffect } from 'react';
import {
  Network,
  Bot,
  Shield,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Sparkles,
  ArrowRight,
  RefreshCw,
  Cpu,
  Layers,
  TrendingUp,
  FileCheck2,
  Scale,
  FileText,
  Lock,
  ChevronRight,
  ExternalLink,
  Zap,
  ShieldCheck,
} from 'lucide-react';
import {
  api,
  AgentMetadataItem,
  AgentOrchestrationResultItem,
  MLModelItem,
  AgentAssessmentItem,
  PredictionResultItem,
} from '@/lib/api';
import { Deal } from '@/types';
import { cn } from '@/lib/utils';

export default function AgentOrchestrationPage() {
  const [deals, setDeals] = useState<Deal[]>([]);
  const [selectedDealId, setSelectedDealId] = useState<string | null>(null);
  const [agents, setAgents] = useState<AgentMetadataItem[]>([]);
  const [mlModels, setMlModels] = useState<MLModelItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [orchestrating, setOrchestrating] = useState<boolean>(false);
  const [runningMLModelId, setRunningMLModelId] = useState<string | null>(null);
  const [mlPredictionResult, setMlPredictionResult] = useState<PredictionResultItem | null>(null);
  const [orchestrationMode, setOrchestrationMode] = useState<string>('FULL_DEAL_DECISION');
  const [queryInput, setQueryInput] = useState<string>('');
  const [orchestrationResult, setOrchestrationResult] = useState<AgentOrchestrationResultItem | null>(null);
  const [activeTab, setActiveTab] = useState<'decision' | 'specialists' | 'ml' | 'extensibility'>('decision');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [dealsList, agentList, modelList] = await Promise.all([
        api.getDeals().catch(() => []),
        api.listAgents().catch(() => []),
        api.listMLModels().catch(() => []),
      ]);
      setDeals(dealsList);
      if (dealsList.length > 0) {
        setSelectedDealId(dealsList[0].id);
      }
      setAgents(agentList);
      setMlModels(modelList);
    } catch (err: any) {
      setError(err.message || 'Failed to initialize agent metadata catalog.');
    } finally {
      setLoading(false);
    }
  };

  const handleRunOrchestration = async () => {
    if (!selectedDealId) {
      setError('Please select an active deal to run agent orchestration.');
      return;
    }

    try {
      setOrchestrating(true);
      setError(null);
      const result = await api.orchestrateAgents(selectedDealId, {
        orchestration_mode: orchestrationMode,
        query: queryInput.trim() ? queryInput.trim() : undefined,
      });
      setOrchestrationResult(result);
      setActiveTab('decision');
    } catch (err: any) {
      setError(err.message || 'Multi-agent orchestration execution failed.');
    } finally {
      setOrchestrating(false);
    }
  };

  const handleRunMLPrediction = async (modelId: string) => {
    if (!selectedDealId) {
      setError('Please select an active deal to execute ML inference.');
      return;
    }

    try {
      setRunningMLModelId(modelId);
      setError(null);
      const res = await api.predictDealML(selectedDealId, { model_id: modelId });
      setMlPredictionResult(res);
    } catch (err: any) {
      setError(err.message || `ML inference failed for model '${modelId}'.`);
    } finally {
      setRunningMLModelId(null);
    }
  };

  const getRecommendationBadge = (rec?: string) => {
    switch (rec) {
      case 'BUY':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'BUY_WITH_CONDITIONS':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/30';
      case 'RENEGOTIATE':
        return 'bg-purple-500/10 text-purple-400 border-purple-500/30';
      case 'HOLD':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'AVOID':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      default:
        return 'bg-zinc-800 text-zinc-400 border-zinc-700';
    }
  };

  const preDealAgents = agents.filter(
    (a) => a.lifecycle_phase === 'PRE_DEAL_ACQUISITION' || a.lifecycle_phase === 'CROSS_LIFECYCLE'
  );
  const postDealAgents = agents.filter(
    (a) => a.lifecycle_phase === 'POST_DEAL_VALUE_CREATION'
  );

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between border-b border-surface-border pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-500/10 text-primary-400 border border-primary-500/20">
              <Network className="h-4 w-4" />
            </span>
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Agentic Intelligence Orchestration
            </h1>
          </div>
          <p className="mt-1 text-sm text-gray-400">
            Institutional multi-agent supervisor orchestrating 8 specialized diligence agents with deterministic tool validation & grounded synthesis.
          </p>
        </div>

        {/* Deal Selector */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-surface-card px-3 py-1.5 rounded-lg border border-surface-border">
            <span className="text-xs text-gray-400 font-medium">Deal:</span>
            <select
              value={selectedDealId || ''}
              onChange={(e) => setSelectedDealId(e.target.value)}
              className="bg-transparent text-sm font-semibold text-white focus:outline-none cursor-pointer"
            >
              {deals.map((d) => (
                <option key={d.id} value={d.id} className="bg-surface text-white">
                  {d.title} ({d.code_name})
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Control Banner & Orchestration Dispatcher */}
      <div className="rounded-xl border border-surface-border bg-surface-card p-5 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              <Zap className="h-4 w-4 text-primary-400" />
              Multi-Agent Diligence Supervisor
            </h2>
            <p className="text-xs text-gray-400">
              Select orchestration pipeline mode to route intent through bounded specialist DAGs without unconstrained autonomous loops.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <select
              value={orchestrationMode}
              onChange={(e) => setOrchestrationMode(e.target.value)}
              className="rounded-lg border border-surface-border bg-surface px-3 py-2 text-xs font-medium text-white focus:border-primary-500 focus:outline-none"
            >
              <option value="FULL_DEAL_DECISION">Full Deal Decision Synthesis (8 Agents)</option>
              <option value="TECH_AND_INTEGRATION_RISK">Tech, SPOF & 100-Day Integration</option>
              <option value="FINANCIAL_AND_VALUATION">Financial Statements & Valuation Lab</option>
              <option value="LEGAL_AND_RISK">Contract VaR & 17-Pillar Risk Engine</option>
            </select>

            <button
              onClick={handleRunOrchestration}
              disabled={orchestrating || !selectedDealId}
              className={cn(
                'inline-flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-semibold shadow-sm transition-colors',
                orchestrating
                  ? 'bg-primary-500/50 text-white cursor-not-allowed'
                  : 'bg-primary-600 text-white hover:bg-primary-500'
              )}
            >
              {orchestrating ? (
                <>
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                  Orchestrating Agents...
                </>
              ) : (
                <>
                  <Sparkles className="h-3.5 w-3.5" />
                  Execute Orchestration DAG
                </>
              )}
            </button>
          </div>
        </div>

        <div>
          <input
            type="text"
            placeholder="Optional diligence hypothesis or focus (e.g., 'Examine customer churn risk and AWS cloud unit economics')..."
            value={queryInput}
            onChange={(e) => setQueryInput(e.target.value)}
            className="w-full rounded-lg border border-surface-border bg-surface px-3.5 py-2 text-xs text-white placeholder-gray-500 focus:border-primary-500 focus:outline-none"
          />
        </div>

        {error && (
          <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-400 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Tabs Navigation */}
      <div className="flex border-b border-surface-border">
        <button
          onClick={() => setActiveTab('decision')}
          className={cn(
            'flex items-center gap-2 border-b-2 px-4 py-2.5 text-xs font-medium transition-colors',
            activeTab === 'decision'
              ? 'border-primary-500 text-primary-400'
              : 'border-transparent text-gray-400 hover:text-white'
          )}
        >
          <Shield className="h-4 w-4" />
          Deal Decision Synthesis
          {orchestrationResult && (
            <span className="ml-1 rounded bg-primary-500/20 px-1.5 py-0.5 text-[10px] text-primary-300">
              Ready
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('specialists')}
          className={cn(
            'flex items-center gap-2 border-b-2 px-4 py-2.5 text-xs font-medium transition-colors',
            activeTab === 'specialists'
              ? 'border-primary-500 text-primary-400'
              : 'border-transparent text-gray-400 hover:text-white'
          )}
        >
          <Bot className="h-4 w-4" />
          Specialist Agents ({preDealAgents.length})
        </button>

        <button
          onClick={() => setActiveTab('ml')}
          className={cn(
            'flex items-center gap-2 border-b-2 px-4 py-2.5 text-xs font-medium transition-colors',
            activeTab === 'ml'
              ? 'border-primary-500 text-primary-400'
              : 'border-transparent text-gray-400 hover:text-white'
          )}
        >
          <Cpu className="h-4 w-4" />
          ML & XAI Foundation ({mlModels.length})
        </button>

        <button
          onClick={() => setActiveTab('extensibility')}
          className={cn(
            'flex items-center gap-2 border-b-2 px-4 py-2.5 text-xs font-medium transition-colors',
            activeTab === 'extensibility'
              ? 'border-primary-500 text-primary-400'
              : 'border-transparent text-gray-400 hover:text-white'
          )}
        >
          <TrendingUp className="h-4 w-4" />
          Post-Deal Growth Registry ({postDealAgents.length})
        </button>
      </div>

      {/* Tab Content: Deal Decision Synthesis */}
      {activeTab === 'decision' && (
        <div className="space-y-6">
          {orchestrationResult ? (
            <>
              {/* Executive Decision Header Card */}
              <div className="rounded-xl border border-surface-border bg-surface-card p-6 space-y-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-surface-border pb-5">
                  <div className="space-y-1">
                    <div className="flex items-center gap-3">
                      <span
                        className={cn(
                          'rounded-full border px-3 py-1 text-xs font-bold uppercase tracking-wider',
                          getRecommendationBadge(orchestrationResult.decision_assessment.recommendation)
                        )}
                      >
                        {orchestrationResult.decision_assessment.recommendation.replace(/_/g, ' ')}
                      </span>
                      <span className="text-xs text-gray-400 font-mono">
                        Exec ID: {orchestrationResult.execution_id.slice(0, 8)}...
                      </span>
                      <span className="text-xs text-gray-400 flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {orchestrationResult.total_duration_ms.toFixed(1)}ms
                      </span>
                    </div>
                    <h3 className="text-lg font-bold text-white">
                      Synthesized Acquisition Recommendation
                    </h3>
                  </div>

                  <div className="flex items-center gap-6">
                    <div className="text-right">
                      <div className="text-[10px] uppercase tracking-wider text-gray-500 font-semibold">
                        Deterministic Score
                      </div>
                      <div className="text-xl font-bold font-mono text-white">
                        {orchestrationResult.decision_assessment.deterministic_decision_score !== null
                          ? orchestrationResult.decision_assessment.deterministic_decision_score.toFixed(1)
                          : 'N/A'}{' '}
                        <span className="text-xs text-gray-500 font-normal">/ 100</span>
                      </div>
                    </div>

                    <div className="text-right border-l border-surface-border pl-6">
                      <div className="text-[10px] uppercase tracking-wider text-gray-500 font-semibold">
                        Confidence
                      </div>
                      <div className="text-sm font-bold text-emerald-400">
                        {(orchestrationResult.decision_assessment.confidence_score * 100).toFixed(0)}% (
                        {orchestrationResult.decision_assessment.confidence})
                      </div>
                    </div>
                  </div>
                </div>

                {/* Human Review Escalation Banner */}
                {orchestrationResult.decision_assessment.human_review_required && (
                  <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4 space-y-2">
                    <div className="flex items-center gap-2 text-xs font-bold text-amber-300">
                      <AlertTriangle className="h-4 w-4" />
                      HUMAN-IN-THE-LOOP REVIEW ESCALATION REQUIRED
                    </div>
                    <p className="text-xs text-amber-200/90">
                      {orchestrationResult.decision_assessment.recommended_human_action ||
                        'Senior Investment Committee review required before signing.'}
                    </p>
                    {orchestrationResult.decision_assessment.escalation_reasons.length > 0 && (
                      <ul className="list-disc list-inside text-[11px] text-amber-300/80 space-y-0.5">
                        {orchestrationResult.decision_assessment.escalation_reasons.map((r, i) => (
                          <li key={i}>{r}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}

                {/* Executive Rationale */}
                <div className="space-y-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-gray-400">
                    Executive Decision Rationale
                  </h4>
                  <p className="text-sm leading-relaxed text-gray-200 bg-surface/60 p-4 rounded-lg border border-surface-border">
                    {orchestrationResult.decision_assessment.executive_rationale}
                  </p>
                </div>

                {/* Drivers Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Positive Drivers */}
                  <div className="rounded-lg border border-surface-border bg-surface/40 p-4 space-y-2">
                    <h5 className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5">
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      Positive Value Drivers ({orchestrationResult.decision_assessment.positive_drivers.length})
                    </h5>
                    <ul className="space-y-1 text-xs text-gray-300">
                      {orchestrationResult.decision_assessment.positive_drivers.map((d, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="text-emerald-400 mt-0.5">•</span>
                          <span>{d}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Negative Drivers */}
                  <div className="rounded-lg border border-surface-border bg-surface/40 p-4 space-y-2">
                    <h5 className="text-xs font-semibold text-rose-400 flex items-center gap-1.5">
                      <AlertTriangle className="h-3.5 w-3.5" />
                      Downside Risks & Friction ({orchestrationResult.decision_assessment.negative_drivers.length})
                    </h5>
                    <ul className="space-y-1 text-xs text-gray-300">
                      {orchestrationResult.decision_assessment.negative_drivers.map((d, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="text-rose-400 mt-0.5">•</span>
                          <span>{d}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Multi-Domain Specialist Synthesis Views */}
                {(orchestrationResult.decision_assessment.financial_view ||
                  orchestrationResult.decision_assessment.risk_view ||
                  orchestrationResult.decision_assessment.legal_view ||
                  orchestrationResult.decision_assessment.technology_view ||
                  orchestrationResult.decision_assessment.valuation_view ||
                  orchestrationResult.decision_assessment.synergy_integration_view) && (
                  <div className="space-y-3 pt-2">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-gray-400 flex items-center gap-1.5">
                      <Layers className="h-3.5 w-3.5 text-primary-400" />
                      Specialist Domain Synthesis Views
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                      {orchestrationResult.decision_assessment.financial_view && (
                        <div className="rounded-lg border border-surface-border bg-surface/40 p-3 space-y-1">
                          <span className="text-[10px] font-mono uppercase text-emerald-400 font-bold">Financial & QoE</span>
                          <p className="text-xs text-gray-300">{orchestrationResult.decision_assessment.financial_view}</p>
                        </div>
                      )}
                      {orchestrationResult.decision_assessment.risk_view && (
                        <div className="rounded-lg border border-surface-border bg-surface/40 p-3 space-y-1">
                          <span className="text-[10px] font-mono uppercase text-rose-400 font-bold">Risk Assessment</span>
                          <p className="text-xs text-gray-300">{orchestrationResult.decision_assessment.risk_view}</p>
                        </div>
                      )}
                      {orchestrationResult.decision_assessment.valuation_view && (
                        <div className="rounded-lg border border-surface-border bg-surface/40 p-3 space-y-1">
                          <span className="text-[10px] font-mono uppercase text-blue-400 font-bold">Valuation Multiples</span>
                          <p className="text-xs text-gray-300">{orchestrationResult.decision_assessment.valuation_view}</p>
                        </div>
                      )}
                      {orchestrationResult.decision_assessment.legal_view && (
                        <div className="rounded-lg border border-surface-border bg-surface/40 p-3 space-y-1">
                          <span className="text-[10px] font-mono uppercase text-amber-400 font-bold">Legal & Contracts</span>
                          <p className="text-xs text-gray-300">{orchestrationResult.decision_assessment.legal_view}</p>
                        </div>
                      )}
                      {orchestrationResult.decision_assessment.technology_view && (
                        <div className="rounded-lg border border-surface-border bg-surface/40 p-3 space-y-1">
                          <span className="text-[10px] font-mono uppercase text-purple-400 font-bold">Technology & Architecture</span>
                          <p className="text-xs text-gray-300">{orchestrationResult.decision_assessment.technology_view}</p>
                        </div>
                      )}
                      {orchestrationResult.decision_assessment.synergy_integration_view && (
                        <div className="rounded-lg border border-surface-border bg-surface/40 p-3 space-y-1">
                          <span className="text-[10px] font-mono uppercase text-cyan-400 font-bold">Synergies & 100-Day Plan</span>
                          <p className="text-xs text-gray-300">{orchestrationResult.decision_assessment.synergy_integration_view}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Required Conditions & Mitigations */}
                {((orchestrationResult.decision_assessment.required_conditions &&
                  orchestrationResult.decision_assessment.required_conditions.length > 0) ||
                  (orchestrationResult.decision_assessment.required_mitigations &&
                    orchestrationResult.decision_assessment.required_mitigations.length > 0)) && (
                  <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-4 space-y-2">
                    <h5 className="text-xs font-semibold text-amber-400 flex items-center gap-1.5">
                      <ShieldCheck className="h-3.5 w-3.5" />
                      Mandatory Pre-Closing Conditions & Escrow Covenants
                    </h5>
                    <ul className="space-y-1 text-xs text-gray-300">
                      {(orchestrationResult.decision_assessment.required_conditions || []).map((c, i) => (
                        <li key={`c-${i}`} className="flex items-start gap-2">
                          <span className="text-amber-400 mt-0.5">•</span>
                          <span>{c}</span>
                        </li>
                      ))}
                      {(orchestrationResult.decision_assessment.required_mitigations || []).map((m, i) => (
                        <li key={`m-${i}`} className="flex items-start gap-2">
                          <span className="text-amber-400 mt-0.5">•</span>
                          <span>{m}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Data Room Diligence Gaps */}
                {orchestrationResult.decision_assessment.data_gaps &&
                  orchestrationResult.decision_assessment.data_gaps.length > 0 && (
                    <div className="rounded-lg border border-orange-500/20 bg-orange-500/5 p-4 space-y-2">
                      <h5 className="text-xs font-semibold text-orange-400 flex items-center gap-1.5">
                        <AlertTriangle className="h-3.5 w-3.5" />
                        Identified Data Room Evidence Gaps ({orchestrationResult.decision_assessment.data_gaps.length})
                      </h5>
                      <ul className="space-y-1 text-xs text-gray-300">
                        {orchestrationResult.decision_assessment.data_gaps.map((g, i) => (
                          <li key={i} className="flex items-start gap-2">
                            <span className="text-orange-400 mt-0.5">•</span>
                            <span>{g}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                {/* Grounded Citations */}
                {orchestrationResult.decision_assessment.citations.length > 0 && (
                  <div className="space-y-2 pt-2">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-gray-400 flex items-center gap-1.5">
                      <FileCheck2 className="h-3.5 w-3.5 text-primary-400" />
                      Grounded Data Room Evidence ({orchestrationResult.decision_assessment.citations.length})
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {orchestrationResult.decision_assessment.citations.map((c, i) => (
                        <div
                          key={i}
                          className="rounded-lg border border-surface-border bg-surface/40 p-3 space-y-1"
                        >
                          <div className="flex items-center justify-between text-[11px] text-gray-400">
                            <span className="font-medium text-white">{c.document_name}</span>
                            <span className="font-mono text-primary-400">Page {c.page_number}</span>
                          </div>
                          <p className="text-xs italic text-gray-300">
                            &ldquo;{(c as any).exact_quote || c.quote}&rdquo;
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Specialist Outputs Quick Cards */}
              <div className="space-y-3">
                <h4 className="text-sm font-bold text-white flex items-center gap-2">
                  <Layers className="h-4 w-4 text-primary-400" />
                  Specialist Agent Outputs ({Object.keys(orchestrationResult.specialist_assessments).length})
                </h4>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {Object.entries(orchestrationResult.specialist_assessments).map(([id, assess]) => (
                    <div
                      key={id}
                      className="rounded-xl border border-surface-border bg-surface-card p-4 space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-white uppercase">{assess.domain}</span>
                        <span className="text-[10px] font-mono text-emerald-400">
                          {assess.execution_time_ms.toFixed(1)}ms
                        </span>
                      </div>
                      <p className="text-xs text-gray-400 line-clamp-3">{assess.summary}</p>
                      <div className="flex items-center justify-between pt-2 border-t border-surface-border text-[11px] text-gray-500">
                        <span>{assess.tools_invoked.length} tools</span>
                        <span className="text-primary-400 font-medium">
                          {(assess.confidence_score * 100).toFixed(0)}% conf
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="rounded-xl border border-dashed border-surface-border bg-surface-card/40 p-12 text-center space-y-3">
              <Network className="h-10 w-10 text-gray-500 mx-auto" />
              <h3 className="text-base font-semibold text-white">No Active Orchestration Run</h3>
              <p className="text-xs text-gray-400 max-w-md mx-auto">
                Click &ldquo;Execute Orchestration DAG&rdquo; above to trigger parallel specialist agent diligence across all 8 domains.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Tab Content: Specialist Agents Registry */}
      {activeTab === 'specialists' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {preDealAgents.map((agent) => (
            <div
              key={agent.agent_id}
              className="rounded-xl border border-surface-border bg-surface-card p-5 space-y-4"
            >
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-primary-400 font-mono">
                    {agent.domain}
                  </span>
                  <h4 className="text-base font-bold text-white">{agent.name}</h4>
                </div>
                <span className="rounded bg-surface px-2 py-0.5 text-[10px] font-mono text-gray-400 border border-surface-border">
                  v{agent.version}
                </span>
              </div>

              <p className="text-xs text-gray-300 leading-relaxed">{agent.purpose}</p>

              <div className="space-y-1.5">
                <div className="text-[11px] font-semibold uppercase text-gray-500">Authorized Tool Whitelist</div>
                <div className="flex flex-wrap gap-1.5">
                  {agent.allowed_tools.map((t) => (
                    <span
                      key={t}
                      className="rounded bg-surface px-2 py-0.5 text-[10px] font-mono text-emerald-400 border border-emerald-500/20"
                    >
                      {t}
                    </span>
                  ))}
                </div>
              </div>

              <div className="pt-2 border-t border-surface-border text-[11px] text-gray-400">
                <span className="font-semibold text-gray-300">Confidence Policy: </span>
                {agent.confidence_policy}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab Content: ML & XAI Foundation */}
      {activeTab === 'ml' && (
        <div className="space-y-6">
          <div className="rounded-xl border border-surface-border bg-surface-card p-4 space-y-1">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Cpu className="h-4 w-4 text-primary-400" />
              Machine Learning Predictive Intelligence & XAI Console
            </h3>
            <p className="text-xs text-gray-400">
              Empirical ML models trained with reproducible tabular pipelines, statistical baseline comparisons, and real TreeSHAP / LinearSHAP explainability.
            </p>
          </div>

          {/* Active Prediction Result Card */}
          {mlPredictionResult && (
            <div className="rounded-xl border border-primary-500/30 bg-primary-950/10 p-5 space-y-4">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <span className="text-[10px] font-mono font-semibold uppercase text-primary-400">
                    Latest Inference Result &bull; {mlPredictionResult.task_type}
                  </span>
                  <h4 className="text-base font-bold text-white">Model: {mlPredictionResult.model_id}</h4>
                </div>
                <div className="text-right">
                  <span className="text-xs font-mono font-semibold text-emerald-400">
                    {(mlPredictionResult.prediction_confidence * 100).toFixed(1)}% Confidence
                  </span>
                </div>
              </div>

              {/* Prediction Output & Probabilities */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="rounded-lg border border-surface-border bg-surface/50 p-3 space-y-1">
                  <span className="text-[11px] text-gray-400 uppercase font-semibold">Predicted Value / Class</span>
                  <div className="text-lg font-bold text-white font-mono">
                    {typeof mlPredictionResult.predicted_value === 'number'
                      ? mlPredictionResult.predicted_value.toLocaleString()
                      : String(mlPredictionResult.predicted_value)}
                  </div>
                </div>

                {mlPredictionResult.probability_distribution && (
                  <div className="rounded-lg border border-surface-border bg-surface/50 p-3 space-y-1">
                    <span className="text-[11px] text-gray-400 uppercase font-semibold">Probability Distribution</span>
                    <div className="flex gap-3 text-xs font-mono text-gray-300">
                      {Object.entries(mlPredictionResult.probability_distribution).map(([k, v]) => (
                        <span key={k} className={v > 0.4 ? 'text-amber-400 font-bold' : 'text-emerald-400 font-bold'}>
                          {k}: {(v * 100).toFixed(1)}%
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {mlPredictionResult.confidence_interval && (
                  <div className="rounded-lg border border-surface-border bg-surface/50 p-3 space-y-1">
                    <span className="text-[11px] text-gray-400 uppercase font-semibold">95% Uncertainty Interval</span>
                    <div className="text-xs font-mono text-gray-300">
                      [{mlPredictionResult.confidence_interval[0].toLocaleString()} &ndash; {mlPredictionResult.confidence_interval[1].toLocaleString()}]
                    </div>
                  </div>
                )}
              </div>

              {/* SHAP Feature Attribution Visualization */}
              {mlPredictionResult.explanation && (
                <div className="space-y-3 pt-3 border-t border-surface-border">
                  <div className="flex items-center justify-between">
                    <h5 className="text-xs font-bold uppercase tracking-wider text-gray-300 flex items-center gap-1.5">
                      <Sparkles className="h-3.5 w-3.5 text-primary-400" />
                      Grounded SHAP Feature Attribution ({mlPredictionResult.explanation.method})
                    </h5>
                  </div>

                  <p className="text-xs italic text-gray-300 bg-surface/40 p-3 rounded-lg border border-surface-border">
                    &ldquo;{mlPredictionResult.explanation.narrative_summary}&rdquo;
                  </p>

                  <div className="space-y-2">
                    {mlPredictionResult.explanation.top_features.map((feat) => (
                      <div key={feat.feature_name} className="space-y-1">
                        <div className="flex items-center justify-between text-[11px] font-mono">
                          <span className="text-gray-300">{feat.feature_name}</span>
                          <span className={feat.direction === 'POSITIVE' ? 'text-rose-400' : 'text-emerald-400'}>
                            {feat.direction} ({feat.importance_score.toFixed(4)})
                          </span>
                        </div>
                        <div className="h-1.5 w-full rounded-full bg-surface-border overflow-hidden">
                          <div
                            className={cn(
                              'h-full rounded-full',
                              feat.direction === 'POSITIVE' ? 'bg-rose-500' : 'bg-emerald-500'
                            )}
                            style={{ width: `${Math.min(100, feat.importance_score * 100)}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Model Catalog Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {mlModels.map((model) => {
              const isTrained = model.status === 'VALIDATED' || model.status === 'TRAINED' || Object.keys(model.evaluation_metrics).length > 0;
              const isRunning = runningMLModelId === model.model_id;

              return (
                <div
                  key={model.model_id}
                  className="rounded-xl border border-surface-border bg-surface-card p-5 space-y-3 flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <span className="text-[10px] font-mono font-semibold uppercase text-primary-400">
                          {model.task_type}
                        </span>
                        <h4 className="text-sm font-bold text-white">{model.name}</h4>
                      </div>
                      <span
                        className={cn(
                          'rounded px-2 py-0.5 text-[10px] font-semibold border',
                          isTrained
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                            : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                        )}
                      >
                        {isTrained ? 'TRAINED & VALIDATED' : 'DATASET REQUIRED'}
                      </span>
                    </div>

                    <div className="text-[11px] text-gray-400 font-mono">
                      Framework: <span className="text-white">{model.framework}</span> (v{model.version})
                    </div>

                    <div className="space-y-1">
                      <div className="text-[10px] font-semibold uppercase text-gray-500">
                        Feature Schema ({model.feature_names.length})
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {model.feature_names.slice(0, 4).map((f) => (
                          <span key={f} className="rounded bg-surface px-1.5 py-0.5 text-[10px] font-mono text-gray-300">
                            {f}
                          </span>
                        ))}
                        {model.feature_names.length > 4 && (
                          <span className="text-[10px] text-gray-500 font-mono">+{model.feature_names.length - 4} more</span>
                        )}
                      </div>
                    </div>

                    {isTrained ? (
                      <div className="pt-2 border-t border-surface-border space-y-1 text-[11px] font-mono">
                        <span className="text-gray-500 uppercase text-[10px] font-semibold">Test Evaluation Metrics:</span>
                        <div className="flex flex-wrap gap-2 text-emerald-400 font-semibold">
                          {Object.entries(model.evaluation_metrics).map(([k, v]) => (
                            <span key={k} className="bg-surface px-1.5 py-0.5 rounded border border-surface-border">
                              {k.toUpperCase()}: {typeof v === 'number' ? v.toFixed(3) : v}
                            </span>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <div className="pt-2 border-t border-surface-border text-[11px] text-amber-400/80 italic">
                        Specification initialized &bull; Awaiting customer historical accounting/telemetry dataset.
                      </div>
                    )}
                  </div>

                  {isTrained && (
                    <div className="pt-3 border-t border-surface-border">
                      <button
                        onClick={() => handleRunMLPrediction(model.model_id)}
                        disabled={isRunning || !selectedDealId}
                        className={cn(
                          'w-full inline-flex items-center justify-center gap-2 rounded-lg px-3 py-1.5 text-xs font-semibold shadow-sm transition-colors',
                          isRunning
                            ? 'bg-primary-500/50 text-white cursor-not-allowed'
                            : 'bg-primary-600 text-white hover:bg-primary-500'
                        )}
                      >
                        {isRunning ? (
                          <>
                            <RefreshCw className="h-3 w-3 animate-spin" />
                            Executing ML Inference...
                          </>
                        ) : (
                          <>
                            <Sparkles className="h-3 w-3" />
                            Execute Deal Prediction & SHAP
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Tab Content: Post-Deal Extensibility */}
      {activeTab === 'extensibility' && (
        <div className="space-y-4">
          <div className="rounded-xl border border-surface-border bg-surface-card p-4 space-y-1">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-primary-400" />
              Post-Acquisition Corporate Value Creation Registry
            </h3>
            <p className="text-xs text-gray-400">
              Clean modular extension points supporting company growth, customer retention, pricing elasticity, and continuous performance telemetry.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {postDealAgents.map((agent) => (
              <div
                key={agent.agent_id}
                className="rounded-xl border border-surface-border bg-surface-card p-5 space-y-3"
              >
                <div>
                  <span className="text-[10px] font-mono font-semibold uppercase text-purple-400">
                    {agent.domain}
                  </span>
                  <h4 className="text-sm font-bold text-white">{agent.name}</h4>
                </div>
                <p className="text-xs text-gray-300">{agent.purpose}</p>
                <div className="space-y-1">
                  <div className="text-[10px] font-semibold uppercase text-gray-500">Planned Tools</div>
                  <div className="flex flex-wrap gap-1">
                    {agent.allowed_tools.map((t) => (
                      <span key={t} className="rounded bg-surface px-1.5 py-0.5 text-[10px] font-mono text-purple-300 border border-purple-500/20">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
