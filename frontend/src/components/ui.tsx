import type { ReactNode } from "react";
import { AlertTriangle, CheckCircle2, ChevronRight, CircleHelp, LoaderCircle, X } from "lucide-react";
import type { AnalysisEvidence, PageId, Ticket, TicketStatus } from "../types";

export const pageNames: Record<PageId, string> = {
  tickets: "Tickets",
  "ticket-detail": "Ticket detail",
  report: "Incident analysis",
  knowledge: "Knowledge base",
  approvals: "Approval review",
  dashboard: "Operations dashboard",
  users: "User accounts",
};

export function PageHeading({ title, description, actions }: { title: string; description?: string; actions?: ReactNode }) {
  return <div className="page-heading"><div><h1>{title}</h1>{description && <p>{description}</p>}</div>{actions && <div className="heading-actions">{actions}</div>}</div>;
}

export function Panel({ title, subtitle, action, children, className = "" }: { title?: string; subtitle?: ReactNode; action?: ReactNode; children: ReactNode; className?: string }) {
  return <section className={`panel ${className}`}>{title && <div className="panel-head"><div><div className="panel-title">{title}</div>{subtitle && <div className="panel-subtitle">{subtitle}</div>}</div>{action}</div>}{children}</section>;
}

export function Notice({ children, tone = "info" }: { children: ReactNode; tone?: "info" | "warn" | "success" | "error" }) {
  const Icon = tone === "warn" ? AlertTriangle : tone === "success" ? CheckCircle2 : CircleHelp;
  return <div className={`notice ${tone === "info" ? "" : tone}`}><Icon size={15} /><div>{children}</div></div>;
}

export function StatusLabel({ status }: { status: string }) {
  const names: Record<string, string> = {
    new: "New",
    assigned: "Assigned",
    in_progress: "Investigating",
    waiting_for_employee: "Waiting for Employee",
    resolved: "Resolved",
    closed: "Closed",
  };
  return <span className="status-text"><i className={`status-dot ${status}`} />{names[status] ?? status}</span>;
}

export function PriorityLabel({ priority }: { priority: string }) {
  return <span className={`severity ${priority.toLowerCase()}`}>{priority.toUpperCase()}</span>;
}

export function TicketTable({ tickets, onSelect, onStatus, canManage }: { tickets: Ticket[]; onSelect: (ticket: Ticket) => void; onStatus: (ticket: Ticket, status: TicketStatus) => void; canManage: boolean }) {
  if (!tickets.length) return <div className="empty-state">No matching tickets.</div>;
  return <div className="data-table-wrap"><table className="data-table"><thead><tr><th>Ticket</th><th>Summary</th><th>Service</th><th>Priority</th><th>Status</th><th>Assigned team</th><th>Updated</th><th /></tr></thead><tbody>{tickets.map((ticket) => <tr key={ticket.ticket_id}>
    <td><button className="ticket-id mono" onClick={() => onSelect(ticket)}>{ticket.ticket_id}</button><div className="cell-caption">{new Date(ticket.created_at).toLocaleDateString()}</div></td>
    <td><div className="cell-title">{ticket.title}</div><div className="cell-caption">{ticket.description.slice(0, 98)}{ticket.description.length > 98 ? "…" : ""}</div></td>
    <td>{ticket.service}<div className="cell-caption">{ticket.category.replaceAll("_", " ")}</div></td>
    <td><PriorityLabel priority={ticket.priority} /></td>
    <td>{canManage ? <select aria-label={`Status ${ticket.ticket_id}`} className="select" style={{ width: 140, minHeight: 29, padding: "4px 7px", fontSize: 10 }} value={ticket.status} onChange={(event) => onStatus(ticket, event.target.value as TicketStatus)}><option value="new">New</option><option value="assigned">Assigned</option><option value="in_progress">Investigating</option><option value="waiting_for_employee">Waiting for Employee</option><option value="resolved">Resolved</option><option value="closed">Closed</option></select> : <StatusLabel status={ticket.status} />}</td>
    <td>{canManage ? ticket.assigned_team ?? "Unassigned" : ticket.technician_response ? "Response available" : "Awaiting technician"}</td>
    <td className="mono">{new Date(ticket.updated_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</td>
    <td><button className="btn btn-small" onClick={() => onSelect(ticket)}>Open <ChevronRight size={13} /></button></td>
  </tr>)}</tbody></table></div>;
}

export function EvidenceButton({ id, onClick }: { id: string; onClick: (id: string) => void }) {
  return <button className="citation" onClick={() => onClick(id)}>[{id}]</button>;
}

export function EvidenceDialog({ evidence, onClose }: { evidence: AnalysisEvidence | null; onClose: () => void }) {
  if (!evidence) return null;
  return <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
    <section className="modal" role="dialog" aria-modal="true" aria-labelledby="evidence-heading">
      <div className="modal-head"><div><h2 id="evidence-heading">Evidence source</h2><div className="panel-subtitle mono">{evidence.evidence_id} · {evidence.source_type}</div></div><button className="btn btn-subtle btn-small" aria-label="Close evidence" onClick={onClose}><X size={16} /></button></div>
      <div className="modal-body">
        <div className="detail-kv" style={{ margin: 0, padding: 0, border: 0 }}><div><div className="kv-label">Service</div><div className="kv-value">{evidence.service}</div></div><div><div className="kv-label">Timestamp</div><div className="kv-value mono">{evidence.timestamp ? new Date(evidence.timestamp).toLocaleString() : "Not supplied"}</div></div></div>
        <div style={{ marginTop: 15 }}><div className="kv-label">Source content</div><pre className="code-box">{evidence.content}</pre></div>
        <div style={{ marginTop: 12 }}><Notice tone="warn">Evidence is context, not proof of cause. Validate source, time window and access permissions before acting.</Notice></div>
      </div>
      <div className="modal-foot"><button className="btn" onClick={onClose}>Close</button></div>
    </section>
  </div>;
}

export function Loading({ label = "Loading" }: { label?: string }) {
  return <div className="empty-state" style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}><LoaderCircle size={15} className="animate-spin" />{label}</div>;
}
