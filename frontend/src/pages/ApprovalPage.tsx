import { Ban, Check, Clock3, FileWarning, ShieldCheck } from "lucide-react";
import { useState } from "react";
import type { ApprovalItem } from "../types";
import { Notice, PageHeading, Panel } from "../components/ui";

export default function ApprovalPage({ items, onDecision }: { items: ApprovalItem[]; onDecision: (id: string, status: "approved" | "rejected", note: string) => void }) {
  const [notes, setNotes] = useState<Record<string, string>>({});
  const pending = items.filter((item) => item.status === "pending");
  const complete = items.filter((item) => item.status !== "pending");
  return <div className="page-wrap">
    <PageHeading title="Approval review" description="Review proposed remediation before any operational change." />
    <div style={{ marginBottom: 14 }}><Notice tone="warn">Demo identities are used for this local workflow. Decisions are saved to the backend audit store; no production commands are executed.</Notice></div>
    <div className="two-col">
      <Panel title="Pending requests" subtitle={`${pending.length} awaiting review`}>
        <div className="panel-body">{pending.length === 0 ? <div className="empty-state">No pending requests. Start from a report and select “Request review”.</div> : <div className="stack">{pending.map((item) => <div key={item.id} style={{ padding: 13, border: "1px solid #e6ebf0", borderRadius: 6 }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 8, flexWrap: "wrap" }}><strong className="ticket-id">{item.ticketId}</strong><span className="meta-line mono"><Clock3 size={12} />{new Date(item.createdAt).toLocaleString()}</span></div>
          <div style={{ marginTop: 9, fontSize: 12, lineHeight: 1.55, color: "#344357" }}>{item.action}</div>
          <div className="meta-line" style={{ marginTop: 6 }}>Risk level · {item.risk.toUpperCase()} · policy checks required</div>
          <div className="code-box" style={{ marginTop: 10 }}>EXECUTION BLOCKED IN DEMO{"\n"}{item.action}</div>
          <div className="field" style={{ marginTop: 10 }}><label htmlFor={`note-${item.id}`}>Reviewer note</label><textarea id={`note-${item.id}`} className="textarea" placeholder="Record why this should be approved or rejected" value={notes[item.id] ?? ""} onChange={(event) => setNotes({ ...notes, [item.id]: event.target.value })} /></div>
          <div style={{ display: "flex", gap: 8, marginTop: 10 }}><button className="btn btn-success" onClick={() => onDecision(item.id, "approved", notes[item.id] ?? "")}><Check size={14} />Approve mock</button><button className="btn btn-danger" onClick={() => onDecision(item.id, "rejected", notes[item.id] ?? "")}><Ban size={14} />Reject</button></div>
        </div>)}</div>}</div>
      </Panel>
      <div className="stack">
        <Panel title="Policy checks"><div className="panel-body" style={{ display: "grid", gap: 10 }}><div className="meta-line"><ShieldCheck size={14} color="#16865d" /> No automatic command execution path in this frontend</div><div className="meta-line"><FileWarning size={14} color="#b07b22" /> Capacity guardrail must be checked by a technician</div><div className="meta-line"><FileWarning size={14} color="#b07b22" /> Change freeze window is not connected to a source</div><div className="meta-line"><ShieldCheck size={14} color="#16865d" /> Add a reviewer note for audit-quality decisions</div><Notice tone="info">These are interface reminders, not an enforced backend policy engine.</Notice></div></Panel>
        <Panel title="Recent decisions" subtitle="Persisted approval records"><div className="panel-body">{complete.length ? <div className="file-list">{complete.slice().reverse().map((item) => <div className="file-item" key={item.id}><span style={{ color: item.status === "approved" ? "#16865d" : "#b42318" }}>{item.status === "approved" ? <Check size={16} /> : <Ban size={16} />}</span><div><strong>{item.ticketId} · {item.status}</strong><span>{item.note || "No reviewer note"}</span></div><span className="score">{new Date(item.createdAt).toLocaleTimeString()}</span></div>)}</div> : <div className="empty-state">No decisions recorded.</div>}</div></Panel>
      </div>
    </div>
  </div>;
}
