'use client';

/**
 * DealGuard AI Enterprise Authentication Login View
 */

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Shield, Lock, Mail, AlertCircle, ArrowRight, CheckCircle2, Server } from 'lucide-react';
import { useAuth } from '@/lib/auth-context';
import { getApiBaseUrl } from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const { login, isAuthenticated } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [activeApiUrl, setActiveApiUrl] = useState<string>('');

  useEffect(() => {
    setActiveApiUrl(getApiBaseUrl());
  }, []);

  // If already logged in, redirect to workspace
  useEffect(() => {
    if (isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setIsSubmitting(true);

    try {
      await login(email, password);
      router.push('/');
    } catch (err: any) {
      setErrorMsg(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const fillCredentials = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setErrorMsg(null);
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Subtle Background Radial Glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        <div className="flex items-center justify-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white font-mono">
              DEALGUARD <span className="text-emerald-400">AI</span>
            </h1>
            <p className="text-xs text-slate-400 font-mono tracking-wide uppercase">
              M&A Intelligence & Diligence Platform
            </p>
          </div>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        <div className="bg-slate-900 border border-slate-800 py-8 px-4 shadow-2xl sm:rounded-2xl sm:px-10">
          <div className="mb-6">
            <h2 className="text-lg font-semibold text-white">Sign In to Institutional Workspace</h2>
            <p className="text-sm text-slate-400 mt-1">
              Enter your enterprise credentials to access active deal rooms and risk models.
            </p>
          </div>

          {errorMsg && (
            <div className="mb-6 p-4 rounded-lg bg-rose-500/10 border border-rose-500/30 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div className="text-sm text-rose-200">{errorMsg}</div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5 font-mono">
                Corporate Email
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="analyst@firm.com"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-10 pr-3 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5 font-mono">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-10 pr-3 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full mt-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold py-2.5 px-4 rounded-lg shadow-lg shadow-emerald-500/20 transition-all flex items-center justify-center gap-2 text-sm disabled:opacity-50"
            >
              {isSubmitting ? (
                <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  Authenticate Session
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Quick-Fill Seed Fixture Profiles for Demo / Evaluation */}
          <div className="mt-8 pt-6 border-t border-slate-800">
            <p className="text-xs font-mono uppercase text-slate-400 mb-3 tracking-wider">
              Quick-Fill Synthetic Evaluation Accounts
            </p>
            <div className="space-y-2">
              <button
                type="button"
                onClick={() => fillCredentials('admin@dealguard.ai', 'DemoPassword123!')}
                className="w-full text-left p-2.5 rounded-lg bg-slate-950/80 border border-slate-800 hover:border-slate-700 hover:bg-slate-800/50 transition-colors flex items-center justify-between text-xs"
              >
                <div>
                  <div className="font-semibold text-slate-200">Alex Vance (Tenant Admin)</div>
                  <div className="text-slate-500 font-mono">admin@dealguard.ai</div>
                </div>
                <span className="px-2 py-0.5 text-[10px] font-mono bg-emerald-950 text-emerald-400 border border-emerald-800 rounded">
                  ADMIN
                </span>
              </button>

              <button
                type="button"
                onClick={() => fillCredentials('analyst@dealguard.ai', 'DemoPassword123!')}
                className="w-full text-left p-2.5 rounded-lg bg-slate-950/80 border border-slate-800 hover:border-slate-700 hover:bg-slate-800/50 transition-colors flex items-center justify-between text-xs"
              >
                <div>
                  <div className="font-semibold text-slate-200">Sarah Chen (M&A Analyst)</div>
                  <div className="text-slate-500 font-mono">analyst@dealguard.ai</div>
                </div>
                <span className="px-2 py-0.5 text-[10px] font-mono bg-sky-950 text-sky-400 border border-sky-800 rounded">
                  ANALYST
                </span>
              </button>

              <button
                type="button"
                onClick={() => fillCredentials('reviewer@dealguard.ai', 'DemoPassword123!')}
                className="w-full text-left p-2.5 rounded-lg bg-slate-950/80 border border-slate-800 hover:border-slate-700 hover:bg-slate-800/50 transition-colors flex items-center justify-between text-xs"
              >
                <div>
                  <div className="font-semibold text-slate-200">Marcus Brody (IC Reviewer)</div>
                  <div className="text-slate-500 font-mono">reviewer@dealguard.ai</div>
                </div>
                <span className="px-2 py-0.5 text-[10px] font-mono bg-amber-950 text-amber-400 border border-amber-800 rounded">
                  REVIEWER
                </span>
              </button>
            </div>
          </div>

          {/* Connection Target Indicator */}
          {activeApiUrl && (
            <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-[10px] font-mono text-slate-500">
              <span className="flex items-center gap-1.5 truncate">
                <Server className="w-3 h-3 text-emerald-500 shrink-0" />
                <span className="truncate">{activeApiUrl}</span>
              </span>
              <span className="text-emerald-500 font-semibold uppercase shrink-0">TLS Active</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
