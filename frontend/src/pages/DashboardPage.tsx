import { Activity, Database, FileCheck2, Gauge } from "lucide-react";
import type { BenchmarkRow, Ticket } from "../types";
import { benchmarkDisclosure } from "../services/mockData";
import { Notice, PageHeading, Panel } from "../components/ui";

function percent(value: number) { return `${(value * 100).toFixed(1)}%`; }

export default function DashboardPage({ tickets, benchmarks }: { tickets: Ticket[]; benchmarks: BenchmarkRow[] }) {
  const p1 = tickets.filter((ticket) => ticket.priority.toLowerCase() === "p1").length;
  const open = tickets.filter((ticket) => !["resolved", "closed"].includes(ticket.status)).length;
  const byCategory = ["server_api", "database", "network"].map((category) => ({ category, count: tickets.filter((ticket) => ticket.category === category).length }));
  const largest = Math.max(...byCategory.map((row) => row.count), 1);
  return <div className="page-wrap">
    <PageHeading title="Operations dashboard" description="Operational counts are derived from the current ticket API result set. Retrieval benchmark is an exploratory V2 report, not a production KPI." />
    <div className="kpi-grid">
      <Panel className="kpi"><div className="kpi-label">Tickets loaded</div><div className="kpi-value mono">{tickets.length}</div><div className="kpi-note">API result set · max 100</div></Panel>
      <Panel className="kpi"><div className="kpi-label">Open tickets</div><div className="kpi-value mono">{open}</div><div className="kpi-note">Not resolved or closed</div></Panel>
      <Panel className="kpi"><div className="kpi-label">P1 priority</div><div className="kpi-value mono" style={{ color: p1 ? "#b42318" : undefined }}>{p1}</div><div className="kpi-note">Current loaded records</div></Panel>
      <Panel className="kpi"><div className="kpi-label">RCA quality KPI</div><div className="kpi-value" style={{ fontSize: 16 }}>Not validated</div><div className="kpi-note">Insufficient independent ground truth</div></Panel>
    </div>
    <div className="two-col" style={{ marginBottom: 14 }}>
      <Panel title="Tickets by category" subtitle="Counts in the currently loaded ticket set"><div className="panel-body">{byCategory.map(({ category, count }) => <div className="bar-row" key={category}><span>{category.replace("_", " ")}</span><div className="bar-track"><div className="bar-fill" style={{ width: `${count / largest * 100}%` }} /></div><span className="mono">{count}</span></div>)}</div></Panel>
      <Panel title="System status" subtitle="Integration scope"><div className="panel-body" style={{ display: "grid", gap: 12 }}><div className="meta-line"><Activity size={14} /> Tickets, retrieval and RCA use FastAPI when connected</div><div className="meta-line"><Database size={14} /> Knowledge documents/chunks persist in PostgreSQL</div><div className="meta-line"><Gauge size={14} /> Embedding index status is not exposed by a dashboard API</div><div className="meta-line"><FileCheck2 size={14} /> Approval decisions are session-local mock data</div></div></Panel>
    </div>
    <Panel title="Retrieval benchmark · E1–E4" subtitle="Metrics copied from the V2 exploratory test report">
      <div className="data-table-wrap"><table className="benchmark-table"><thead><tr><th>Configuration</th><th>Recall@5</th><th>Precision@5</th><th>MRR@10</th><th>nDCG@5</th><th>p95 (ms)</th></tr></thead><tbody>{benchmarks.map((row) => <tr key={row.name}><td style={{ fontWeight: 650, color: "#344357" }}>{row.name}</td><td className="mono">{percent(row.recall)}</td><td className="mono">{percent(row.precision)}</td><td className="mono">{row.mrr.toFixed(4)}</td><td className="mono">{row.ndcg.toFixed(4)}</td><td className="mono">{row.p95.toFixed(1)}</td></tr>)}</tbody></table></div>
      <div className="panel-body" style={{ paddingTop: 11 }}><Notice tone="warn">{benchmarkDisclosure} E2 is not present in this report’s result set, and no trustworthy E5 RCA accuracy or hallucination score is available. These numbers are not stable operational performance.</Notice></div>
    </Panel>
    <div style={{ marginTop: 14 }}><Notice tone="info">MTTR and SLA compliance are omitted because event history and SLA clock data are not represented by the current API.</Notice></div>
  </div>;
}
