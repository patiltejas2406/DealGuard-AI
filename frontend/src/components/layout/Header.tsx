'use client';

import React from 'react';
import Link from 'next/navigation';
import { ShieldCheck, Lock, Database, LogOut, User as UserIcon, Building2, ChevronDown } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { useAuth } from '@/lib/auth-context';

export const Header: React.FC = () => {
  const { user, organization, role, accessibleOrganizations, switchOrganization, logout, isAuthenticated } = useAuth();
  const [showOrgDropdown, setShowOrgDropdown] = React.useState(false);

  const getRoleVariant = (roleName?: string | null) => {
    switch (roleName?.toUpperCase()) {
      case 'ADMIN':
        return 'success';
      case 'ANALYST':
      case 'FINANCIAL_ANALYST':
        return 'info';
      case 'REVIEWER':
        return 'warning';
      case 'AUDITOR':
        return 'default';
      default:
        return 'default';
    }
  };


  return (
    <header className="sticky top-0 z-40 flex h-14 w-full items-center justify-between border-b border-surface-border bg-surface/95 px-6 backdrop-blur">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded bg-emerald-500/20 text-emerald-400 ring-1 ring-emerald-500/30">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold tracking-tight text-white font-mono">DEALGUARD AI</span>
              <Badge variant="success" size="sm">Phase 9</Badge>
            </div>
          </div>
        </div>

        {/* Top Nav Links */}
        <nav className="hidden md:flex items-center gap-1 pl-4 border-l border-slate-800 text-xs font-mono">
          <a
            href="/"
            className="px-3 py-1 rounded-md text-slate-300 hover:text-white hover:bg-slate-900 transition-colors"
          >
            Data Room
          </a>
          <a
            href="/financials"
            className="px-3 py-1 rounded-md text-slate-300 hover:text-white hover:bg-slate-900 transition-colors"
          >
            3-Statements & QoE
          </a>
          <a
            href="/valuation"
            className="px-3 py-1 rounded-md text-slate-300 hover:text-white hover:bg-slate-900 transition-colors"
          >
            Valuation Intelligence
          </a>
          <a
            href="/risks"
            className="px-3 py-1 rounded-md text-slate-300 hover:text-white hover:bg-slate-900 transition-colors"
          >
            Risk Intelligence
          </a>
          <a
            href="/decision"
            className="px-3 py-1 rounded-md text-slate-300 hover:text-white hover:bg-slate-900 transition-colors"
          >
            Decision Score
          </a>
          <a
            href="/scenarios"
            className="px-3 py-1 rounded-md text-emerald-400 bg-emerald-950/40 border border-emerald-800/40 hover:bg-emerald-900/40 transition-colors font-semibold"
          >
            Scenario Lab
          </a>
        </nav>
      </div>



      <div className="flex items-center gap-4 text-xs">
        <div className="hidden lg:flex items-center gap-1.5 font-mono text-gray-400">
          <Database className="h-3.5 w-3.5 text-primary-500" />
          <span>PostgreSQL + pgvector (1536d)</span>
        </div>
        
        <div className="hidden lg:block h-3.5 w-[1px] bg-surface-border" />

        {isAuthenticated && user ? (
          <div className="flex items-center gap-3">
            {/* Organization Switcher */}
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowOrgDropdown(!showOrgDropdown)}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-200 transition-colors"
              >
                <Building2 className="w-3.5 h-3.5 text-emerald-400" />
                <span className="font-medium max-w-[120px] truncate">{organization?.name || 'Organization'}</span>
                {accessibleOrganizations.length > 1 && <ChevronDown className="w-3 h-3 text-slate-400" />}
              </button>

              {showOrgDropdown && accessibleOrganizations.length > 1 && (
                <div className="absolute right-0 mt-1.5 w-56 rounded-lg bg-slate-900 border border-slate-800 shadow-xl py-1 z-50">
                  <div className="px-3 py-1.5 text-[10px] uppercase font-mono tracking-wider text-slate-400 border-b border-slate-800">
                    Switch Organization
                  </div>
                  {accessibleOrganizations.map((org) => (
                    <button
                      key={org.id}
                      onClick={() => {
                        switchOrganization(org.id);
                        setShowOrgDropdown(false);
                      }}
                      className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-slate-800/80 transition-colors ${
                        org.id === organization?.id ? 'text-emerald-400 bg-slate-800/40 font-semibold' : 'text-slate-300'
                      }`}
                    >
                      <span className="truncate">{org.name}</span>
                      <span className="text-[10px] font-mono text-slate-500">{org.role}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Role Badge */}
            <Badge variant={getRoleVariant(role)} size="sm">
              {role || 'MEMBER'}
            </Badge>

            {/* User Details */}
            <div className="flex items-center gap-2 pl-2 border-l border-surface-border">
              <div className="text-right">
                <div className="font-medium text-slate-200 leading-tight">{user.full_name}</div>
                <div className="text-[10px] text-slate-500 font-mono truncate max-w-[130px]">{user.email}</div>
              </div>
              <button
                type="button"
                onClick={() => logout()}
                title="Revoke session and sign out"
                className="p-1.5 rounded text-slate-400 hover:text-rose-400 hover:bg-rose-950/30 transition-colors"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        ) : (
          <a
            href="/login"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20 font-mono font-medium transition-colors"
          >
            <Lock className="w-3.5 h-3.5" />
            <span>Sign In</span>
          </a>
        )}
      </div>
    </header>
  );
};
