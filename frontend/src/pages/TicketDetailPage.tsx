import { ArrowLeft, CheckCircle2, FileSearch, Play, RefreshCw, Send } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import type { RetrievalResult, Ticket, TicketComment, TicketStatus } from "../types";
import { EvidenceButton, Notice, PageHeading, Panel, PriorityLabel, StatusLabel } from "../components/ui";
import { api } from "../services/api";

function isoLocal(date: Date) {
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 16);
}

export default function TicketDetailPage({ ticket, results, retrievalLoading, onBack, onRetrieve, onAnalyze, onEvidence, onStatus, canAnalyze }: {
  ticket: Ticket; results: RetrievalResult[]; retrievalLoading: boolean; onBack: () => void; onRetrieve: (method: string) => void; onAnalyze: (start: string, end: string, method: string) => void; onEvidence: (id: string) => void; onStatus: (ticket: Ticket, status: TicketStatus) => void; canAnalyze: boolean;
}) {
  const end = new Date();
  const [windowEnd, setWindowEnd] = useState(isoLocal(end));
  const [windowStart, setWindowStart] = useState(isoLocal(new Date(end.getTime() - 15 * 60 * 1000)));
  const [method, setMethod] = useState("hybrid_rerank");
  const [comments, setComments] = useState<TicketComment[]>([]);
  const [commentText, setCommentText] = useState("");
  const [commentBusy, setCommentBusy] = useState(false);
  const [commentError, setCommentError] = useState("");

  const loadComments = useCallback(async () => {
    try {
      const rows = await api.listComments(ticket.ticket_id);
      setComments(rows);
    } catch {
      setComments([]);
    }
  }, [ticket.ticket_id]);

  useEffect(() => {
    void loadComments();
  }, [loadComments]);

  const handleAddComment = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!commentText.trim()) return;
    setCommentBusy(true);
    setCommentError("");
    try {
      const commentType = canAnalyze ? "technician_note" : "supplementary_info";
      await api.addComment(ticket.ticket_id, commentText, commentType);
      setCommentText("");
      await loadComments();
      if (!canAnalyze && ticket.status === "waiting_for_employee") {
        onStatus(ticket, "in_progress");
      }
    } catch (e) {
      setCommentError(e instanceof Error ? e.message : "Could not post note");
    } finally {
      setCommentBusy(false);
    }
  };

  return <div className="page-wrap">
    <PageHeading
      title="Ticket detail"
      description={`${ticket.ticket_id} · ${ticket.service}`}
      actions={
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <button className="btn" onClick={onBack}><ArrowLeft size={14} />Back to tickets</button>
          {!canAnalyze && ticket.status === "resolved" && (
            <button className="btn btn-success" onClick={() => onStatus(ticket, "closed")}>
              <CheckCircle2 size={14} />Confirm & close ticket
            </button>
          )}
          {canAnalyze && (
            <button className="btn btn-primary" onClick={() => onAnalyze(new Date(windowStart).toISOString(), new Date(windowEnd).toISOString(), method)}>
              <Play size={14} />Analyze incident
            </button>
          )}
        </div>
      }
    />

    {!canAnalyze && ticket.status === "waiting_for_employee" && (
      <div style={{ marginBottom: 14 }}>
        <Notice tone="warn">
          <strong>Action needed:</strong> The IT technician has asked for additional information to analyze this incident. Please check the discussion below and supplement the details.
        </Notice>
      </div>
    )}

    {!canAnalyze && ticket.status === "resolved" && (
      <div style={{ marginBottom: 14 }}>
        <Notice tone="success">
          <strong>Resolution ready:</strong> A technician has reviewed the root cause and provided a resolution response below. If your issue is resolved, please click <strong>Confirm & close ticket</strong>.
        </Notice>
      </div>
    )}

    <div className="detail-grid">
      <div className="stack">
        <Panel title="Incident summary" subtitle={<span className="meta-line"><span>{ticket.ticket_id}</span><span>·</span><span>{ticket.service}</span><span>·</span><span>{ticket.category.replaceAll("_", " ")}</span></span>}>
          <div className="panel-body">
            <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
              <h2 className="detail-title">{ticket.title}</h2>
              <PriorityLabel priority={ticket.priority} />
              <StatusLabel status={ticket.status} />
            </div>
            <p className="detail-description">{ticket.description}</p>
            <div className="detail-kv">
              <div><div className="kv-label">Assigned team</div><div className="kv-value">{ticket.assigned_team || "Unassigned"}</div></div>
              <div><div className="kv-label">Reporter</div><div className="kv-value">{ticket.requester_email_redacted || "Redacted / unavailable"}</div></div>
              <div><div className="kv-label">Created</div><div className="kv-value mono">{new Date(ticket.created_at).toLocaleString()}</div></div>
              <div><div className="kv-label">Source</div><div className="kv-value">{ticket.source || "Not specified"}</div></div>
            </div>
            {canAnalyze && (
              <div style={{ marginTop: 16, display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                <span className="kv-label" style={{ marginBottom: 0 }}>Update status:</span>
                <select
                  aria-label={`Update status ${ticket.ticket_id}`}
                  className="select"
                  style={{ width: 190 }}
                  value={ticket.status}
                  onChange={(event) => onStatus(ticket, event.target.value as TicketStatus)}
                >
                  <option value="new">New</option>
                  <option value="assigned">Assigned</option>
                  <option value="in_progress">Investigating</option>
                  <option value="waiting_for_employee">Waiting for Employee</option>
                  <option value="resolved">Resolved</option>
                  <option value="closed">Closed</option>
                </select>
              </div>
            )}
          </div>
        </Panel>

        {!canAnalyze && (
          <Panel title="Technician response" subtitle={ticket.response_sent_at ? `Reviewed and sent ${new Date(ticket.response_sent_at).toLocaleString()}` : "The technician has not sent a response yet."}>
            <div className="panel-body">
              {ticket.technician_response ? (
                <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.6, color: "#1e293b" }}>{ticket.technician_response}</div>
              ) : (
                <div className="empty-state">Your report is with the IT team. The RCA will appear here after technician review.</div>
              )}
            </div>
          </Panel>
        )}

        <Panel
          title="Incident Discussion & Information"
          subtitle={`${comments.length} updates / notes on this incident`}
        >
          <div className="panel-body">
            {commentError && <Notice tone="error">{commentError}</Notice>}
            <div className="comment-list">
              {comments.map((c) => (
                <div key={c.id} className={`comment-item ${c.user_role}`}>
                  <div className="comment-header">
                    <span className="comment-author">
                      {c.user_name}
                      <span className={`comment-badge ${c.user_role}`}>{c.user_role}</span>
                      {c.comment_type === "supplementary_info" && <span style={{ fontSize: 9, color: "#0369a1" }}>· supplementary info</span>}
                    </span>
                    <span className="comment-time mono">{new Date(c.created_at).toLocaleString()}</span>
                  </div>
                  <div className="comment-body">{c.content}</div>
                </div>
              ))}
              {!comments.length && (
                <div className="empty-state">No comments or supplementary information added yet.</div>
              )}
            </div>

            <form onSubmit={handleAddComment} style={{ marginTop: 14, display: "grid", gap: 8 }}>
              <textarea
                className="input"
                rows={3}
                placeholder={canAnalyze ? "Add a technical note or ask the user for details..." : "Add supplementary information, error logs, or reply to the technician..."}
                value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
                required
              />
              <div style={{ display: "flex", justifyContent: "flex-end" }}>
                <button className="btn btn-primary btn-small" type="submit" disabled={commentBusy || !commentText.trim()}>
                  <Send size={13} />
                  {commentBusy ? "Posting…" : canAnalyze ? "Add Note" : "Send Information"}
                </button>
              </div>
            </form>
          </div>
        </Panel>

        {canAnalyze && (
          <Panel title="Retrieved evidence" subtitle="Hybrid retrieval · source citations open the evidence inspector" action={<button className="btn btn-small" onClick={() => onRetrieve(method)} disabled={retrievalLoading}><RefreshCw size={13} />{retrievalLoading ? "Searching…" : "Retrieve evidence"}</button>}>
            <div className="panel-body">{!results.length ? <div className="empty-state">Run retrieval to find runbooks and historical ticket chunks for this service.</div> : <div className="evidence-list">{results.map((item) => <div className="evidence-row" key={item.chunk_id}><div><EvidenceButton id={item.chunk_id} onClick={onEvidence} /><div className="evidence-source">#{item.rank} · {item.source_type}</div></div><div><div className="evidence-preview">{item.content.slice(0, 230)}{item.content.length > 230 ? "…" : ""}</div><div className="evidence-source">{item.document_id} · {item.service || "service not set"} · {item.access_scope}</div></div><div className="score">{item.score.toFixed(3)}</div></div>)}</div>}</div>
          </Panel>
        )}
      </div>

      <div className="stack">
        {canAnalyze && (
          <Panel title="Analysis window" subtitle="Logs and metrics are filtered by service and time window">
            <div className="panel-body" style={{ display: "grid", gap: 12 }}>
              <div className="field"><label htmlFor="window-start">Start</label><input id="window-start" className="input mono" type="datetime-local" value={windowStart} onChange={(event) => setWindowStart(event.target.value)} /></div>
              <div className="field"><label htmlFor="window-end">End</label><input id="window-end" className="input mono" type="datetime-local" value={windowEnd} onChange={(event) => setWindowEnd(event.target.value)} /></div>
              <div className="field"><label htmlFor="retrieval-method">Retrieval method</label><select id="retrieval-method" className="select" value={method} onChange={(event) => setMethod(event.target.value)}><option value="bm25">BM25</option><option value="hybrid">Hybrid RRF</option><option value="hybrid_rerank">Hybrid + reranker</option></select></div>
              <button className="btn btn-primary" onClick={() => onAnalyze(new Date(windowStart).toISOString(), new Date(windowEnd).toISOString(), method)}><FileSearch size={14} />Generate RCA report</button>
            </div>
          </Panel>
        )}
        {canAnalyze && (
          <Panel title="Workflow" subtitle="Human review remains required">
            <div className="panel-body">
              <div className="meta-line" style={{ lineHeight: 1.8 }}>
                Ticket status changes are persisted through the ticket API. AI analysis is advisory; proposed production changes are never executed by this screen.
              </div>
              <div style={{ marginTop: 12 }}>
                <Notice tone="warn">Verify that the selected time window matches the incident. A successful API response does not mean the cause is confirmed.</Notice>
              </div>
            </div>
          </Panel>
        )}
      </div>
    </div>
  </div>;
}

