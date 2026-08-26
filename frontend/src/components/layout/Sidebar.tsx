'use client';

import React from 'react';
import { usePathname } from 'next/navigation';
import {
  Briefcase,
  TrendingUp,
  AlertTriangle,
  Sliders,
  Sparkles,
  Calendar,
  Scale,
  Cpu,
  Bot,
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
  badge?: string;
  badgeVariant?: 'default' | 'primary' | 'success' | 'warning';
}

const navItems: NavItem[] = [
  { name: 'Data Room & Deals', icon: Briefcase, href: '/' },
  { name: '3-Statements & QoE', icon: TrendingUp, href: '/financials', badge: 'Deterministic' },
  { name: 'Valuation Lab', icon: Layers, href: '/valuation', badge: 'Multi-Method' },
  { name: 'Risk Intelligence', icon: AlertTriangle, href: '/risks', badge: '17 Pillars' },
  { name: 'Decision Intelligence', icon: Shield, href: '/decision', badge: 'Composite' },
  { name: 'What-If Simulator', icon: Sliders, href: '/scenarios', badge: 'Monte Carlo' },
  { name: 'Value Creation', icon: Sparkles, href: '/synergies', badge: 'Waterfall' },
  { name: '100-Day Integration', icon: Calendar, href: '/integration', badge: 'Execution' },
  { name: 'Legal & Contracts', icon: Scale, href: '/legal', badge: 'Evidence' },
  { name: 'Tech & Architecture', icon: Cpu, href: '/technology', badge: 'Architecture' },
  { name: 'AI Deal Copilot', icon: Bot, href: '/copilot', badge: 'Streaming' },
  { name: 'Audit & Citations', icon: FileCheck2, href: '#', badge: 'Immutable' },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();

  return (
    <aside className="flex h-[calc(100vh-3.5rem)] w-64 flex-col border-r border-surface-border bg-surface px-3 py-4">
      <div className="mb-4 px-3">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-gray-500 font-mono">
          Intelligence Layers
        </p>
      </div>

      <nav className="flex-1 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = item.href !== '#' && (pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href)));
          
          return (
            <a
              key={item.name}
              href={item.href}
              className={cn(
                'group flex items-center justify-between rounded-md px-3 py-2 text-xs font-medium transition-colors',
                isActive
                  ? 'bg-surface-elevated text-white border border-surface-border'
                  : 'text-gray-400 hover:bg-surface-elevated/50 hover:text-gray-200'
              )}
            >
              <div className="flex items-center gap-2.5">
                <Icon className={cn('h-4 w-4', isActive ? 'text-primary-500' : 'text-gray-500')} />
                <span>{item.name}</span>
              </div>
              {item.badge && (
                <span className={cn(
                  "rounded px-1.5 py-0.5 text-[10px] font-mono",
                  isActive ? "bg-emerald-950 text-emerald-400 border border-emerald-800" : "bg-surface-border text-gray-400"
                )}>
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
          <span>Enterprise Tenant Guard</span>
        </div>
      </div>
    </aside>
  );
};
