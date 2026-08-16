import React from 'react';
import { cn } from '@/lib/utils';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hover?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  className,
  hover = false,
  ...props
}) => {
  return (
    <div
      className={cn(
        'rounded-lg border border-surface-border bg-surface p-5 shadow-sm',
        hover && 'transition-colors hover:border-gray-600 hover:bg-surface-elevated',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};
