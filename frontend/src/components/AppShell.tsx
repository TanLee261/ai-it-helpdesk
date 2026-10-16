import { Activity, BookOpenText, ClipboardList, LayoutDashboard, LogOut, Menu, Plus, ShieldCheck, Users, X } from "lucide-react";
import type { ReactNode } from "react";
import { useState } from "react";
import type { PageId } from "../types";
import { pageNames } from "./ui";
import type { AuthUser } from "../types";

const nav: { id: PageId; icon: typeof ClipboardList; label: string }[] = [
  { id: "tickets", icon: ClipboardList, label: "Tickets" },
  { id: "knowledge", icon: BookOpenText, label: "Knowledge base" },
  { id: "report", icon: Activity, label: "Incident analysis" },
  { id: "approvals", icon: ShieldCheck, label: "Approval review" },
  { id: "dashboard", icon: LayoutDashboard, label: "Dashboard & evaluation" },
  { id: "users", icon: Users, label: "User accounts" },
];

export default function AppShell({ page, onNavigate, onNewTicket, onLogout, user, children, apiOnline, pendingCount }: {
  page: PageId;
  onNavigate: (page: PageId) => void;
  onNewTicket: () => void;
  onLogout: () => void;
  user: AuthUser;
  children: ReactNode;
  apiOnline: boolean;
  pendingCount: number;
}) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = (target: PageId) => { onNavigate(target); setMobileOpen(false); };
  const visibleNav = nav.filter((item) => user.role !== "employee" || item.id === "tickets");
  return <div className="app-shell">
    <aside className={`sidebar ${mobileOpen ? "mobile-open" : ""}`}>
      <div className="brand"><div className="brand-mark"><Activity size={18} /></div><div><div className="brand-name">Incident Desk</div><div className="brand-caption">AI IT Helpdesk</div></div><button className="btn btn-subtle mobile-menu" style={{ marginLeft: "auto" }} onClick={() => setMobileOpen(false)} aria-label="Close menu"><X size={16} /></button></div>
      <div className="side-label">Workspace</div>
      <nav className="nav-list" aria-label="Main navigation">{visibleNav.map(({ id, icon: Icon, label }) => <button key={id} className={`nav-link ${page === id || (id === "tickets" && page === "ticket-detail") ? "active" : ""}`} onClick={() => navigate(id)}><Icon size={16} /><span>{label}</span>{id === "approvals" && pendingCount > 0 && <span className="nav-count">{pendingCount}</span>}</button>)}</nav>
      <div className="sidebar-bottom"><button className="btn btn-primary" style={{ width: "100%" }} onClick={onNewTicket}><Plus size={15} />Create ticket</button><div className={`connection ${apiOnline ? "online" : ""}`} style={{ marginTop: 10 }}><i className="connection-dot" />{apiOnline ? "Backend connected" : "Preview mode · API offline"}</div></div>
    </aside>
    <main className="main-area">
      <header className="topbar"><div className="breadcrumb"><button className="btn btn-subtle btn-small mobile-menu" onClick={() => setMobileOpen(true)} aria-label="Open menu"><Menu size={17} /></button><span>Workspace</span><span>/</span><strong>{pageNames[page]}</strong></div><div className="top-actions"><span className="user-chip">{user.full_name} · {user.role}</span><button className="btn btn-small top-new-label" onClick={onNewTicket}><Plus size={14} />New ticket</button><button className="btn btn-subtle btn-small" onClick={onLogout} title="Sign out" aria-label="Sign out"><LogOut size={15} /></button></div></header>
      {children}
    </main>
  </div>;
}
