import React from 'react';
import {
  Briefcase,
  TrendingUp,
  AlertTriangle,
  Sliders,
  Sparkles,
  FileText,
  Shield,
  Layers,
  FileCheck2,
  Terminal,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface NavItem {
  name: string;
  icon: React.ComponentType<{ className?: string }>;
  href: string;
  active?: boolean;
  badge?: string;
}

const navItems: NavItem[] = [
  { name: 'Deal Overview', icon: Briefcase, href: '#', active: true },
  { name: 'Financial Engine', icon: TrendingUp, href: '#', badge: 'Deterministic' },
  { name: 'Risk Intelligence', icon: AlertTriangle, href: '#', badge: '17 Pillars' },
  { name: 'Valuation Lab', icon: Layers, href: '#' },
  { name: 'What-If Simulator', icon: Sliders, href: '#' },
  { name: 'Value Creation', icon: Sparkles, href: '#', badge: '100-Day' },
  { name: 'Data Room & RAG', icon: FileText, href: '#' },
  { name: 'Audit & Citations', icon: FileCheck2, href: '#' },
  { name: 'System Telemetry', icon: Terminal, href: '#' },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="flex h-[calc(100vh-3.5rem)] w-64 flex-col border-r border-surface-border bg-surface px-3 py-4">
      <div className="mb-4 px-3">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-gray-500 font-mono">
          Deal Navigation
        </p>
      </div>

      <nav className="flex-1 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <a
              key={item.name}
              href={item.href}
              className={cn(
                'group flex items-center justify-between rounded-md px-3 py-2 text-xs font-medium transition-colors',
                item.active
                  ? 'bg-surface-elevated text-white border border-surface-border'
                  : 'text-gray-400 hover:bg-surface-elevated/50 hover:text-gray-200'
              )}
            >
              <div className="flex items-center gap-2.5">
                <Icon className={cn('h-4 w-4', item.active ? 'text-primary-500' : 'text-gray-500')} />
                <span>{item.name}</span>
              </div>
              {item.badge && (
                <span className="rounded bg-surface-border px-1.5 py-0.5 text-[10px] font-mono text-gray-300">
                  {item.badge}
                </span>
              )}
            </a>
          );
        })}
      </nav>

      <div className="border-t border-surface-border pt-4 px-3">
        <div className="flex items-center gap-2 text-[11px] text-gray-500 font-mono">
          <Shield className="h-3.5 w-3.5 text-primary-500" />
          <span>Tenant: Institutional Alpha</span>
        </div>
      </div>
    </aside>
  );
};
