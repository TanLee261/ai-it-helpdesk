import { X } from "lucide-react";
import { useState } from "react";

export interface TicketDraft {
  title: string;
  description: string;
  service: string;
  category: string;
  priority: string;
  impact: string;
  urgency: string;
  assigned_team: string;
}

const emptyDraft: TicketDraft = { title: "", description: "", service: "", category: "server_api", priority: "p3", impact: "medium", urgency: "medium", assigned_team: "" };

export default function NewTicketDialog({ open, busy, onClose, onSubmit }: { open: boolean; busy: boolean; onClose: () => void; onSubmit: (draft: TicketDraft) => void }) {
  const [draft, setDraft] = useState(emptyDraft);
  if (!open) return null;
  const set = (field: keyof TicketDraft, value: string) => setDraft((current) => ({ ...current, [field]: value }));
  const close = () => { setDraft(emptyDraft); onClose(); };
  return <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) close(); }}><form className="modal" role="dialog" aria-modal="true" aria-labelledby="create-ticket-title" onSubmit={(event) => { event.preventDefault(); onSubmit(draft); }}>
    <div className="modal-head"><div><h2 id="create-ticket-title">Create incident ticket</h2><div className="panel-subtitle">A new record is written to the ticket API when connected.</div></div><button type="button" className="btn btn-subtle btn-small" aria-label="Close dialog" onClick={close}><X size={16} /></button></div>
    <div className="modal-body" style={{ display: "grid", gap: 12 }}>
      <div className="field"><label htmlFor="ticket-title">Title</label><input id="ticket-title" className="input" minLength={3} required value={draft.title} onChange={(event) => set("title", event.target.value)} /></div>
      <div className="field"><label htmlFor="ticket-description">Description / symptoms</label><textarea id="ticket-description" className="textarea" minLength={3} required value={draft.description} onChange={(event) => set("description", event.target.value)} /></div>
      <div className="two-col" style={{ gridTemplateColumns: "1fr 1fr", gap: 10 }}><div className="field"><label htmlFor="ticket-service">Service</label><input id="ticket-service" className="input" minLength={2} required placeholder="e.g. payment-api" value={draft.service} onChange={(event) => set("service", event.target.value)} /></div><div className="field"><label htmlFor="ticket-category">Category</label><select id="ticket-category" className="select" value={draft.category} onChange={(event) => set("category", event.target.value)}>{["server_api", "database", "network", "account", "other"].map((item) => <option key={item}>{item}</option>)}</select></div></div>
      <div className="two-col" style={{ gridTemplateColumns: "repeat(3,1fr)", gap: 10 }}>{(["priority", "impact", "urgency"] as const).map((field) => <div className="field" key={field}><label htmlFor={`ticket-${field}`}>{field}</label><select id={`ticket-${field}`} className="select" value={draft[field]} onChange={(event) => set(field, event.target.value)}>{(field === "priority" ? ["p1", "p2", "p3", "p4"] : ["low", "medium", "high"]).map((item) => <option key={item}>{item}</option>)}</select></div>)}</div>
      <div className="field"><label htmlFor="ticket-team">Assigned team (optional)</label><input id="ticket-team" className="input" value={draft.assigned_team} onChange={(event) => set("assigned_team", event.target.value)} /></div>
    </div>
    <div className="modal-foot"><button type="button" className="btn" onClick={close}>Cancel</button><button className="btn btn-primary" disabled={busy}>{busy ? "Creating…" : "Create ticket"}</button></div>
  </form></div>;
}
