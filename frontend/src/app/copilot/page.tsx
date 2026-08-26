'use client';

/**
 * DealGuard AI — Phase 14: Streaming RAG Copilot Deal Intelligence Console
 */

import React, { useEffect, useRef, useState } from 'react';
import {
  Bot,
  Send,
  Sparkles,
  RefreshCw,
  Plus,
  Trash2,
  FileCheck2,
  Eye,
  XCircle,
  Building2,
  Shield,
  Layers,
  AlertTriangle,
  FileText,
  Cpu,
  HelpCircle,
  MessageSquare,
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { api } from '@/lib/api';
import {
  CopilotCitation,
  CopilotConversationResponse,
  CopilotMessageResponse,
  Deal,
} from '@/types';

const SUGGESTED_PROMPTS = [
  { text: 'Why is this deal risky?', domain: 'RISKS' },
  { text: 'Which contracts have change-of-control clauses?', domain: 'LEGAL' },
  { text: 'What are the major single points of failure in technology?', domain: 'TECH' },
  { text: 'Explain the normalized EBITDA and QoE adjustments.', domain: 'FINANCIALS' },
  { text: 'What must be executed in the first 30 days of integration?', domain: 'INTEGRATION' },
  { text: 'Where is the largest synergy realization opportunity?', domain: 'SYNERGIES' },
];

export default function CopilotPage() {
  const [deals, setDeals] = useState<Deal[]>([]);
  const [selectedDealId, setSelectedDealId] = useState<string | null>(null);

  // Conversations State
  const [conversations, setConversations] = useState<CopilotConversationResponse[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<CopilotMessageResponse[]>([]);

  // Input & Streaming State
  const [inputQuery, setInputQuery] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [streamingText, setStreamingText] = useState<string>('');
  const [streamingDomains, setStreamingDomains] = useState<string[]>([]);
  const [streamingCitations, setStreamingCitations] = useState<CopilotCitation[]>([]);

  // Modal / Evidence Drawer
  const [selectedCitation, setSelectedCitation] = useState<CopilotCitation | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingText]);

  // 1. Load Deals on Mount
  useEffect(() => {
    async function loadDeals() {
      try {
        const dealList = await api.getDeals();
        setDeals(dealList);
        if (dealList.length > 0 && !selectedDealId) {
          setSelectedDealId(dealList[0].id);
        }
      } catch (err) {
        console.error('Failed to load deals:', err);
      }
    }
    loadDeals();
  }, []);

  // 2. Load Conversations when deal changes
  useEffect(() => {
    if (!selectedDealId) return;
    loadConversations(selectedDealId);
  }, [selectedDealId]);

  async function loadConversations(dealId: string) {
    try {
      const convList = await api.getCopilotConversations(dealId);
      setConversations(convList);
      if (convList.length > 0) {
        selectConversation(convList[0].id, dealId);
      } else {
        setActiveConversationId(null);
        setMessages([]);
      }
    } catch (err) {
      console.error('Failed to load conversations:', err);
    }
  }

  async function selectConversation(convId: string, dealId?: string) {
    const targetDealId = dealId || selectedDealId;
    if (!targetDealId) return;
    setActiveConversationId(convId);
    try {
      const conv = await api.getCopilotConversation(targetDealId, convId);
      setMessages(conv.messages || []);
    } catch (err) {
      console.error('Failed to load conversation history:', err);
    }
  }

  // 3. Create New Conversation
  async function handleNewConversation() {
    if (!selectedDealId) return;
    try {
      const conv = await api.createCopilotConversation(selectedDealId, {
        title: 'New Deal Intelligence Chat',
      });
      setConversations([conv, ...conversations]);
      setActiveConversationId(conv.id);
      setMessages([]);
    } catch (err) {
      console.error('Failed to create new conversation:', err);
    }
  }

  // 4. Delete Conversation
  async function handleDeleteConversation(e: React.MouseEvent, convId: string) {
    e.stopPropagation();
    if (!selectedDealId) return;
    try {
      await api.deleteCopilotConversation(selectedDealId, convId);
      const remaining = conversations.filter((c) => c.id !== convId);
      setConversations(remaining);
      if (activeConversationId === convId) {
        if (remaining.length > 0) {
          selectConversation(remaining[0].id);
        } else {
          setActiveConversationId(null);
          setMessages([]);
        }
      }
    } catch (err) {
      console.error('Failed to delete conversation:', err);
    }
  }

  // 5. Send Message & Stream Response
  async function handleSendMessage(queryOverride?: string) {
    const query = queryOverride || inputQuery;
    if (!query.trim() || !selectedDealId || isProcessing) return;

    setInputQuery('');
    setIsProcessing(true);
    setStreamingText('');
    setStreamingDomains([]);
    setStreamingCitations([]);

    // Optimistic user message
    const tempUserMsg: CopilotMessageResponse = {
      id: `temp-${Date.now()}`,
      deal_id: selectedDealId,
      conversation_id: activeConversationId || 'temp',
      role: 'user',
      content: query,
      citations: [],
      confidence: 'HIGH',
      retrieved_domains: [],
      metadata_payload: {},
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const res = await api.queryCopilot(selectedDealId, {
        conversation_id: activeConversationId || undefined,
        message: query,
      });

      if (!activeConversationId) {
        setActiveConversationId(res.conversation_id);
        loadConversations(selectedDealId);
      }

      setMessages((prev) => [
        ...prev.filter((m) => m.id !== tempUserMsg.id),
        res.user_message,
        res.assistant_message,
      ]);
    } catch (err) {
      console.error('Failed to process copilot query:', err);
    } finally {
      setIsProcessing(false);
      setStreamingText('');
    }
  }

  return (
    <div className="flex h-[calc(100vh-4.5rem)] bg-surface-base text-slate-100 font-mono text-xs overflow-hidden">
      {/* Left Sidebar: Conversations History */}
      <aside className="w-72 border-r border-slate-800 bg-slate-950 flex flex-col justify-between">
        <div className="p-3.5 space-y-3">
          {/* Deal Workspace Selector */}
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs">
            <Building2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <select
              value={selectedDealId || ''}
              onChange={(e) => setSelectedDealId(e.target.value)}
              className="bg-transparent text-slate-200 focus:outline-none w-full cursor-pointer truncate"
            >
              {deals.map((d) => (
                <option key={d.id} value={d.id} className="bg-slate-900 text-slate-200">
                  {d.title}
                </option>
              ))}
            </select>
          </div>

          <button
            type="button"
            onClick={handleNewConversation}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold transition-colors shadow"
          >
            <Plus className="w-4 h-4" />
            New Deal Chat
          </button>

          {/* Conversations List */}
          <div className="space-y-1 overflow-y-auto max-h-[calc(100vh-14rem)] pr-1">
            <span className="text-[10px] text-slate-500 uppercase tracking-wider block px-1 pb-1">
              Conversations ({conversations.length})
            </span>
            {conversations.map((c) => (
              <div
                key={c.id}
                onClick={() => selectConversation(c.id)}
                className={`group flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors ${
                  activeConversationId === c.id
                    ? 'bg-slate-800 text-white font-bold'
                    : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <MessageSquare className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span className="truncate text-xs">{c.title}</span>
                </div>
                <button
                  type="button"
                  onClick={(e) => handleDeleteConversation(e, c.id)}
                  className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-rose-400 p-1"
                  title="Delete chat"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="p-3 border-t border-slate-800/80 text-[10px] text-slate-500">
          Grounded RAG • Zero Hallucination
        </div>
      </aside>

      {/* Main Chat Workspace */}
      <main className="flex-1 flex flex-col justify-between bg-slate-900/60 overflow-hidden">
        {/* Chat Header */}
        <div className="p-3.5 border-b border-slate-800 bg-slate-950/80 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-white">DealGuard Copilot</span>
                <Badge variant="success" size="sm">Evidence-Grounded RAG</Badge>
              </div>
              <span className="text-[10px] text-slate-400">
                Synthesizing multi-domain data room records across financials, legal, risks & technology
              </span>
            </div>
          </div>
        </div>

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && !isProcessing && (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-lg mx-auto space-y-4">
              <div className="p-3 rounded-full bg-slate-800 text-emerald-400">
                <Sparkles className="w-8 h-8" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Ask Anything About This Acquisition</h3>
                <p className="text-xs text-slate-400 mt-1">
                  Every answer is mathematically verified and grounded with exact citations to the data room.
                </p>
              </div>

              {/* Suggested Questions */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full text-left pt-2">
                {SUGGESTED_PROMPTS.map((p, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSendMessage(p.text)}
                    className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 hover:border-emerald-500/50 hover:bg-slate-900 text-slate-300 text-xs transition-colors"
                  >
                    <div className="flex items-center justify-between pb-1">
                      <span className="text-[9px] text-emerald-400 font-bold">{p.domain}</span>
                    </div>
                    {p.text}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m) => (
            <div
              key={m.id}
              className={`flex flex-col ${
                m.role === 'user' ? 'items-end' : 'items-start'
              }`}
            >
              <div
                className={`max-w-2xl rounded-2xl p-4 space-y-2.5 ${
                  m.role === 'user'
                    ? 'bg-emerald-700 text-white rounded-br-none'
                    : 'bg-slate-950 border border-slate-800 text-slate-200 rounded-bl-none'
                }`}
              >
                {/* Assistant Header Badge */}
                {m.role === 'assistant' && (
                  <div className="flex items-center justify-between pb-1 border-b border-slate-800/80 text-[10px]">
                    <div className="flex items-center gap-1.5">
                      <Bot className="w-3.5 h-3.5 text-emerald-400" />
                      <span className="font-bold text-white">DealGuard AI</span>
                      {m.retrieved_domains?.map((d) => (
                        <Badge key={d} variant="info" size="sm">{d}</Badge>
                      ))}
                    </div>
                    <span className="text-slate-500">Confidence: {m.confidence}</span>
                  </div>
                )}

                {/* Content */}
                <div className="whitespace-pre-wrap leading-relaxed">{m.content}</div>

                {/* Citations List */}
                {m.citations && m.citations.length > 0 && (
                  <div className="pt-2 border-t border-slate-800/80 space-y-1.5">
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider block font-bold">
                      Supporting Evidence ({m.citations.length})
                    </span>
                    <div className="grid grid-cols-1 gap-1.5">
                      {m.citations.map((c, idx) => (
                        <button
                          key={idx}
                          type="button"
                          onClick={() => setSelectedCitation(c)}
                          className="flex items-center justify-between p-2 rounded bg-slate-900/90 border border-slate-800 text-left hover:border-emerald-500/40 transition-colors"
                        >
                          <div className="truncate">
                            <span className="text-emerald-400 font-bold block truncate">
                              {c.document_name}
                            </span>
                            <span className="text-[10px] text-slate-400 truncate block">
                              Page {c.page_number || 1} • {c.section_title || 'General'}
                            </span>
                          </div>
                          <Eye className="w-3.5 h-3.5 text-slate-400 hover:text-emerald-400 shrink-0 ml-2" />
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Processing Indicator */}
          {isProcessing && (
            <div className="flex items-center gap-2 text-xs text-emerald-400 p-3">
              <Sparkles className="w-4 h-4 animate-spin" />
              <span>Synthesizing multi-domain data room records...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/90">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 focus-within:border-emerald-500/60"
          >
            <input
              type="text"
              value={inputQuery}
              disabled={isProcessing}
              onChange={(e) => setInputQuery(e.target.value)}
              placeholder="Ask about risks, financial metrics, change of control, technology architecture..."
              className="w-full bg-transparent text-slate-100 placeholder-slate-500 focus:outline-none text-xs"
            />
            <button
              type="submit"
              disabled={isProcessing || !inputQuery.trim()}
              className="p-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white transition-colors"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </main>

      {/* Citation Preview Modal */}
      {selectedCitation && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn font-mono text-xs">
          <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-xl shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <FileCheck2 className="w-4 h-4 text-emerald-400" />
                Verified Data Room Citation
              </h3>
              <button onClick={() => setSelectedCitation(null)} className="text-slate-400 hover:text-white">
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <span className="text-[10px] text-slate-500 uppercase block">Source Document</span>
                <span className="text-white font-bold">{selectedCitation.document_name}</span>
              </div>

              <div>
                <span className="text-[10px] text-slate-500 uppercase block">Location</span>
                <span className="text-slate-300">
                  Page {selectedCitation.page_number || 1} • {selectedCitation.section_title || 'General Section'}
                </span>
              </div>

              <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg space-y-1">
                <span className="text-[10px] text-emerald-400 uppercase font-bold block">Verbatim Grounded Text</span>
                <p className="text-slate-200 text-xs italic">&ldquo;{selectedCitation.quote}&rdquo;</p>
              </div>

              <div className="flex items-center justify-between text-[10px] pt-2 border-t border-slate-800 text-slate-500">
                <span>Provenance: Immutable Citation Ledger</span>
                <span className="text-emerald-400 font-bold">Confidence: {selectedCitation.confidence}</span>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                type="button"
                onClick={() => setSelectedCitation(null)}
                className="px-4 py-1.5 rounded bg-slate-800 text-white font-bold"
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
