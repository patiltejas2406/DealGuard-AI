import React from 'react';
import { cn } from '@/lib/utils';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'outline';
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'md',
  className,
  ...props
}) => {
  const variantStyles = {
    default: 'bg-surface-elevated text-gray-300 border-surface-border',
    success: 'bg-emerald-950/60 text-emerald-400 border-emerald-800/50',
    warning: 'bg-amber-950/60 text-amber-400 border-amber-800/50',
    danger: 'bg-red-950/60 text-red-400 border-red-800/50',
    info: 'bg-blue-950/60 text-blue-400 border-blue-800/50',
    outline: 'bg-transparent text-gray-400 border-surface-border',
  };

  const sizeStyles = {
    sm: 'px-2 py-0.5 text-xs font-mono',
    md: 'px-2.5 py-1 text-xs font-medium font-mono',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded border tracking-wide uppercase',
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
};
