import { AlertTriangle, BookOpenText, CheckCircle2, FileText, LoaderCircle, ShieldCheck, Upload } from "lucide-react";
import { useRef, useState } from "react";
import type { KnowledgeDocument } from "../types";
import { Notice, PageHeading, Panel } from "../components/ui";

export default function KnowledgePage({ documents, loading, onUpload, onDocument }: {
  documents: KnowledgeDocument[]; loading: boolean; onUpload: (payload: { title: string; source: string; source_type: string; content: string; service: string; category: string; document_id: string }) => Promise<void>; onDocument: (document: KnowledgeDocument) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [sourceType, setSourceType] = useState("runbook");
  const [service, setService] = useState("");
  const [category, setCategory] = useState("server_api");
  const [fileText, setFileText] = useState("");
  const [filename, setFilename] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const onFile = async (file?: File) => {
    if (!file) return;
    if (file.size > 100_000) { setError("Maximum file size is 100 KB for this MVP endpoint."); return; }
    setError(""); setSuccess(""); setFilename(file.name); setFileText(await file.text());
  };
  const submit = async () => {
    if (!fileText || !filename) return;
    setBusy(true); setError(""); setSuccess("");
    const stem = filename.replace(/\.[^.]+$/, "").replace(/[^A-Za-z0-9_-]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 52) || "upload";
    const id = `${sourceType === "runbook" ? "RB" : sourceType === "log" ? "LOG" : "TCK"}-UPLOAD-${stem}`;
    try {
      await onUpload({ title: filename.replace(/\.[^.]+$/, ""), source: filename, source_type: sourceType, content: fileText, service, category, document_id: id });
      setSuccess("Document ingested and chunks persisted. Build/update the vector index separately before expecting dense retrieval to include it.");
      setFileText(""); setFilename(""); if (inputRef.current) inputRef.current.value = "";
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Upload failed"); }
    finally { setBusy(false); }
  };
  return <div className="page-wrap">
    <PageHeading title="Knowledge base" description="Upload text sources through the ingestion API, inspect redaction, and review stored documents and chunks." />
    <div style={{ marginBottom: 14 }}><Notice tone="warn">Text ingestion persists PostgreSQL document/chunk records. Vector embedding and Qdrant upsert remain a separate indexing step; binary PDF parsing is not wired into this MVP screen.</Notice></div>
    <div className="two-col">
      <Panel title="Ingest a source" subtitle="Supported: .md, .txt, .csv or .log text files · 100 KB max">
        <div className="panel-body" style={{ display: "grid", gap: 13 }}>
          <div className="field"><label htmlFor="source-type">Source type</label><select id="source-type" className="select" value={sourceType} onChange={(event) => setSourceType(event.target.value)}><option value="runbook">Runbook / SOP</option><option value="historical_ticket">Historical ticket text</option><option value="log">Log text</option></select></div>
          <div className="two-col" style={{ gridTemplateColumns: "1fr 1fr", gap: 10 }}><div className="field"><label htmlFor="service">Service (optional)</label><input id="service" className="input" placeholder="e.g. payment-api" value={service} onChange={(event) => setService(event.target.value)} /></div><div className="field"><label htmlFor="category">Category</label><select id="category" className="select" value={category} onChange={(event) => setCategory(event.target.value)}>{["server_api", "database", "network", "account", "other"].map((item) => <option key={item} value={item}>{item.replace("_", " ")}</option>)}</select></div></div>
          <input ref={inputRef} type="file" accept=".md,.txt,.csv,.log,text/plain,text/markdown,text/csv" hidden onChange={(event) => void onFile(event.target.files?.[0])} />
          <div className="upload-zone" onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); void onFile(event.dataTransfer.files[0]); }}><Upload size={20} color="#56718f" style={{ margin: "0 auto 9px" }} /><div style={{ color: "#43566c", fontSize: 12, fontWeight: 650 }}>Drop a text file or choose from device</div><div className="panel-subtitle" style={{ margin: "5px 0 11px" }}>Secret and personal-data redaction runs again on the server before chunking.</div><button className="btn btn-small" onClick={() => inputRef.current?.click()}>Choose file</button></div>
          {filename && <div className="file-item"><FileText size={17} color="#4e77a8" /><div><strong>{filename}</strong><span>{(new Blob([fileText]).size / 1024).toFixed(1)} KB · preview shows redacted text</span></div><ShieldCheck size={16} color="#16865d" /></div>}
          {filename && <div className="field"><label htmlFor="redacted-content">Redacted ingestion preview</label><textarea id="redacted-content" className="textarea mono" readOnly value={fileText.replace(/\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi, "[REDACTED_EMAIL]").replace(/\b(?:\d{1,3}\.){3}\d{1,3}\b/g, "[REDACTED_IP]").replace(/\b(password|passwd|pwd|token|api[_-]?key|secret)\b\s*[:=]\s*['"]?[^'"\s]+/gi, "$1=[REDACTED_SECRET]")} /></div>}
          {error && <Notice tone="error"><AlertTriangle size={14} />{error}</Notice>}{success && <Notice tone="success"><CheckCircle2 size={14} />{success}</Notice>}
          <button className="btn btn-primary" disabled={!filename || busy} onClick={() => void submit()}>{busy ? <LoaderCircle size={14} className="animate-spin" /> : <Upload size={14} />}{busy ? "Ingesting…" : "Redact, chunk and persist"}</button>
        </div>
      </Panel>
      <Panel title="Stored documents" subtitle={loading ? "Loading" : `${documents.length} documents returned`}>
        <div className="panel-body"><div className="file-list">{loading ? <div className="empty-state">Loading knowledge records…</div> : documents.length ? documents.map((document) => <button className="file-item" key={document.document_id} style={{ textAlign: "left", background: "#fff", width: "100%" }} onClick={() => onDocument(document)}><BookOpenText size={17} color="#4e77a8" /><div><strong>{document.title}</strong><span className="mono">{document.document_id} · {document.source_type} · {document.service || "no service"}</span></div><span className="score">{document.access_scope}</span></button>) : <div className="empty-state">No knowledge documents found. Confirm migrations and ingestion.</div>}</div><div style={{ marginTop: 13 }}><Notice>Use document detail to inspect chunks and indexing metadata. Raw credentials should never be uploaded intentionally.</Notice></div></div>
      </Panel>
    </div>
  </div>;
}
