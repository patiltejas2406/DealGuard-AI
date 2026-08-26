'use client';

/**
 * DealGuard AI — Phase 11: 100-Day Post-Acquisition Integration Execution Command Center
 */

import React, { useEffect, useState } from 'react';
import {
  Calendar,
  Layers,
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
  ChevronRight,
  Sparkles,
  Link as LinkIcon,
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { api } from '@/lib/api';
import {
  BlockerResponse,
  CriticalPathResponse,
  Deal,
  ExecutiveAttentionResponse,
  IntegrationHealthResponse,
  IntegrationProgramResponse,
  MilestoneResponse,
  TimelineStageResponse,
  WorkstreamResponse,
} from '@/types';

type ActiveTab = 'TIMELINE' | 'WORKSTREAMS' | 'MILESTONES' | 'CRITICAL_PATH' | 'ESCALATIONS';

const WORKSTREAM_CATEGORIES = [
  'EXECUTIVE_GOVERNANCE',
  'FINANCE_ACCOUNTING',
  'TECHNOLOGY_IT',
  'DATA_SYSTEMS',
  'SALES',
  'MARKETING',
  'CUSTOMER_SUCCESS',
  'PRODUCT',
  'OPERATIONS',
  'PROCUREMENT',
  'HUMAN_RESOURCES',
  'LEGAL_COMPLIANCE',
  'CYBERSECURITY',
  'ERP_CRM_INTEGRATION',
  'COMMUNICATIONS',
  'SYNERGY_REALIZATION',
  'BUSINESS_CONTINUITY',
];

export default function IntegrationPage() {
  // Deals & Program State
  const [deals, setDeals] = useState<Deal[]>([]);
  const [selectedDealId, setSelectedDealId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<ActiveTab>('TIMELINE');

  // Integration Data State
  const [program, setProgram] = useState<IntegrationProgramResponse | null>(null);
  const [workstreams, setWorkstreams] = useState<WorkstreamResponse[]>([]);
  const [milestones, setMilestones] = useState<MilestoneResponse[]>([]);
  const [timeline, setTimeline] = useState<TimelineStageResponse | null>(null);
  const [criticalPath, setCriticalPath] = useState<CriticalPathResponse | null>(null);
  const [healthData, setHealthData] = useState<IntegrationHealthResponse | null>(null);
  const [escalations, setEscalations] = useState<ExecutiveAttentionResponse | null>(null);
  const [blockers, setBlockers] = useState<BlockerResponse[]>([]);

  // Filter State
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');

  // Modals State
  const [isCreateWsOpen, setIsCreateWsOpen] = useState<boolean>(false);
  const [isCreateMilestoneOpen, setIsCreateMilestoneOpen] = useState<boolean>(false);
  const [isAddDepOpen, setIsAddDepOpen] = useState<boolean>(false);
  const [isReportBlockerOpen, setIsReportBlockerOpen] = useState<boolean>(false);
  const [isResolveBlockerOpen, setIsResolveBlockerOpen] = useState<boolean>(false);
  const [activeBlockerForResolve, setActiveBlockerForResolve] = useState<BlockerResponse | null>(null);

  // Form State: Workstream
  const [wsName, setWsName] = useState<string>('');
  const [wsCategory, setWsCategory] = useState<string>('FINANCE_ACCOUNTING');
  const [wsPriority, setWsPriority] = useState<'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'>('HIGH');
  const [wsOwner, setWsOwner] = useState<string>('');
  const [wsStartDay, setWsStartDay] = useState<number>(0);
  const [wsTargetDay, setWsTargetDay] = useState<number>(100);

  // Form State: Milestone
  const [mWorkstreamId, setMWorkstreamId] = useState<string>('');
  const [mName, setMName] = useState<string>('');
  const [mTargetDay, setMTargetDay] = useState<number>(30);
  const [mPriority, setMPriority] = useState<'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'>('HIGH');
  const [mOwner, setMOwner] = useState<string>('');
  const [mDeliverable, setMDeliverable] = useState<string>('');

  // Form State: Dependency
  const [depPredId, setDepPredId] = useState<string>('');
  const [depSuccId, setDepSuccId] = useState<string>('');

  // Form State: Blocker
  const [bWorkstreamId, setBWorkstreamId] = useState<string>('');
  const [bMilestoneId, setBMilestoneId] = useState<string>('');
  const [bTitle, setBTitle] = useState<string>('');
  const [bDescription, setBDescription] = useState<string>('');
  const [bSeverity, setBSeverity] = useState<'CRITICAL' | 'HIGH' | 'MEDIUM'>('HIGH');
  const [bOwner, setBOwner] = useState<string>('');

  // Form State: Resolve
  const [resolveNotes, setResolveNotes] = useState<string>('');

  // Feedback State
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

  // 2. Load Integration Data whenever deal changes
  useEffect(() => {
    if (!selectedDealId) return;
    loadAllIntegrationData(selectedDealId);
  }, [selectedDealId]);

  async function loadAllIntegrationData(dealId: string) {
    setIsLoading(true);
    setError(null);
    try {
      const [prog, wsList, mList, timeRes, cpRes, hRes, escRes, bList] = await Promise.all([
        api.getIntegrationProgram(dealId),
        api.getWorkstreams(dealId),
        api.getMilestones(dealId),
        api.getTimeline(dealId),
        api.getCriticalPath(dealId),
        api.getIntegrationHealth(dealId),
        api.getExecutiveAttention(dealId),
        api.getBlockers(dealId),
      ]);
      setProgram(prog);
      setWorkstreams(wsList);
      setMilestones(mList);
      setTimeline(timeRes);
      setCriticalPath(cpRes);
      setHealthData(hRes);
      setEscalations(escRes);
      setBlockers(bList);

      if (wsList.length > 0 && !mWorkstreamId) {
        setMWorkstreamId(wsList[0].id);
        setBWorkstreamId(wsList[0].id);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to load integration data.');
    } finally {
      setIsLoading(false);
    }
  }

  // 3. Create Workstream
  async function handleCreateWorkstream(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedDealId || !wsName) return;
    setIsSubmitting(true);
    try {
      await api.createWorkstream(selectedDealId, {
        name: wsName,
        category: wsCategory,
        priority: wsPriority,
        owner: wsOwner,
        start_day: wsStartDay,
        target_day: wsTargetDay,
      });
      setSuccessMessage(`Workstream '${wsName}' created.`);
      setIsCreateWsOpen(false);
      setWsName('');
      loadAllIntegrationData(selectedDealId);
    } catch (err: any) {
      setError(err?.message || 'Failed to create workstream.');
    } finally {
      setIsSubmitting(false);
    }
  }

  // 4. Create Milestone
  async function handleCreateMilestone(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedDealId || !mName || !mWorkstreamId) return;
    setIsSubmitting(true);
    try {
      await api.createMilestone(selectedDealId, {
        workstream_id: mWorkstreamId,
        name: mName,
        target_day: mTargetDay,
        priority: mPriority,
        owner: mOwner,
        deliverable: mDeliverable,
      });
      setSuccessMessage(`Milestone '${mName}' added.`);
      setIsCreateMilestoneOpen(false);
      setMName('');
      setMDeliverable('');
      loadAllIntegrationData(selectedDealId);
    } catch (err: any) {
      setError(err?.message || 'Failed to add milestone.');
    } finally {
      setIsSubmitting(false);
    }
  }

  // 5. Update Milestone Status
  async function handleUpdateMilestoneStatus(milestoneId: string, status: string, compPct: number) {
    if (!selectedDealId) return;
    try {
      await api.updateMilestoneStatus(selectedDealId, milestoneId, {
        status,
        completion_pct: compPct,
      });
      setSuccessMessage('Milestone updated.');
      loadAllIntegrationData(selectedDealId);
    } catch (err: any) {
      setError(err?.message || 'Failed to update milestone.');
    }
  }

  // 6. Create Dependency
  async function handleCreateDependency(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedDealId || !depPredId || !depSuccId) return;
    setIsSubmitting(true);
    try {
      await api.createDependency(selectedDealId, {
        predecessor_id: depPredId,
        successor_id: depSuccId,
        dependency_type: 'FINISH_TO_START',
      });
      setSuccessMessage('Dependency link established.');
      setIsAddDepOpen(false);
      loadAllIntegrationData(selectedDealId);
    } catch (err: any) {
      setError(err?.message || 'Dependency creation failed.');
    } finally {
      setIsSubmitting(false);
    }
  }

  // 7. Report Blocker
  async function handleReportBlocker(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedDealId || !bTitle || !bWorkstreamId) return;
    setIsSubmitting(true);
    try {
      await api.reportBlocker(selectedDealId, {
        workstream_id: bWorkstreamId,
        milestone_id: bMilestoneId || undefined,
        title: bTitle,
        description: bDescription,
        severity: bSeverity,
        owner: bOwner,
      });
      setSuccessMessage(`Blocker '${bTitle}' reported.`);
      setIsReportBlockerOpen(false);
      setBTitle('');
      setBDescription('');
      loadAllIntegrationData(selectedDealId);
    } catch (err: any) {
      setError(err?.message || 'Failed to report blocker.');
    } finally {
      setIsSubmitting(false);
    }
  }

  // 8. Resolve Blocker
  async function handleResolveBlocker(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedDealId || !activeBlockerForResolve || !resolveNotes) return;
    setIsSubmitting(true);
    try {
      await api.resolveBlocker(selectedDealId, activeBlockerForResolve.id, {
        resolution_notes: resolveNotes,
      });
      setSuccessMessage('Blocker resolved.');
      setIsResolveBlockerOpen(false);
      setActiveBlockerForResolve(null);
      setResolveNotes('');
      loadAllIntegrationData(selectedDealId);
    } catch (err: any) {
      setError(err?.message || 'Failed to resolve blocker.');
    } finally {
      setIsSubmitting(false);
    }
  }

  const getHealthBandBadge = (band: string) => {
    switch (band) {
      case 'HEALTHY':
        return <Badge variant="success" size="sm">HEALTHY</Badge>;
      case 'WATCH':
        return <Badge variant="info" size="sm">WATCH</Badge>;
      case 'AT_RISK':
        return <Badge variant="warning" size="sm">AT RISK</Badge>;
      case 'CRITICAL':
        return <Badge variant="danger" size="sm">CRITICAL</Badge>;
      default:
        return <Badge variant="default" size="sm">{band}</Badge>;
    }
  };

  const filteredWorkstreams = workstreams.filter((w) =>
    categoryFilter === 'ALL' ? true : w.category === categoryFilter
  );

  return (
    <div className="min-h-screen bg-surface-base text-slate-100 p-6 space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 border-b border-slate-800 pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <Calendar className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2 font-mono">
                100-Day Integration Command Center
                <Badge variant="success" size="sm">Phase 11 Engine v1.0</Badge>
              </h1>
              <p className="text-xs text-slate-400">
                Deterministic Execution DAGs, 100-Day Milestones, Critical Path Analysis & Executive Escalations
              </p>
            </div>
          </div>
        </div>

        {/* Workspace & Action Controls */}
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
            onClick={() => setIsCreateWsOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow font-mono transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            Add Workstream
          </button>

          <button
            type="button"
            onClick={() => setIsCreateMilestoneOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold border border-slate-700 font-mono transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            Add Milestone
          </button>

          <button
            type="button"
            onClick={() => setIsReportBlockerOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-950/60 hover:bg-rose-900/60 text-rose-300 text-xs font-semibold border border-rose-800/60 font-mono transition-colors"
          >
            <AlertTriangle className="w-3.5 h-3.5" />
            Report Blocker
          </button>

          <button
            type="button"
            onClick={() => selectedDealId && loadAllIntegrationData(selectedDealId)}
            className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Program Summary Cards Grid */}
      {program && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3 font-mono">
          <Card className="p-3.5 bg-slate-900/90 border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-500 uppercase">Integration Health</span>
            <div className="flex items-center gap-2">
              <p className="text-xl font-bold text-white">{program.health_score.toFixed(0)}/100</p>
              {getHealthBandBadge(program.health_band)}
            </div>
            <span className="text-[10px] text-slate-400">Deterministic Metric</span>
          </Card>

          <Card className="p-3.5 bg-slate-900/90 border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-500 uppercase">Program Timeline</span>
            <p className="text-xl font-bold text-emerald-400">Day {program.current_day_offset} / 100</p>
            <span className="text-[10px] text-slate-400">{100 - program.current_day_offset} Days Remaining</span>
          </Card>

          <Card className="p-3.5 bg-slate-900/90 border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-500 uppercase">Active Workstreams</span>
            <p className="text-xl font-bold text-blue-400">{program.total_workstreams}</p>
            <span className="text-[10px] text-slate-400">17-Pillar Coverage</span>
          </Card>

          <Card className="p-3.5 bg-slate-900/90 border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-500 uppercase">Milestones Completed</span>
            <p className="text-xl font-bold text-white">
              {program.completed_milestones} / {program.total_milestones}
            </p>
            <span className="text-[10px] text-slate-400">{program.overall_progress_pct}% Overall Progress</span>
          </Card>

          <Card className="p-3.5 bg-slate-900/90 border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-500 uppercase">Critical Path Duration</span>
            <p className="text-xl font-bold text-amber-400">{program.critical_path_duration_days} Days</p>
            <span className="text-[10px] text-slate-400">DAG Longest Sequence</span>
          </Card>

          <Card className="p-3.5 bg-slate-900/90 border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-500 uppercase">Open Blockers</span>
            <p className="text-xl font-bold text-rose-400">{program.open_blockers}</p>
            <span className="text-[10px] text-slate-400">{program.overdue_milestones} Overdue Milestones</span>
          </Card>
        </div>
      )}

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2 text-xs font-mono">
        <button
          onClick={() => setActiveTab('TIMELINE')}
          className={`px-3.5 py-1.5 rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === 'TIMELINE'
              ? 'bg-emerald-600 text-white font-bold shadow'
              : 'text-slate-400 hover:text-white hover:bg-slate-900'
          }`}
        >
          <Calendar className="w-3.5 h-3.5" />
          100-Day Timeline
        </button>
        <button
          onClick={() => setActiveTab('WORKSTREAMS')}
          className={`px-3.5 py-1.5 rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === 'WORKSTREAMS'
              ? 'bg-emerald-600 text-white font-bold shadow'
              : 'text-slate-400 hover:text-white hover:bg-slate-900'
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          Workstreams ({workstreams.length})
        </button>
        <button
          onClick={() => setActiveTab('MILESTONES')}
          className={`px-3.5 py-1.5 rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === 'MILESTONES'
              ? 'bg-emerald-600 text-white font-bold shadow'
              : 'text-slate-400 hover:text-white hover:bg-slate-900'
          }`}
        >
          <CheckCircle2 className="w-3.5 h-3.5" />
          Milestones ({milestones.length})
        </button>
        <button
          onClick={() => setActiveTab('CRITICAL_PATH')}
          className={`px-3.5 py-1.5 rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === 'CRITICAL_PATH'
              ? 'bg-emerald-600 text-white font-bold shadow'
              : 'text-slate-400 hover:text-white hover:bg-slate-900'
          }`}
        >
          <GitBranch className="w-3.5 h-3.5" />
          Critical Path DAG
        </button>
        <button
          onClick={() => setActiveTab('ESCALATIONS')}
          className={`px-3.5 py-1.5 rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === 'ESCALATIONS'
              ? 'bg-emerald-600 text-white font-bold shadow'
              : 'text-slate-400 hover:text-white hover:bg-slate-900'
          }`}
        >
          <Flame className="w-3.5 h-3.5 text-rose-400" />
          Executive Attention ({escalations?.total_attention_items || 0})
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

      {/* TAB 1: 100-DAY TIMELINE */}
      {activeTab === 'TIMELINE' && timeline && (
        <div className="space-y-4 font-mono">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Stage 1: Day 0 */}
            <Card className="p-4 bg-slate-900/90 border-slate-800 space-y-3">
              <div className="border-b border-slate-800 pb-2 flex items-center justify-between">
                <span className="font-bold text-xs text-white">DAY 0: CLOSE</span>
                <Badge variant="default" size="sm">Completion</Badge>
              </div>
              <div className="space-y-2">
                {timeline.stages.DAY_0_CLOSE.length === 0 ? (
                  <p className="text-[10px] text-slate-500 italic">No Day 0 milestones</p>
                ) : (
                  timeline.stages.DAY_0_CLOSE.map((m) => (
                    <div key={m.id} className="p-2 rounded bg-slate-950 border border-slate-800 space-y-1">
                      <div className="text-xs font-bold text-slate-200">{m.name}</div>
                      <div className="flex items-center justify-between text-[10px] text-slate-400">
                        <span>Day {m.target_day}</span>
                        <span className="text-emerald-400 font-bold">{m.status}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </Card>

            {/* Stage 2: Days 1-30 Stabilize */}
            <Card className="p-4 bg-slate-900/90 border-slate-800 space-y-3">
              <div className="border-b border-slate-800 pb-2 flex items-center justify-between">
                <span className="font-bold text-xs text-emerald-400">DAYS 1–30: STABILIZE</span>
                <Badge variant="success" size="sm">{timeline.stages.DAYS_1_30_STABILIZE.length} Items</Badge>
              </div>
              <div className="space-y-2">
                {timeline.stages.DAYS_1_30_STABILIZE.map((m) => (
                  <div key={m.id} className="p-2.5 rounded bg-slate-950 border border-slate-800 space-y-1.5">
                    <div className="text-xs font-bold text-slate-200">{m.name}</div>
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="text-slate-400">Day {m.target_day} • {m.owner || 'Unassigned'}</span>
                      <span className={`font-bold ${m.status === 'COMPLETED' ? 'text-emerald-400' : 'text-amber-400'}`}>
                        {m.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* Stage 3: Days 31-60 Integrate */}
            <Card className="p-4 bg-slate-900/90 border-slate-800 space-y-3">
              <div className="border-b border-slate-800 pb-2 flex items-center justify-between">
                <span className="font-bold text-xs text-blue-400">DAYS 31–60: INTEGRATE</span>
                <Badge variant="info" size="sm">{timeline.stages.DAYS_31_60_INTEGRATE.length} Items</Badge>
              </div>
              <div className="space-y-2">
                {timeline.stages.DAYS_31_60_INTEGRATE.map((m) => (
                  <div key={m.id} className="p-2.5 rounded bg-slate-950 border border-slate-800 space-y-1.5">
                    <div className="text-xs font-bold text-slate-200">{m.name}</div>
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="text-slate-400">Day {m.target_day} • {m.owner || 'Unassigned'}</span>
                      <span className={`font-bold ${m.status === 'COMPLETED' ? 'text-emerald-400' : 'text-blue-400'}`}>
                        {m.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* Stage 4: Days 61-100 Optimize */}
            <Card className="p-4 bg-slate-900/90 border-slate-800 space-y-3">
              <div className="border-b border-slate-800 pb-2 flex items-center justify-between">
                <span className="font-bold text-xs text-purple-400">DAYS 61–100: OPTIMIZE</span>
                <Badge variant="default" size="sm">{timeline.stages.DAYS_61_100_OPTIMIZE.length} Items</Badge>
              </div>
              <div className="space-y-2">
                {timeline.stages.DAYS_61_100_OPTIMIZE.map((m) => (
                  <div key={m.id} className="p-2.5 rounded bg-slate-950 border border-slate-800 space-y-1.5">
                    <div className="text-xs font-bold text-slate-200">{m.name}</div>
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="text-slate-400">Day {m.target_day} • {m.owner || 'Unassigned'}</span>
                      <span className={`font-bold ${m.status === 'COMPLETED' ? 'text-emerald-400' : 'text-purple-400'}`}>
                        {m.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* TAB 2: WORKSTREAMS REGISTER */}
      {activeTab === 'WORKSTREAMS' && (
        <Card className="p-5 bg-slate-900/90 border-slate-800 space-y-4 font-mono">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">Filter Category:</span>
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 focus:outline-none cursor-pointer"
              >
                <option value="ALL">ALL (17 Pillars)</option>
                {WORKSTREAM_CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <span className="text-xs text-slate-400">
              Showing {filteredWorkstreams.length} of {workstreams.length} Workstreams
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {filteredWorkstreams.map((ws) => (
              <div key={ws.id} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3 flex flex-col justify-between">
                <div className="space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-xs font-bold text-white">{ws.name}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                      ws.priority === 'CRITICAL' ? 'bg-rose-950 text-rose-400 border border-rose-800/80' : 'bg-slate-800 text-slate-400'
                    }`}>
                      {ws.priority}
                    </span>
                  </div>
                  <div className="text-[10px] text-slate-400">{ws.category}</div>
                  {ws.owner && <div className="text-[10px] text-slate-500">Lead: {ws.owner}</div>}
                </div>

                <div className="space-y-2 border-t border-slate-900 pt-2">
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="text-slate-400">Days {ws.start_day}–{ws.target_day}</span>
                    <span className="text-emerald-400 font-bold">{ws.progress_pct}%</span>
                  </div>
                  <div className="w-full h-1 bg-slate-900 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${ws.progress_pct}%` }} />
                  </div>
                  <div className="flex items-center justify-between text-[10px] pt-1">
                    <span className="text-slate-400">{ws.completed_milestones_count}/{ws.milestones_count} Milestones</span>
                    <span className={`font-bold ${
                      ws.status === 'BLOCKED' ? 'text-rose-400' : ws.status === 'COMPLETED' ? 'text-emerald-400' : 'text-blue-400'
                    }`}>
                      {ws.status}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* TAB 3: MILESTONES TABLE */}
      {activeTab === 'MILESTONES' && (
        <Card className="p-5 bg-slate-900/90 border-slate-800 space-y-4 font-mono">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <span className="text-xs font-bold text-white">Integration Deliverables & Milestones ({milestones.length})</span>
            <button
              onClick={() => setIsAddDepOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 text-xs text-blue-300 font-semibold"
            >
              <LinkIcon className="w-3.5 h-3.5" />
              Add Dependency Link
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-[10px] uppercase text-slate-500 border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">Milestone Deliverable</th>
                  <th className="py-2.5 px-3">Target Day / Stage</th>
                  <th className="py-2.5 px-3">Owner</th>
                  <th className="py-2.5 px-3">Priority</th>
                  <th className="py-2.5 px-3">Completion %</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40">
                {milestones.map((m) => (
                  <tr key={m.id} className="hover:bg-slate-800/30">
                    <td className="py-3 px-3">
                      <div className="font-bold text-white">{m.name}</div>
                      {m.deliverable && <div className="text-[10px] text-slate-500">{m.deliverable}</div>}
                    </td>
                    <td className="py-3 px-3">
                      <div className="font-bold text-emerald-400">Day {m.target_day}</div>
                      <div className="text-[10px] text-slate-500">{m.stage}</div>
                    </td>
                    <td className="py-3 px-3 text-slate-300">{m.owner || 'Unassigned'}</td>
                    <td className="py-3 px-3">
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                        m.priority === 'CRITICAL' ? 'bg-rose-950 text-rose-400 border border-rose-800/80' : 'bg-slate-800 text-slate-400'
                      }`}>
                        {m.priority}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-bold text-white">{m.completion_pct}%</td>
                    <td className="py-3 px-3">
                      <select
                        value={m.status}
                        onChange={(e) => handleUpdateMilestoneStatus(m.id, e.target.value, e.target.value === 'COMPLETED' ? 100.0 : m.completion_pct)}
                        className="bg-slate-950 border border-slate-800 rounded px-1.5 py-0.5 text-[10px] text-slate-300 focus:outline-none cursor-pointer"
                      >
                        <option value="NOT_STARTED">NOT_STARTED</option>
                        <option value="IN_PROGRESS">IN_PROGRESS</option>
                        <option value="AT_RISK">AT_RISK</option>
                        <option value="BLOCKED">BLOCKED</option>
                        <option value="COMPLETED">COMPLETED</option>
                        <option value="OVERDUE">OVERDUE</option>
                      </select>
                    </td>
                    <td className="py-3 px-3 text-right">
                      {m.status !== 'COMPLETED' ? (
                        <button
                          onClick={() => handleUpdateMilestoneStatus(m.id, 'COMPLETED', 100.0)}
                          className="px-2 py-1 rounded bg-emerald-950 text-emerald-400 hover:bg-emerald-900 text-[10px] font-bold"
                        >
                          Complete
                        </button>
                      ) : (
                        <span className="text-[10px] text-emerald-500 font-bold">Done</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* TAB 4: CRITICAL PATH DAG */}
      {activeTab === 'CRITICAL_PATH' && criticalPath && (
        <Card className="p-5 bg-slate-900/90 border-slate-800 space-y-4 font-mono">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h2 className="text-sm font-semibold text-white flex items-center gap-2">
                <GitBranch className="w-4 h-4 text-amber-400" />
                Critical Path Sequence (Longest Chain)
              </h2>
              <p className="text-xs text-slate-400">
                Deterministic DAG traversal identifies the sequence of milestones that dictate total program duration.
              </p>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-right">
              <span className="text-slate-500 text-[10px] uppercase block">Critical Duration</span>
              <span className="text-amber-400 font-bold text-sm">{criticalPath.critical_path_duration_days} Days</span>
            </div>
          </div>

          <div className="space-y-3">
            {criticalPath.critical_milestones.map((m, idx) => (
              <div key={m.id} className="flex items-center gap-3">
                <div className="w-6 h-6 rounded-full bg-amber-500/20 border border-amber-500 text-amber-400 flex items-center justify-center font-bold text-xs shrink-0">
                  {idx + 1}
                </div>
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex-1 flex items-center justify-between">
                  <div>
                    <div className="text-xs font-bold text-white">{m.name}</div>
                    <div className="text-[10px] text-slate-400">Day {m.target_day} • Priority: {m.priority}</div>
                  </div>
                  <span className={`text-[10px] font-bold ${m.status === 'COMPLETED' ? 'text-emerald-400' : 'text-amber-400'}`}>
                    {m.status}
                  </span>
                </div>
                {idx < criticalPath.critical_milestones.length - 1 && (
                  <ArrowRight className="w-4 h-4 text-slate-600 shrink-0" />
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* TAB 5: ESCALATIONS & BLOCKERS */}
      {activeTab === 'ESCALATIONS' && escalations && (
        <div className="space-y-4 font-mono">
          {/* Executive Escalations List */}
          <Card className="p-5 bg-slate-900/90 border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-sm font-semibold text-white flex items-center gap-2">
                <Flame className="w-4 h-4 text-rose-400" />
                Steering Committee Attention Queue ({escalations.total_attention_items})
              </h2>
            </div>

            <div className="space-y-2">
              {escalations.critical_items.map((item, idx) => (
                <div key={idx} className="p-3.5 rounded-lg bg-rose-950/30 border border-rose-800/80 text-rose-200 flex items-start justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Badge variant="danger" size="sm">CRITICAL</Badge>
                      <span className="font-bold text-xs text-white">{item.title}</span>
                    </div>
                    <p className="text-xs text-rose-300">{item.description}</p>
                    <div className="text-[10px] text-slate-400">Workstream: {item.workstream_name} • Owner: {item.owner}</div>
                  </div>
                  <span className="text-[10px] bg-rose-950 px-2 py-1 rounded text-rose-300 font-bold shrink-0">
                    Action: {item.action_required}
                  </span>
                </div>
              ))}
            </div>
          </Card>

          {/* Open Blockers Table */}
          <Card className="p-5 bg-slate-900/90 border-slate-800 space-y-4">
            <span className="text-xs font-bold text-white">Active Operational Blockers ({blockers.length})</span>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="text-[10px] uppercase text-slate-500 border-b border-slate-800">
                  <tr>
                    <th className="py-2 px-3">Blocker Title</th>
                    <th className="py-2 px-3">Severity</th>
                    <th className="py-2 px-3">Status</th>
                    <th className="py-2 px-3">Owner</th>
                    <th className="py-2 px-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/40">
                  {blockers.map((b) => (
                    <tr key={b.id} className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-3 font-bold text-white">{b.title}</td>
                      <td className="py-2.5 px-3">
                        <span className={`text-[10px] font-bold ${b.severity === 'CRITICAL' ? 'text-rose-400' : 'text-amber-400'}`}>
                          {b.severity}
                        </span>
                      </td>
                      <td className="py-2.5 px-3">
                        <span className={`text-[10px] font-bold ${b.status === 'RESOLVED' ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {b.status}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-slate-400">{b.owner || 'Unassigned'}</td>
                      <td className="py-2.5 px-3 text-right">
                        {b.status === 'OPEN' && (
                          <button
                            onClick={() => {
                              setActiveBlockerForResolve(b);
                              setIsResolveBlockerOpen(true);
                            }}
                            className="px-2 py-1 rounded bg-emerald-950 text-emerald-300 hover:bg-emerald-900 text-[10px] font-bold"
                          >
                            Resolve
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* CREATE WORKSTREAM MODAL */}
      {isCreateWsOpen && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn font-mono text-xs">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-xl shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white">Add Integration Workstream</h3>
              <button onClick={() => setIsCreateWsOpen(false)} className="text-slate-400 hover:text-white">
                <XCircle className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleCreateWorkstream} className="space-y-3">
              <div>
                <label className="text-[10px] uppercase text-slate-400 block mb-1">Workstream Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. ERP & Financial Reporting Harmonization"
                  value={wsName}
                  onChange={(e) => setWsName(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-white"
                />
              </div>

              <div>
                <label className="text-[10px] uppercase text-slate-400 block mb-1">Category (17 Pillars)</label>
                <select
                  value={wsCategory}
                  onChange={(e) => setWsCategory(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-200"
                >
                  {WORKSTREAM_CATEGORIES.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] uppercase text-slate-400 block mb-1">Priority</label>
                  <select
                    value={wsPriority}
                    onChange={(e: any) => setWsPriority(e.target.value)}
                    className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-200"
                  >
                    <option value="CRITICAL">CRITICAL</option>
                    <option value="HIGH">HIGH</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="LOW">LOW</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] uppercase text-slate-400 block mb-1">Owner</label>
                  <input
                    type="text"
                    placeholder="e.g. Sarah Jenkins"
                    value={wsOwner}
                    onChange={(e) => setWsOwner(e.target.value)}
                    className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-200"
                  />
                </div>
              </div>

              <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
                <button type="button" onClick={() => setIsCreateWsOpen(false)} className="px-3 py-1.5 rounded bg-slate-800 text-slate-300">
                  Cancel
                </button>
                <button type="submit" disabled={isSubmitting} className="px-4 py-1.5 rounded bg-emerald-600 text-white font-bold">
                  {isSubmitting ? 'Creating...' : 'Save Workstream'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* CREATE MILESTONE MODAL */}
      {isCreateMilestoneOpen && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn font-mono text-xs">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-xl shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white">Add 100-Day Milestone</h3>
              <button onClick={() => setIsCreateMilestoneOpen(false)} className="text-slate-400 hover:text-white">
                <XCircle className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleCreateMilestone} className="space-y-3">
              <div>
                <label className="text-[10px] uppercase text-slate-400 block mb-1">Workstream *</label>
                <select
                  value={mWorkstreamId}
                  onChange={(e) => setMWorkstreamId(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-200"
                >
                  {workstreams.map((w) => (
                    <option key={w.id} value={w.id}>{w.name} ({w.category})</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-[10px] uppercase text-slate-400 block mb-1">Milestone Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Completed Chart of Accounts Alignment"
                  value={mName}
                  onChange={(e) => setMName(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] uppercase text-slate-400 block mb-1">Target Day (0-100) *</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={mTargetDay}
                    onChange={(e) => setMTargetDay(parseInt(e.target.value) || 0)}
                    className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-200"
                  />
                </div>
                <div>
                  <label className="text-[10px] uppercase text-slate-400 block mb-1">Owner</label>
                  <input
                    type="text"
                    value={mOwner}
                    onChange={(e) => setMOwner(e.target.value)}
                    className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-200"
                  />
                </div>
              </div>

              <div>
                <label className="text-[10px] uppercase text-slate-400 block mb-1">Deliverable Summary</label>
                <input
                  type="text"
                  placeholder="e.g. Signed sign-off document from CFO"
                  value={mDeliverable}
                  onChange={(e) => setMDeliverable(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-200"
                />
              </div>

              <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
                <button type="button" onClick={() => setIsCreateMilestoneOpen(false)} className="px-3 py-1.5 rounded bg-slate-800 text-slate-300">
                  Cancel
                </button>
                <button type="submit" disabled={isSubmitting} className="px-4 py-1.5 rounded bg-emerald-600 text-white font-bold">
                  {isSubmitting ? 'Adding...' : 'Save Milestone'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ADD DEPENDENCY MODAL */}
      {isAddDepOpen && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn font-mono text-xs">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-xl shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white">Add DAG Dependency Link</h3>
              <button onClick={() => setIsAddDepOpen(false)} className="text-slate-400 hover:text-white">
                <XCircle className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleCreateDependency} className="space-y-3">
              <div>
                <label className="text-[10px] uppercase text-slate-400 block mb-1">Predecessor Milestone (Must Finish First)</label>
                <select
                  value={depPredId}
                  onChange={(e) => setDepPredId(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-200"
                >
                  <option value="">Select Predecessor...</option>
                  {milestones.map((m) => (
                    <option key={m.id} value={m.id}>Day {m.target_day}: {m.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-[10px] uppercase text-slate-400 block mb-1">Successor Milestone (Depends On Predecessor)</label>
                <select
                  value={depSuccId}
                  onChange={(e) => setDepSuccId(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-200"
                >
                  <option value="">Select Successor...</option>
                  {milestones.map((m) => (
                    <option key={m.id} value={m.id}>Day {m.target_day}: {m.name}</option>
                  ))}
                </select>
              </div>

              <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
                <button type="button" onClick={() => setIsAddDepOpen(false)} className="px-3 py-1.5 rounded bg-slate-800 text-slate-300">
                  Cancel
                </button>
                <button type="submit" disabled={isSubmitting || !depPredId || !depSuccId} className="px-4 py-1.5 rounded bg-emerald-600 text-white font-bold">
                  {isSubmitting ? 'Validating DAG...' : 'Link Dependency'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* REPORT BLOCKER MODAL */}
      {isReportBlockerOpen && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn font-mono text-xs">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-xl shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white text-rose-400">Report Operational Blocker</h3>
              <button onClick={() => setIsReportBlockerOpen(false)} className="text-slate-400 hover:text-white">
                <XCircle className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleReportBlocker} className="space-y-3">
              <div>
                <label className="text-[10px] uppercase text-slate-400 block mb-1">Workstream *</label>
                <select
                  value={bWorkstreamId}
                  onChange={(e) => setBWorkstreamId(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-200"
                >
                  {workstreams.map((w) => (
                    <option key={w.id} value={w.id}>{w.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-[10px] uppercase text-slate-400 block mb-1">Blocker Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. ERP Vendor Refusing Schema Access"
                  value={bTitle}
                  onChange={(e) => setBTitle(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] uppercase text-slate-400 block mb-1">Severity</label>
                  <select
                    value={bSeverity}
                    onChange={(e: any) => setBSeverity(e.target.value)}
                    className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-200"
                  >
                    <option value="CRITICAL">CRITICAL</option>
                    <option value="HIGH">HIGH</option>
                    <option value="MEDIUM">MEDIUM</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] uppercase text-slate-400 block mb-1">Owner</label>
                  <input
                    type="text"
                    value={bOwner}
                    onChange={(e) => setBOwner(e.target.value)}
                    className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-200"
                  />
                </div>
              </div>

              <div>
                <label className="text-[10px] uppercase text-slate-400 block mb-1">Description</label>
                <textarea
                  rows={2}
                  value={bDescription}
                  onChange={(e) => setBDescription(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-200"
                />
              </div>

              <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
                <button type="button" onClick={() => setIsReportBlockerOpen(false)} className="px-3 py-1.5 rounded bg-slate-800 text-slate-300">
                  Cancel
                </button>
                <button type="submit" disabled={isSubmitting} className="px-4 py-1.5 rounded bg-rose-600 text-white font-bold">
                  {isSubmitting ? 'Reporting...' : 'Save Blocker'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* RESOLVE BLOCKER MODAL */}
      {isResolveBlockerOpen && activeBlockerForResolve && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn font-mono text-xs">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-xl shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white">Resolve: {activeBlockerForResolve.title}</h3>
              <button onClick={() => setIsResolveBlockerOpen(false)} className="text-slate-400 hover:text-white">
                <XCircle className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleResolveBlocker} className="space-y-3">
              <div>
                <label className="text-[10px] uppercase text-slate-400 block mb-1">Resolution Notes *</label>
                <textarea
                  rows={3}
                  required
                  placeholder="Document the resolution, work-around, or executive approval..."
                  value={resolveNotes}
                  onChange={(e) => setResolveNotes(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-200"
                />
              </div>
              <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
                <button type="button" onClick={() => setIsResolveBlockerOpen(false)} className="px-3 py-1.5 rounded bg-slate-800 text-slate-300">
                  Cancel
                </button>
                <button type="submit" disabled={isSubmitting} className="px-4 py-1.5 rounded bg-emerald-600 text-white font-bold">
                  {isSubmitting ? 'Resolving...' : 'Confirm Resolution'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
