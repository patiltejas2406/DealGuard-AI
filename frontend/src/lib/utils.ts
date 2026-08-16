import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(
  amount: number,
  currency: string = 'USD',
  compact: boolean = false
): string {
  if (compact) {
    if (Math.abs(amount) >= 1_000_000_000) {
      return `${(amount / 1_000_000_000).toFixed(1)}B ${currency}`;
    }
    if (Math.abs(amount) >= 1_000_000) {
      return `${(amount / 1_000_000).toFixed(1)}M ${currency}`;
    }
    if (Math.abs(amount) >= 1_000) {
      return `${(amount / 1_000).toFixed(1)}K ${currency}`;
    }
  }

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatPercent(value: number, decimals: number = 1): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

export function formatMultiple(value: number, decimals: number = 1): string {
  return `${value.toFixed(decimals)}x`;
}
