import { useCallback, useEffect, useMemo, useState } from "react";
import AppShell from "./components/AppShell";
import NewTicketDialog, { type TicketDraft } from "./components/NewTicketDialog";
import { EvidenceDialog, Notice } from "./components/ui";
import ApprovalPage from "./pages/ApprovalPage";
import AnalysisReportPage from "./pages/AnalysisReportPage";
import DashboardPage from "./pages/DashboardPage";
import KnowledgePage from "./pages/KnowledgePage";
import TicketDetailPage from "./pages/TicketDetailPage";
import TicketListPage from "./pages/TicketListPage";
import { api, redactPreview } from "./services/api";
import { benchmarkRows } from "./services/mockData";
import type { AnalysisEvidence, AnalysisReport, ApprovalItem, AuthUser, KnowledgeDocument, KnowledgeDocumentDetail, PageId, RetrievalResult, Ticket, TicketStatus } from "./types";
import { ChangePasswordPage, LoginPage, UserManagementPage } from "./pages/AuthPages";

export default function App() {
  const [page, setPage] = useState<PageId>("tickets");
  const [authUser, setAuthUser] = useState<AuthUser | null>(null);
  const [authChecking, setAuthChecking] = useState(true);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [documentDetail, setDocumentDetail] = useState<KnowledgeDocumentDetail | null>(null);
  const [evidence, setEvidence] = useState<AnalysisEvidence | null>(null);
  const [retrievalResults, setRetrievalResults] = useState<RetrievalResult[]>([]);
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [reportError, setReportError] = useState<string | null>(null);
  const [apiOnline, setApiOnline] = useState(false);
  const [booting, setBooting] = useState(true);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [retrievalLoading, setRetrievalLoading] = useState(false);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [createBusy, setCreateBusy] = useState(false);
  const [toast, setToast] = useState("");
  const [approvals, setApprovals] = useState<ApprovalItem[]>([]);

  const notify = useCallback((message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(""), 3600);
  }, []);

  const loadTickets = useCallback(async () => {
    setBooting(true);
    try {
      const response = await api.listTickets();
      setTickets(response.items);
      setApiOnline(true);
    } catch {
      setTickets([]);
      setApiOnline(false);
    } finally { setBooting(false); }
  }, []);

  const loadDocuments = useCallback(async () => {
    setDocumentsLoading(true);
    try {
      const response = await api.listDocuments();
      setDocuments(response.items);
      setApiOnline(true);
    } catch {
      setDocuments([]);
    } finally { setDocumentsLoading(false); }
  }, []);

  useEffect(() => {
    void api.me().then(setAuthUser).catch(() => setAuthUser(null)).finally(() => setAuthChecking(false));
  }, []);
  useEffect(() => {
    if (!authUser || authUser.must_change_password) return;
    void loadTickets();
    if (authUser.role !== "employee") void loadDocuments();
  }, [authUser, loadTickets, loadDocuments]);
  useEffect(() => {
    if (!authUser || authUser.must_change_password || authUser.role === "employee") return;
    void api.listApprovals().then((rows) => setApprovals(rows.map((item) => ({
      id: item.approval_id,
      ticketId: item.ticket_id,
      action: item.action,
      risk: /restart|delete|drop|rollback|production|increase/i.test(item.action) ? "high" : /change|update|modify|scale/i.test(item.action) ? "medium" : "low",
      status: item.status,
      createdAt: item.decided_at ?? item.created_at,
      note: item.decision_note ?? undefined,
    })))).catch(() => setApprovals([]));
  }, [authUser]);

  const ticketCounts = useMemo(() => ({ pending: approvals.filter((item) => item.status === "pending").length }), [approvals]);

  const updateStatus = async (ticket: Ticket, status: TicketStatus) => {
    try {
      const updated = await api.updateStatus(ticket.ticket_id, status);
      setTickets((current) => current.map((item) => item.ticket_id === updated.ticket_id ? updated : item));
      setSelectedTicket(updated);
      notify(`Ticket ${updated.ticket_id} updated.`);
    } catch (error) { notify(error instanceof Error ? error.message : "Status update failed."); }
  };

  const createTicket = async (draft: TicketDraft) => {
    setCreateBusy(true);
    try {
      const created = await api.createTicket({ ...draft, assigned_team: draft.assigned_team || null });
      setTickets((current) => [created, ...current]); setSelectedTicket(created); setRetrievalResults([]); setReport(null); setPage("ticket-detail"); setCreateOpen(false); setApiOnline(true); notify(`Created ${created.ticket_id}.`);
    } catch (error) { notify(error instanceof Error ? error.message : "Could not create ticket."); }
    finally { setCreateBusy(false); }
  };

  const retrieve = async (method: string) => {
    if (!selectedTicket) return;
    setRetrievalLoading(true);
    try {
      const result = await api.retrieve({ ticket_id: selectedTicket.ticket_id, method, rewrite: method === "hybrid_rerank", service: selectedTicket.service, category: selectedTicket.category, source_types: ["runbook", "historical_ticket"], access_scope: "it_internal", top_k: 5, candidate_k: 50, rerank_k: 20 });
      setRetrievalResults(result.results); setApiOnline(true);
      if (!result.results.length) notify("Retrieval returned no evidence for these filters.");
    } catch (error) { notify(error instanceof Error ? error.message : "Evidence retrieval failed."); }
    finally { setRetrievalLoading(false); }
  };

  const analyze = async (windowStart: string, windowEnd: string, retrievalMethod: string) => {
    if (!selectedTicket) return;
    setPage("report"); setReport(null); setReportError(null); setAnalysisLoading(true);
    try {
      const result = await api.analyze({ ticket_id: selectedTicket.ticket_id, window_start: windowStart, window_end: windowEnd, retrieval_method: retrievalMethod, top_k: 5 });
      setReport(result); setApiOnline(true);
    } catch (error) { setReportError(error instanceof Error ? error.message : "Analysis failed."); }
    finally { setAnalysisLoading(false); }
  };

  const openTicket = (ticket: Ticket) => { setSelectedTicket(ticket); setRetrievalResults([]); setReport(null); setPage("ticket-detail"); };

  const openEvidence = (id: string) => {
    const fromReport = report?.evidence.find((item) => item.evidence_id === id);
    if (fromReport) { setEvidence(fromReport); return; }
    const fromRetrieval = retrievalResults.find((item) => item.chunk_id === id);
    if (fromRetrieval) { setEvidence({ evidence_id: id, source_type: fromRetrieval.source_type as AnalysisEvidence["source_type"], content: fromRetrieval.content, service: fromRetrieval.service ?? "unknown" }); return; }
    notify(`Evidence ${id} is not in the current report/retrieval result.`);
  };

  const requestApproval = async (action: string, ticketId: string) => {
    try {
      const created = await api.createApproval({ ticket_id: ticketId, action, rationale: "Requested from the reviewed RCA report." });
      const item: ApprovalItem = { id: created.approval_id, ticketId: created.ticket_id, action: created.action, risk: /restart|delete|drop|rollback|production|increase/i.test(action) ? "high" : /change|update|modify|scale/i.test(action) ? "medium" : "low", status: "pending", createdAt: created.created_at };
      setApprovals((current) => [item, ...current]); setPage("approvals"); notify("Approval request saved for review. No system action was executed.");
    } catch (error) { notify(error instanceof Error ? error.message : "Could not save approval request."); }
  };

  const decision = async (id: string, status: "approved" | "rejected", note: string) => {
    try {
      const saved = await api.decideApproval(id, status, note || `Reviewed and ${status}.`);
      setApprovals((current) => current.map((item) => item.id === id ? { ...item, status: saved.status, note: saved.decision_note ?? undefined, createdAt: saved.decided_at ?? item.createdAt } : item));
      notify(`Decision saved to audit history. No system action was executed.`);
    } catch (error) { notify(error instanceof Error ? error.message : "Could not save approval decision."); }
  };

  const upload = async (payload: { title: string; source: string; source_type: string; content: string; service: string; category: string; document_id: string }) => {
    await api.uploadDocument({ ...payload, content: redactPreview(payload.content), version: "v1", access_scope: "it_internal" });
    await loadDocuments(); setApiOnline(true);
  };

  const openDocument = async (document: KnowledgeDocument) => {
    try { setDocumentDetail(await api.getDocument(document.document_id)); }
    catch (error) { notify(error instanceof Error ? error.message : "Could not load document details."); }
  };

  const navigate = (target: PageId) => {
    if (authUser?.role === "employee" && target !== "tickets") return;
    setPage(target);
    if (target === "knowledge") void loadDocuments();
  };

  const login = async (username: string, password: string) => {
    const result = await api.login(username, password);
    setAuthUser(result.user);
    setPage("tickets");
  };

  const logout = async () => {
    try { await api.logout(); } finally { setAuthUser(null); setTickets([]); setDocuments([]); setSelectedTicket(null); setPage("tickets"); }
  };

  const publishResponse = async (text: string, ticketId: string) => {
    try {
      const updated = await api.publishResponse(ticketId, text);
      setTickets((current) => current.map((item) => item.ticket_id === updated.ticket_id ? updated : item));
      setSelectedTicket(updated);
      notify("Reviewed response sent to the ticket owner.");
    } catch (error) { notify(error instanceof Error ? error.message : "Could not publish technician response."); throw error; }
  };

  if (authChecking) return <main className="auth-screen"><div className="auth-loading">Checking your session…</div></main>;
  if (!authUser) return <LoginPage onLogin={login} />;
  if (authUser.must_change_password) return <ChangePasswordPage user={authUser} forced onChanged={setAuthUser} />;

  return <AppShell page={page} user={authUser} onLogout={() => void logout()} onNavigate={navigate} onNewTicket={() => setCreateOpen(true)} apiOnline={apiOnline} pendingCount={ticketCounts.pending}>
    {authUser.role !== "employee" && <div className="workflow-strip"><span className="workflow-label">INCIDENT WORKFLOW</span><button onClick={() => setCreateOpen(true)} className={selectedTicket ? "done" : "current"}>1 <span>Create ticket</span></button><i /><button disabled={!selectedTicket} onClick={() => setPage("ticket-detail")} className={page === "ticket-detail" ? "current" : selectedTicket ? "done" : ""}>2 <span>Ticket & evidence</span></button><i /><button disabled={!selectedTicket} onClick={() => setPage(report ? "report" : "ticket-detail")} className={page === "report" ? "current" : report ? "done" : ""}>3 <span>RCA report</span></button><i /><button onClick={() => setPage("approvals")} className={page === "approvals" ? "current" : approvals.length ? "done" : ""}>4 <span>Approval review</span></button><i /><button onClick={() => setPage("dashboard")} className={page === "dashboard" ? "current" : ""}>5 <span>Dashboard</span></button></div>}
    {page === "tickets" && <TicketListPage tickets={tickets} demoMode={!apiOnline} canManage={authUser.role !== "employee"} onSelect={openTicket} onCreate={() => setCreateOpen(true)} onStatus={(ticket, status) => void updateStatus(ticket, status)} />}
    {page === "ticket-detail" && (selectedTicket ? <TicketDetailPage ticket={tickets.find((item) => item.ticket_id === selectedTicket.ticket_id) ?? selectedTicket} results={retrievalResults} retrievalLoading={retrievalLoading} onBack={() => setPage("tickets")} onRetrieve={(method) => void retrieve(method)} onAnalyze={(start, end, method) => void analyze(start, end, method)} onEvidence={openEvidence} onStatus={(ticket, status) => void updateStatus(ticket, status)} canAnalyze={authUser.role !== "employee"} /> : <div className="page-wrap"><Notice>Select a ticket first.</Notice></div>)}
    {page === "report" && authUser.role !== "employee" && <AnalysisReportPage report={report} loading={analysisLoading} error={reportError} onEvidence={openEvidence} onRequestApproval={requestApproval} onBack={() => setPage("ticket-detail")} onPublishResponse={publishResponse} canPublish={authUser.role === "technician"} />}
    {page === "knowledge" && authUser.role !== "employee" && <KnowledgePage documents={documents} loading={documentsLoading} onUpload={upload} onDocument={(document) => void openDocument(document)} />}
    {page === "approvals" && authUser.role !== "employee" && <ApprovalPage items={approvals} onDecision={decision} />}
    {page === "dashboard" && authUser.role !== "employee" && <DashboardPage tickets={tickets} benchmarks={benchmarkRows} />}
    {page === "users" && authUser.role !== "employee" && <UserManagementPage currentUser={authUser} />}
    {booting && <div className="toast" role="status">Connecting to backend…</div>}
    {toast && <div className="toast" role="status">{toast}</div>}
    <NewTicketDialog open={createOpen} busy={createBusy} onClose={() => setCreateOpen(false)} onSubmit={(draft) => void createTicket(draft)} />
    <EvidenceDialog evidence={evidence} onClose={() => setEvidence(null)} />
    {documentDetail && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setDocumentDetail(null); }}><section className="modal" role="dialog" aria-modal="true"><div className="modal-head"><div><h2>{documentDetail.title}</h2><div className="panel-subtitle mono">{documentDetail.document_id} · {documentDetail.source_type} · {documentDetail.access_scope}</div></div><button className="btn btn-small" onClick={() => setDocumentDetail(null)}>Close</button></div><div className="modal-body"><div className="meta-line">Source · {documentDetail.source} · {documentDetail.chunks.length} chunks · vector points {documentDetail.chunks.filter((chunk) => chunk.qdrant_point_id).length}/{documentDetail.chunks.length}</div><div className="stack" style={{ marginTop: 14 }}>{documentDetail.chunks.map((chunk) => <div key={chunk.chunk_id} style={{ padding: 11, border: "1px solid #e7ebf0", borderRadius: 6 }}><div className="ticket-id mono">{chunk.chunk_id} · chunk {chunk.chunk_index} · {chunk.token_count} tokens</div><div className="evidence-preview" style={{ marginTop: 7, whiteSpace: "pre-wrap" }}>{chunk.content}</div></div>)}</div></div></section></div>}
  </AppShell>;
}
