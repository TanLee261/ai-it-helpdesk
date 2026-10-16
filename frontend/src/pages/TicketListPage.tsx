import { Filter, Plus, Search } from "lucide-react";
import { useMemo, useState } from "react";
import type { Ticket, TicketStatus } from "../types";
import { Notice, PageHeading, Panel, TicketTable } from "../components/ui";

export default function TicketListPage({ tickets, demoMode, onSelect, onCreate, onStatus, canManage }: {
  tickets: Ticket[]; demoMode: boolean; onSelect: (ticket: Ticket) => void; onCreate: () => void; onStatus: (ticket: Ticket, status: TicketStatus) => void; canManage: boolean;
}) {
  const [search, setSearch] = useState("");
  const [service, setService] = useState("");
  const [priority, setPriority] = useState("");
  const [status, setStatus] = useState("");
  const visible = useMemo(() => tickets.filter((ticket) => {
    const text = `${ticket.ticket_id} ${ticket.title} ${ticket.description} ${ticket.service}`.toLowerCase();
    return (!search || text.includes(search.toLowerCase())) && (!service || ticket.service === service) && (!priority || ticket.priority === priority) && (!status || ticket.status === status);
  }), [tickets, search, service, priority, status]);
  const critical = tickets.filter((ticket) => ticket.priority.toLowerCase() === "p1").length;
  const investigating = tickets.filter((ticket) => ticket.status === "in_progress").length;
  return <div className="page-wrap">
    <PageHeading title="IT incident tickets" description="Triage service requests, review priority and move from ticket context into evidence-backed incident analysis." actions={<button className="btn btn-primary" onClick={onCreate}><Plus size={14} />Create ticket</button>} />
    {demoMode && <div style={{ marginBottom: 14 }}><Notice tone="warn">Backend is not connected. Showing local interface preview data; changes in this mode are not persisted.</Notice></div>}
    <div className="kpi-grid">
      <Panel className="kpi"><div className="kpi-label">Tickets in view</div><div className="kpi-value mono">{tickets.length}</div><div className="kpi-note">Current API result set</div></Panel>
      <Panel className="kpi"><div className="kpi-label">P1 critical</div><div className="kpi-value mono" style={{ color: critical ? "#b42318" : undefined }}>{critical}</div><div className="kpi-note">Require immediate triage</div></Panel>
      <Panel className="kpi"><div className="kpi-label">Investigating</div><div className="kpi-value mono">{investigating}</div><div className="kpi-note">Status in progress</div></Panel>
      <Panel className="kpi"><div className="kpi-label">SLA compliance</div><div className="kpi-value mono">Not tracked</div><div className="kpi-note">No SLA target/clock API yet</div></Panel>
    </div>
    <Panel title="Ticket queue" subtitle={`${visible.length} matching tickets`}>
      <div style={{ padding: "13px 14px", display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap", borderBottom: "1px solid #edf0f4" }}>
        <div className="filters"><div className="search-wrap"><Search size={14} /><input className="input" placeholder="Search ID, title, symptom or service" value={search} onChange={(event) => setSearch(event.target.value)} /></div><select className="select" style={{ width: 155 }} value={service} onChange={(event) => setService(event.target.value)}><option value="">All services</option>{[...new Set(tickets.map((ticket) => ticket.service))].sort().map((name) => <option key={name}>{name}</option>)}</select><select className="select" style={{ width: 126 }} value={priority} onChange={(event) => setPriority(event.target.value)}><option value="">All priorities</option>{["p1", "p2", "p3", "p4"].map((level) => <option key={level} value={level}>{level.toUpperCase()}</option>)}</select><select className="select" style={{ width: 165 }} value={status} onChange={(event) => setStatus(event.target.value)}><option value="">All statuses</option>{["new", "assigned", "in_progress", "waiting_for_employee", "resolved", "closed"].map((item) => <option key={item} value={item}>{item.replaceAll("_", " ")}</option>)}</select></div>
        <button className="btn btn-small" onClick={() => { setSearch(""); setService(""); setPriority(""); setStatus(""); }}><Filter size={13} />Reset</button>
      </div>
      <TicketTable tickets={visible} onSelect={onSelect} onStatus={onStatus} canManage={canManage} />
    </Panel>
  </div>;
}
