'use client';

import React, { useEffect, useState } from 'react';
import {
  ShieldAlert,
  TrendingUp,
  CheckCircle2,
  AlertCircle,
  Database,
  Cpu,
  Layers,
  ArrowRight,
  GitBranch,
  TerminalSquare,
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { api } from '@/lib/api';
import { SystemHealth, SystemInfo } from '@/types';

export default function HomePage() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function checkStatus() {
      try {
        setLoading(true);
        const [healthRes, infoRes] = await Promise.all([
          api.getHealth(),
          api.getSystemInfo(),
        ]);
        setHealth(healthRes);
        setSystemInfo(infoRes);
        setError(null);
      } catch (err: any) {
        setError(err.message || 'Failed to connect to DealGuard Backend.');
      } finally {
        setLoading(false);
      }
    }

    checkStatus();
  }, []);

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      {/* Platform Header Banner */}
      <div className="flex flex-col gap-2 border-b border-surface-border pb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Executive Deal Room & Architecture Console
            </h1>
            <p className="text-sm text-gray-400">
              AI-Powered M&A Due Diligence, Deal Intelligence & Post-Deal Value Creation
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="outline" size="md">
              RELEASE CANDIDATE: PHASE 1
            </Badge>
            <div className="flex items-center gap-1.5 rounded bg-surface-elevated px-3 py-1.5 text-xs font-mono text-gray-300 border border-surface-border">
              <GitBranch className="h-3.5 w-3.5 text-primary-500" />
              <span>main: frozen-baseline</span>
            </div>
          </div>
        </div>
      </div>

      {/* Connection & Architecture Status Banner */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <Card className="flex items-center gap-4 border-surface-border bg-surface">
          <div className="flex h-10 w-10 items-center justify-center rounded bg-primary-950/60 text-primary-500 border border-primary-800/40">
            <CheckCircle2 className="h-5 w-5" />
          </div>
          <div>
            <p className="text-[11px] font-mono uppercase tracking-wider text-gray-400">Backend API</p>
            <p className="text-sm font-semibold text-white">
              {loading ? 'Probing...' : health ? 'FastAPI 0.110+ Live' : 'Offline'}
            </p>
          </div>
        </Card>

        <Card className="flex items-center gap-4 border-surface-border bg-surface">
          <div className="flex h-10 w-10 items-center justify-center rounded bg-blue-950/60 text-blue-400 border border-blue-800/40">
            <Database className="h-5 w-5" />
          </div>
          <div>
            <p className="text-[11px] font-mono uppercase tracking-wider text-gray-400">Vector Storage</p>
            <p className="text-sm font-semibold text-white">
              {systemInfo?.ai_spec.vector_store || 'pgvector 1536d'}
            </p>
          </div>
        </Card>

        <Card className="flex items-center gap-4 border-surface-border bg-surface">
          <div className="flex h-10 w-10 items-center justify-center rounded bg-amber-950/60 text-amber-400 border border-amber-800/40">
            <Cpu className="h-5 w-5" />
          </div>
          <div>
            <p className="text-[11px] font-mono uppercase tracking-wider text-gray-400">Calc Engine</p>
            <p className="text-sm font-semibold text-white">Pure Python (Deterministic)</p>
          </div>
        </Card>

        <Card className="flex items-center gap-4 border-surface-border bg-surface">
          <div className="flex h-10 w-10 items-center justify-center rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800/40">
            <Layers className="h-5 w-5" />
          </div>
          <div>
            <p className="text-[11px] font-mono uppercase tracking-wider text-gray-400">Async Engine</p>
            <p className="text-sm font-semibold text-white">Celery + Redis</p>
          </div>
        </Card>
      </div>

      {/* 4-Layer Intelligence Pipeline Blueprint */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-white">Institutional Diligence Pipeline</h2>
          <span className="text-xs font-mono text-gray-400">End-to-End Decision Framework</span>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          <Card className="space-y-3 border-surface-border bg-surface">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-primary-500 font-semibold">LAYER 1</span>
              <Badge variant="outline" size="sm">Pre-Deal</Badge>
            </div>
            <h3 className="text-sm font-semibold text-white">Forensic Ingestion</h3>
            <p className="text-xs text-gray-400 leading-relaxed">
              Multi-format parsing (PDF/XLSX), 3-statement reconciliation, and Quality of Earnings (QoE) normalization.
            </p>
            <div className="pt-2">
              <span className="text-[11px] font-mono text-gray-500">Output: Clean Fact Records</span>
            </div>
          </Card>

          <Card className="space-y-3 border-surface-border bg-surface">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-amber-400 font-semibold">LAYER 2</span>
              <Badge variant="outline" size="sm">Intelligence</Badge>
            </div>
            <h3 className="text-sm font-semibold text-white">Risk & Valuation</h3>
            <p className="text-xs text-gray-400 leading-relaxed">
              17-pillar explainable risk scoring and multi-method valuation (DCF, CCA Multiples, Precedents).
            </p>
            <div className="pt-2">
              <span className="text-[11px] font-mono text-gray-500">Output: DealGuard Score (0–100)</span>
            </div>
          </Card>

          <Card className="space-y-3 border-surface-border bg-surface">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-blue-400 font-semibold">LAYER 3</span>
              <Badge variant="outline" size="sm">Simulation</Badge>
            </div>
            <h3 className="text-sm font-semibold text-white">What-If Modeling</h3>
            <p className="text-xs text-gray-400 leading-relaxed">
              Real-time multi-variable sensitivity engine calculating instant delta vectors on EV, FCF, and leverage.
            </p>
            <div className="pt-2">
              <span className="text-[11px] font-mono text-gray-500">Output: Baseline vs Delta</span>
            </div>
          </Card>

          <Card className="space-y-3 border-surface-border bg-surface">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-emerald-400 font-semibold">LAYER 4</span>
              <Badge variant="outline" size="sm">Value Creation</Badge>
            </div>
            <h3 className="text-sm font-semibold text-white">Post-Deal Strategy</h3>
            <p className="text-xs text-gray-400 leading-relaxed">
              6-strategy BU/Product diagnostic matrix (Invest/Grow/Optimize/Exit) and 100-day phase-gated execution plan.
            </p>
            <div className="pt-2">
              <span className="text-[11px] font-mono text-gray-500">Output: 100-Day Playbook</span>
            </div>
          </Card>
        </div>
      </div>

      {/* Active System Specifications */}
      <Card className="space-y-4 border-surface-border bg-surface">
        <div className="flex items-center justify-between border-b border-surface-border pb-3">
          <div className="flex items-center gap-2">
            <TerminalSquare className="h-4 w-4 text-primary-500" />
            <h3 className="text-sm font-semibold text-white">System Configuration & Security Profile</h3>
          </div>
          <Badge variant="success" size="sm">Verified Baseline</Badge>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-3 text-xs font-mono">
          <div className="space-y-1">
            <span className="text-gray-500 uppercase">Embedding Configuration</span>
            <p className="text-gray-200">{systemInfo?.ai_spec.embedding_model || 'Gemini Embedding 2'}</p>
            <p className="text-gray-400">Dimensions: {systemInfo?.ai_spec.embedding_dimension || 1536}</p>
          </div>
          <div className="space-y-1">
            <span className="text-gray-500 uppercase">Authentication & RBAC</span>
            <p className="text-gray-200">Hasher: {systemInfo?.security.password_hasher || 'Argon2id'}</p>
            <p className="text-gray-400">{systemInfo?.security.tenant_isolation || 'Server-Side Org & Deal Scoped'}</p>
          </div>
          <div className="space-y-1">
            <span className="text-gray-500 uppercase">Task Execution Engine</span>
            <p className="text-gray-200">{systemInfo?.background_jobs.engine || 'Celery + Redis'}</p>
            <p className="text-gray-400">States: Queued, Running, Succeeded, Failed</p>
          </div>
        </div>
      </Card>
    </div>
  );
}
