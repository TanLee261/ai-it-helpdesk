export type PageId = "tickets" | "ticket-detail" | "report" | "knowledge" | "approvals" | "dashboard" | "users";

export interface AuthUser {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: "admin" | "technician" | "employee";
  is_active: boolean;
  must_change_password: boolean;
  failed_login_attempts?: number;
  locked_until?: string | null;
  created_at: string;
}

export type TicketStatus = "new" | "assigned" | "in_progress" | "waiting_for_employee" | "resolved" | "closed";
export type TicketPriority = "p1" | "p2" | "p3" | "p4";
export type TicketCategory = "network" | "server_api" | "database" | "account" | "other";

export interface TicketComment {
  id: number;
  ticket_id: string;
  user_id: number;
  user_name: string;
  user_role: string;
  comment_type: string;
  content: string;
  created_at: string;
}


export interface Ticket {
  id: number;
  ticket_id: string;
  source_ticket_id?: string | null;
  title: string;
  description: string;
  service: string;
  category: TicketCategory | string;
  raw_category?: string | null;
  sub_category?: string | null;
  priority: TicketPriority | string;
  impact: string;
  urgency: string;
  assigned_team?: string | null;
  auto_resolve: boolean;
  status: TicketStatus | string;
  requester_email_redacted?: string | null;
  verified_root_cause?: string | null;
  resolution?: string | null;
  technician_response?: string | null;
  response_sent_at?: string | null;
  source?: string | null;
  created_at: string;
  updated_at: string;
}

export interface TicketListResponse {
  total: number;
  limit: number;
  offset: number;
  items: Ticket[];
}

export interface KnowledgeDocument {
  id: number;
  document_id: string;
  title: string;
  source_type: string;
  source: string;
  service?: string | null;
  category?: string | null;
  version?: string | null;
  access_scope: string;
  content_hash: string;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeChunk {
  id: number;
  chunk_id: string;
  document_id: string;
  chunk_index: number;
  content: string;
  metadata_json: Record<string, unknown>;
  token_count: number;
  qdrant_point_id?: string | null;
  created_at: string;
}

export interface KnowledgeDocumentDetail extends KnowledgeDocument {
  chunks: KnowledgeChunk[];
}

export interface RetrievalResult {
  rank: number;
  score: number;
  chunk_id: string;
  document_id: string;
  source_type: string;
  source: string;
  service?: string | null;
  category?: string | null;
  access_scope: string;
  content: string;
  metadata: Record<string, unknown>;
}

export interface RetrievalResponse {
  query: string;
  retrieval_method: string;
  filters: {
    service?: string | null;
    category?: string | null;
    version?: string | null;
    source_types: string[];
    access_scope: string;
  };
  results: RetrievalResult[];
  original_query?: string | null;
  intent?: string | null;
  route?: string | null;
}

export interface CitedFact {
  fact: string;
  evidence_ids: string[];
}

export interface Hypothesis {
  cause: string;
  supporting_evidence_ids: string[];
  contradicting_evidence_ids: string[];
}

export interface VerificationStep {
  step: string;
  evidence_ids: string[];
}

export interface AnalysisEvidence {
  evidence_id: string;
  source_type: "ticket" | "historical_ticket" | "runbook" | "log" | "metric";
  content: string;
  service: string;
  timestamp?: string | null;
}

export interface AnalysisReport {
  status: "grounded" | "insufficient_evidence";
  observed_facts: CitedFact[];
  hypotheses: Hypothesis[];
  probable_root_cause?: string | null;
  root_cause_evidence_ids: string[];
  confidence: "low" | "medium" | "high";
  missing_evidence: string[];
  verification_steps: VerificationStep[];
  proposed_actions: string[];
  ticket_id: string;
  service: string;
  window_start: string;
  window_end: string;
  evidence: AnalysisEvidence[];
  model?: string | null;
  review_required: boolean;
}

export interface ApprovalItem {
  id: string;
  ticketId: string;
  action: string;
  risk: "low" | "medium" | "high" | "critical";
  status: "pending" | "approved" | "rejected";
  createdAt: string;
  note?: string;
}

export interface BenchmarkRow {
  name: string;
  recall: number;
  precision: number;
  mrr: number;
  ndcg: number;
  p95: number;
}
