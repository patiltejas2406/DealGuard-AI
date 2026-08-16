import React from 'react';
import type { Metadata } from 'next';
import './globals.css';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';
import { AuthProvider } from '@/lib/auth-context';

export const metadata: Metadata = {
  title: 'DealGuard AI — Institutional M&A Intelligence & Post-Deal Value Creation',
  description:
    'Evidence-grounded M&A due diligence, deterministic financial analysis, 17-pillar risk scoring, valuation, and 100-day value creation platform.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background text-gray-100 antialiased">
        <AuthProvider>
          <Header />
          <div className="flex">
            <Sidebar />
            <main className="flex-1 overflow-y-auto p-8">{children}</main>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
