import type {
  AnalysisReport,
  KnowledgeDocumentDetail,
  KnowledgeDocument,
  RetrievalResponse,
  Ticket,
  TicketComment,
  TicketListResponse,
  AuthUser,
} from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? `${window.location.protocol}//${window.location.hostname}:8000`;
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: unknown } | null;
    let message = `Request failed (${response.status})`;
    if (body?.detail) {
      if (typeof body.detail === "string") {
        message = body.detail;
      } else if (Array.isArray(body.detail)) {
        message = body.detail
          .map((item: { loc?: string[]; msg?: string }) => {
            const field = item.loc && item.loc.length > 0 ? item.loc[item.loc.length - 1] : "field";
            return `${field}: ${item.msg}`;
          })
          .join("; ");
      } else if (typeof body.detail === "object") {
        message = JSON.stringify(body.detail);
      }
    }
    throw new Error(message);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  baseUrl: API_BASE,
  me: () => request<AuthUser>("/api/auth/me"),
  login: (username: string, password: string) => request<{ user: AuthUser }>("/api/auth/login", { method: "POST", body: JSON.stringify({ username, password }) }),
  changePassword: (current_password: string, new_password: string) => request<AuthUser>("/api/auth/change-password", { method: "POST", body: JSON.stringify({ current_password, new_password }) }),
  logout: () => request<void>("/api/auth/logout", { method: "POST" }),
  listUsers: () => request<AuthUser[]>("/api/users?limit=200"),
  createUser: (payload: { username: string; email: string; full_name: string; role: "technician" | "employee" }) => request<AuthUser & { temporary_password: string }>("/api/users", { method: "POST", body: JSON.stringify(payload) }),
  setUserActive: (id: number, is_active: boolean) => request<AuthUser>(`/api/users/${id}/active`, { method: "PATCH", body: JSON.stringify({ is_active }) }),
  resetPassword: (id: number) => request<{ user: AuthUser; temporary_password: string }>(`/api/users/${id}/reset-password`, { method: "POST" }),
  listTickets: (params = "limit=100") => request<TicketListResponse>(`/api/tickets?${params}`),
  getTicket: (id: string) => request<Ticket>(`/api/tickets/${encodeURIComponent(id)}`),
  createTicket: (payload: Record<string, unknown>) => request<Ticket>("/api/tickets", { method: "POST", body: JSON.stringify(payload) }),
  updateStatus: (id: string, status: string) => request<Ticket>(`/api/tickets/${encodeURIComponent(id)}/status`, { method: "PATCH", body: JSON.stringify({ status }) }),
  publishResponse: (id: string, response: string) => request<Ticket>(`/api/tickets/${encodeURIComponent(id)}/response`, { method: "PATCH", body: JSON.stringify({ response }) }),
  listComments: (id: string) => request<TicketComment[]>(`/api/tickets/${encodeURIComponent(id)}/comments`),
  addComment: (id: string, content: string, comment_type = "comment") => request<TicketComment>(`/api/tickets/${encodeURIComponent(id)}/comments`, { method: "POST", body: JSON.stringify({ content, comment_type }) }),

  listDocuments: () => request<{ items: KnowledgeDocument[]; total: number; limit: number; offset: number }>("/api/knowledge/documents?limit=100"),
  getDocument: (id: string) => request<KnowledgeDocumentDetail>(`/api/knowledge/documents/${encodeURIComponent(id)}`),
  uploadDocument: (payload: Record<string, unknown>) => request<{ document_id: string; documents_upserted: number; chunks_upserted: number }>("/api/knowledge/ingest", { method: "POST", body: JSON.stringify(payload) }),
  retrieve: (payload: Record<string, unknown>) => request<RetrievalResponse>("/api/ai/retrieve", { method: "POST", body: JSON.stringify(payload) }),
  analyze: (payload: Record<string, unknown>) => request<AnalysisReport>("/api/ai/analyze", { method: "POST", body: JSON.stringify(payload) }),
  listApprovals: () => request<ApprovalApiItem[]>("/api/approvals?limit=100"),
  createApproval: (payload: { ticket_id: string; action: string; rationale: string }) => request<ApprovalApiItem>("/api/approvals", { method: "POST", body: JSON.stringify(payload) }),
  decideApproval: (id: string, decision: "approved" | "rejected", note: string) => request<ApprovalApiItem>(`/api/approvals/${encodeURIComponent(id)}/decision`, { method: "POST", body: JSON.stringify({ decision, note }) }),
};

export interface ApprovalApiItem {
  approval_id: string;
  ticket_id: string;
  action: string;
  rationale: string;
  status: "pending" | "approved" | "rejected";
  requested_by: string;
  decided_by: string | null;
  decision_note: string | null;
  created_at: string;
  decided_at: string | null;
}

export function redactPreview(text: string): string {
  return text
    .replace(/\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi, "[REDACTED_EMAIL]")
    .replace(/\b(?:\d{1,3}\.){3}\d{1,3}\b/g, "[REDACTED_IP]")
    .replace(/\b(password|passwd|pwd|token|api[_-]?key|secret)\b\s*[:=]\s*['"]?[^'"\s]+/gi, "$1=[REDACTED_SECRET]");
}
