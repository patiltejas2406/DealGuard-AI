'use client';

/**
 * DealGuard AI — Executive Deal Room & Document Ingestion Console
 */

import React, { useEffect, useState } from 'react';
import {
  Shield,
  FileText,
  Upload,
  Search,
  CheckCircle2,
  AlertCircle,
  Clock,
  Layers,
  Sparkles,
  Database,
  ArrowRight,
  RefreshCw,
  FolderOpen,
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import { Deal, DocumentChunkItem, DocumentItem, JobExecutionItem, SemanticSearchResult, SystemHealth } from '@/types';

export default function HomePage() {
  const { isAuthenticated, user, organization, role } = useAuth();

  const [deals, setDeals] = useState<Deal[]>([]);
  const [selectedDealId, setSelectedDealId] = useState<string | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loadingDeals, setLoadingDeals] = useState(false);
  const [loadingDocs, setLoadingDocs] = useState(false);

  // Ingestion State
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [category, setCategory] = useState<string>('FINANCIAL');
  const [isUploading, setIsUploading] = useState(false);
  const [activeJob, setActiveJob] = useState<JobExecutionItem | null>(null);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);

  // Semantic Search State
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SemanticSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  // Health
  const [health, setHealth] = useState<SystemHealth | null>(null);

  useEffect(() => {
    loadHealthAndDeals();
  }, [isAuthenticated, organization]);

  useEffect(() => {
    if (selectedDealId) {
      loadDocuments(selectedDealId);
    }
  }, [selectedDealId]);

  const loadHealthAndDeals = async () => {
    try {
      const healthRes = await api.getHealth().catch(() => null);
      setHealth(healthRes);

      if (isAuthenticated) {
        setLoadingDeals(true);
        const dealList = await api.getDeals();
        setDeals(dealList);
        if (dealList.length > 0 && !selectedDealId) {
          setSelectedDealId(dealList[0].id);
        }
      }
    } catch (err) {
      console.error('Failed to load deals', err);
    } finally {
      setLoadingDeals(false);
    }
  };

  const loadDocuments = async (dealId: string) => {
    try {
      setLoadingDocs(true);
      const docList = await api.getDealDocuments(dealId);
      setDocuments(docList);
    } catch (err) {
      console.error('Failed to load documents', err);
    } finally {
      setLoadingDocs(false);
    }
  };

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile || !selectedDealId) return;

    setIsUploading(true);
    setUploadMessage(null);

    try {
      const res = await api.uploadDocument(selectedDealId, uploadFile, category);
      setActiveJob(res.job);
      setUploadMessage(`Document '${res.document.name}' successfully ingested & indexed!`);
      setUploadFile(null);
      await loadDocuments(selectedDealId);
    } catch (err: any) {
      setUploadMessage(`Upload error: ${err.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim() || !selectedDealId) return;

    setIsSearching(true);
    try {
      const results = await api.searchDealEvidence(selectedDealId, searchQuery, 4);
      setSearchResults(results);
    } catch (err) {
      console.error('Search error', err);
    } finally {
      setIsSearching(false);
    }
  };

  const selectedDeal = deals.find((d) => d.id === selectedDealId);

  return (
    <div className="mx-auto max-w-7xl space-y-8 pb-12">
      {/* Workspace Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-surface-border pb-6">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white font-mono">
              Deal Intelligence & Evidence Data Room
            </h1>
            <Badge variant="success" size="sm">Phase 4 Pipeline</Badge>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Layout-aware document ingestion, Gemini 1536d vector embeddings, and verified evidence grounding.
          </p>
        </div>

        {/* Deal Selector Dropdown */}
        {deals.length > 0 && (
          <div className="flex items-center gap-3">
            <label className="text-xs font-mono text-slate-400 uppercase">Active Deal:</label>
            <select
              value={selectedDealId || ''}
              onChange={(e) => setSelectedDealId(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500 font-medium"
            >
              {deals.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.title} ({d.currency} {d.target_ev ? `${(d.target_ev / 1e6).toFixed(1)}M` : ''})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {!isAuthenticated ? (
        /* Sign-in Callout */
        <Card className="p-8 text-center bg-slate-900/60 border-slate-800 space-y-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center mx-auto">
            <Shield className="w-6 h-6" />
          </div>
          <h2 className="text-lg font-semibold text-white">Sign In to Access Diligence Data Rooms</h2>
          <p className="text-sm text-slate-400 max-w-md mx-auto">
            DealGuard AI enforces strict multi-tenancy and deal-level RBAC. Sign in with institutional credentials to ingest documents and inspect evidence.
          </p>
          <a
            href="/login"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-sm transition-colors"
          >
            Access Login Console
            <ArrowRight className="w-4 h-4" />
          </a>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column: Upload & Ingestion Pipeline (5 Cols) */}
          <div className="lg:col-span-5 space-y-6">
            {/* Upload Box */}
            <Card className="p-6 bg-slate-900/90 border-slate-800 space-y-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Upload className="w-4 h-4 text-emerald-400" />
                  <h2 className="text-sm font-semibold text-white uppercase tracking-wider font-mono">
                    Ingest Diligence Document
                  </h2>
                </div>
                <span className="text-[10px] font-mono text-slate-500">PDF, DOCX, XLSX, TXT</span>
              </div>

              <form onSubmit={handleFileUpload} className="space-y-4">
                {/* File Input */}
                <div className="border-2 border-dashed border-slate-700 hover:border-emerald-500/50 rounded-xl p-6 text-center transition-colors bg-slate-950/40 cursor-pointer">
                  <input
                    type="file"
                    id="doc-file-input"
                    accept=".pdf,.docx,.xlsx,.txt,.csv,.md,.json"
                    onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                    className="hidden"
                  />
                  <label htmlFor="doc-file-input" className="cursor-pointer block">
                    <FileText className="w-8 h-8 text-slate-500 mx-auto mb-2" />
                    <span className="text-xs text-slate-300 font-medium block">
                      {uploadFile ? uploadFile.name : 'Click to select or drag diligence file'}
                    </span>
                    <span className="text-[10px] text-slate-500 block mt-1">
                      {uploadFile ? `${(uploadFile.size / 1024).toFixed(1)} KB` : 'Max size: 50MB'}
                    </span>
                  </label>
                </div>

                {/* Category Selection */}
                <div>
                  <label className="block text-[11px] font-mono uppercase text-slate-400 mb-1">
                    Document Category
                  </label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                  >
                    <option value="FINANCIAL">Financial Statement / QoE Report</option>
                    <option value="LEGAL">Legal / Customer Contract</option>
                    <option value="OPERATIONAL">Technical / Operations Audit</option>
                    <option value="COMMERCIAL">Market & Customer Concentration</option>
                  </select>
                </div>

                <button
                  type="submit"
                  disabled={!uploadFile || isUploading}
                  className="w-full bg-emerald-500 hover:bg-emerald-400 disabled:opacity-40 text-slate-950 font-semibold py-2 px-4 rounded-lg text-xs transition-all flex items-center justify-center gap-2"
                >
                  {isUploading ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      Running 5-Stage Ingestion Pipeline...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-3.5 h-3.5" />
                      Parse, Chunk & Vectorize (1536d)
                    </>
                  )}
                </button>
              </form>

              {uploadMessage && (
                <div
                  className={`p-3 rounded-lg text-xs flex items-start gap-2 ${
                    uploadMessage.includes('error')
                      ? 'bg-rose-500/10 border border-rose-500/30 text-rose-300'
                      : 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-300'
                  }`}
                >
                  {uploadMessage.includes('error') ? (
                    <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  ) : (
                    <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
                  )}
                  <span>{uploadMessage}</span>
                </div>
              )}

              {/* Ingestion Pipeline Stages Status */}
              {activeJob && (
                <div className="pt-4 border-t border-slate-800 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono text-slate-400">Pipeline State:</span>
                    <span className="font-mono font-semibold text-emerald-400">{activeJob.status}</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                    <div
                      className="bg-emerald-500 h-1.5 transition-all duration-300"
                      style={{ width: `${activeJob.progress_pct}%` }}
                    />
                  </div>
                </div>
              )}
            </Card>

            {/* Semantic Evidence Search Box */}
            <Card className="p-6 bg-slate-900/90 border-slate-800 space-y-4">
              <div className="flex items-center gap-2">
                <Search className="w-4 h-4 text-sky-400" />
                <h2 className="text-sm font-semibold text-white uppercase tracking-wider font-mono">
                  Vector Evidence Search
                </h2>
              </div>
              <p className="text-xs text-slate-400">
                Perform cosine similarity retrieval across 1536d document embeddings in this deal room.
              </p>

              <form onSubmit={handleSearch} className="flex gap-2">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="e.g. customer concentration, EBITDA normalization..."
                  className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-sky-500"
                />
                <button
                  type="submit"
                  disabled={isSearching || !searchQuery.trim()}
                  className="px-3 py-2 bg-sky-500 hover:bg-sky-400 disabled:opacity-40 text-slate-950 font-semibold rounded-lg text-xs transition-colors"
                >
                  {isSearching ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : 'Search'}
                </button>
              </form>

              {/* Search Results Preview */}
              {searchResults.length > 0 && (
                <div className="space-y-3 pt-3 border-t border-slate-800">
                  <div className="text-[11px] font-mono text-slate-400">
                    {searchResults.length} Evidence Matches Found:
                  </div>
                  {searchResults.map((res, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-xs space-y-1.5"
                    >
                      <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono">
                        <span className="text-emerald-400 font-medium truncate max-w-[180px]">
                          {res.document_name} (p. {res.page_number})
                        </span>
                        <span className="text-sky-400">Score: {(res.similarity_score * 100).toFixed(1)}%</span>
                      </div>
                      <p className="text-slate-300 italic text-[11px] leading-relaxed">
                        "{res.content.slice(0, 180)}..."
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>

          {/* Right Column: Data Room Document Catalog (7 Cols) */}
          <div className="lg:col-span-7 space-y-6">
            <Card className="p-6 bg-slate-900/90 border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FolderOpen className="w-4 h-4 text-emerald-400" />
                  <h2 className="text-sm font-semibold text-white uppercase tracking-wider font-mono">
                    Diligence Data Room Catalog ({documents.length} Files)
                  </h2>
                </div>
                <button
                  onClick={() => selectedDealId && loadDocuments(selectedDealId)}
                  className="text-xs text-slate-400 hover:text-white flex items-center gap-1 font-mono"
                >
                  <RefreshCw className="w-3 h-3" />
                  Refresh
                </button>
              </div>

              {loadingDocs ? (
                <div className="p-12 text-center text-xs text-slate-500 font-mono">
                  Loading data room catalog...
                </div>
              ) : documents.length === 0 ? (
                <div className="p-12 text-center border border-dashed border-slate-800 rounded-xl space-y-2">
                  <FileText className="w-8 h-8 text-slate-600 mx-auto" />
                  <div className="text-sm text-slate-400">No documents ingested for this deal yet.</div>
                  <div className="text-xs text-slate-600">Upload a PDF, DOCX, or XLSX packet on the left.</div>
                </div>
              ) : (
                <div className="space-y-3">
                  {documents.map((doc) => (
                    <div
                      key={doc.id}
                      className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition-all flex items-center justify-between gap-4"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="w-9 h-9 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-300 shrink-0 font-mono text-xs font-semibold">
                          {doc.file_type}
                        </div>
                        <div className="min-w-0">
                          <div className="text-xs font-semibold text-white truncate max-w-sm">
                            {doc.name}
                          </div>
                          <div className="flex items-center gap-2 text-[10px] text-slate-500 font-mono mt-0.5">
                            <span>{(doc.size_bytes / 1024).toFixed(1)} KB</span>
                            <span>•</span>
                            <span className="text-slate-400">{doc.doc_category || 'DILIGENCE'}</span>
                            <span>•</span>
                            <span className="truncate max-w-[120px]">{doc.sha256_hash.slice(0, 12)}...</span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-3 shrink-0">
                        <Badge
                          variant={
                            doc.status === 'INDEXED'
                              ? 'success'
                              : doc.status === 'FAILED'
                              ? 'danger'
                              : 'warning'
                          }
                          size="sm"
                        >
                          {doc.status}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>

            {/* Architecture Highlights & Vector Metrics */}
            <Card className="p-6 bg-slate-900/60 border-slate-800 space-y-4">
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4 text-emerald-400" />
                <h3 className="text-xs font-semibold text-white uppercase font-mono tracking-wider">
                  Phase 4 Storage & Vector Invariant
                </h3>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800/80">
                  <div className="text-base font-bold text-white font-mono">1536</div>
                  <div className="text-[10px] text-slate-400 font-mono mt-0.5">Embedding Dim</div>
                </div>
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800/80">
                  <div className="text-base font-bold text-emerald-400 font-mono">pgvector</div>
                  <div className="text-[10px] text-slate-400 font-mono mt-0.5">Vector Store</div>
                </div>
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800/80">
                  <div className="text-base font-bold text-sky-400 font-mono">Layout-Aware</div>
                  <div className="text-[10px] text-slate-400 font-mono mt-0.5">Chunking</div>
                </div>
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800/80">
                  <div className="text-base font-bold text-purple-400 font-mono">100%</div>
                  <div className="text-[10px] text-slate-400 font-mono mt-0.5">Tenant Scoped</div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
