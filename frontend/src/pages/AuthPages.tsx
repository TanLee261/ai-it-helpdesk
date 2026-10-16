import { Activity, LogIn, UserPlus } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import type { AuthUser } from "../types";
import { api } from "../services/api";
import { Notice, PageHeading, Panel } from "../components/ui";

export function LoginPage({ onLogin }: { onLogin: (username: string, password: string) => Promise<void> }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  return <main className="auth-screen"><form className="auth-panel" onSubmit={async (event) => { event.preventDefault(); setBusy(true); setError(""); try { await onLogin(username, password); } catch (e) { setError(e instanceof Error ? e.message : "Sign in failed"); } finally { setBusy(false); } }}>
    <div className="auth-brand"><span className="brand-mark"><Activity size={18} /></span><div><strong>Incident Desk</strong><small>AI IT Helpdesk</small></div></div>
    <h1>Sign in</h1><p>Use the account created by your administrator or technician.</p>
    {error && <Notice tone="error">{error}</Notice>}
    <div className="field"><label htmlFor="login-identity">Username or email</label><input id="login-identity" className="input" autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} required /></div>
    <div className="field"><label htmlFor="login-password">Password</label><input id="login-password" className="input" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required /></div>
    <button className="btn btn-primary" type="submit" disabled={busy}><LogIn size={15} />{busy ? "Signing in…" : "Sign in"}</button>
  </form></main>;
}

export function ChangePasswordPage({ user, onChanged, forced }: { user: AuthUser; onChanged: (user: AuthUser) => void; forced: boolean }) {
  const [current, setCurrent] = useState(""); const [next, setNext] = useState(""); const [confirm, setConfirm] = useState(""); const [error, setError] = useState(""); const [busy, setBusy] = useState(false);
  return <main className="auth-screen"><form className="auth-panel" onSubmit={async (event) => { event.preventDefault(); setError(""); if (next !== confirm) { setError("The new passwords do not match."); return; } setBusy(true); try { onChanged(await api.changePassword(current, next)); } catch (e) { setError(e instanceof Error ? e.message : "Could not change password"); } finally { setBusy(false); } }}>
    <div className="auth-brand"><span className="brand-mark"><Activity size={18} /></span><div><strong>Secure your account</strong><small>{user.username}</small></div></div>
    <h1>{forced ? "Change temporary password" : "Change password"}</h1><p>{forced ? "You must choose a new password before using the helpdesk." : "Enter your current password and choose a new one."}</p>
    {error && <Notice tone="error">{error}</Notice>}
    <div className="field"><label htmlFor="current-password">Current password</label><input id="current-password" className="input" type="password" autoComplete="current-password" value={current} onChange={(e) => setCurrent(e.target.value)} required /></div>
    <div className="field"><label htmlFor="new-password">New password</label><input id="new-password" className="input" type="password" autoComplete="new-password" value={next} onChange={(e) => setNext(e.target.value)} minLength={12} required /><small>12–128 characters, including a letter and a number.</small></div>
    <div className="field"><label htmlFor="confirm-password">Confirm new password</label><input id="confirm-password" className="input" type="password" autoComplete="new-password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required /></div>
    <button className="btn btn-primary" type="submit" disabled={busy}>{busy ? "Saving…" : "Save password"}</button>
  </form></main>;
}

export function UserManagementPage({ currentUser }: { currentUser: AuthUser }) {
  const [users, setUsers] = useState<AuthUser[]>([]);
  const [role, setRole] = useState<"employee" | "technician">("employee");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [temporaryPassword, setTemporaryPassword] = useState("");
  const [resetNotice, setResetNotice] = useState<{ username: string; password: string } | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = async () => setUsers(await api.listUsers());
  useEffect(() => { void load().catch((e) => setError(e instanceof Error ? e.message : "Could not load accounts")); }, []);

  const create = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    setTemporaryPassword("");
    const cleanUsername = username.trim().toLowerCase().replace(/\s+/g, ".");
    const cleanEmail = email.trim().toLowerCase();
    const cleanFullName = fullName.trim();
    try {
      const user = await api.createUser({ username: cleanUsername, email: cleanEmail, full_name: cleanFullName, role });
      setTemporaryPassword(user.temporary_password);
      setUsername("");
      setEmail("");
      setFullName("");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not create account");
    } finally {
      setBusy(false);
    }
  };

  const handleResetPassword = async (user: AuthUser) => {
    if (!window.confirm(`Reset password for ${user.username} (${user.full_name})? A new one-time temporary password will be generated.`)) return;
    setError("");
    setResetNotice(null);
    try {
      const result = await api.resetPassword(user.id);
      setResetNotice({ username: user.username, password: result.temporary_password });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not reset password");
    }
  };

  return <div className="page-wrap"><PageHeading title="User accounts" description="Create accounts with least-privilege roles, reset passwords, and revoke access when needed." />
    <div className="detail-grid">
      <Panel title="Create account" subtitle={currentUser.role === "admin" ? "Administrators can create technicians and employees." : "Technicians can create employee accounts only."}>
        <form className="panel-body user-form" onSubmit={create}>
          {error && <Notice tone="error">{error}</Notice>}
          {temporaryPassword && <Notice tone="success">Account created! Temporary password (shown once): <code>{temporaryPassword}</code>. Share it securely; the user must change it at first sign-in.</Notice>}
          {resetNotice && <Notice tone="success">Password reset for <strong>{resetNotice.username}</strong>! Temporary password: <code>{resetNotice.password}</code>. The user must change it upon sign-in.</Notice>}
          <div className="field">
            <label htmlFor="new-fullname">Full name (Họ và tên)</label>
            <input id="new-fullname" className="input" placeholder="e.g. Nguyen Van A" value={fullName} onChange={(e) => setFullName(e.target.value)} required />
          </div>
          <div className="field">
            <label htmlFor="new-username">Username (Tên đăng nhập)</label>
            <input id="new-username" className="input" placeholder="e.g. nhanvien01 or tuan.nv" value={username} onChange={(e) => setUsername(e.target.value)} required />
            <small style={{ color: "#64748b", fontSize: 10, marginTop: 3 }}>Tối thiểu 3 ký tự, không dấu cách (chữ cái, số, dấu '.', '_', '-')</small>
          </div>
          <div className="field">
            <label htmlFor="new-email">Email</label>
            <input id="new-email" className="input" type="email" placeholder="e.g. employee@company.com" value={email} onChange={(e) => setEmail(e.target.value)} required />
            <small style={{ color: "#64748b", fontSize: 10, marginTop: 3 }}>Định dạng: ten@company.com</small>
          </div>
          {currentUser.role === "admin" && (
            <div className="field">
              <label htmlFor="new-role">Role (Vai trò)</label>
              <select id="new-role" className="select" value={role} onChange={(e) => setRole(e.target.value as "employee" | "technician")}>
                <option value="employee">Employee (Nhân viên)</option>
                <option value="technician">Technician (Kỹ thuật viên)</option>
              </select>
            </div>
          )}
          <button className="btn btn-primary" disabled={busy}><UserPlus size={14} />{busy ? "Creating…" : `Create ${role}`}</button>
        </form>
      </Panel>
      <Panel title="Accounts" subtitle={`${users.length} accounts visible to your role`}>
        <div className="data-table-wrap">
          <table className="data-table">
            <thead><tr><th>Name</th><th>Username</th><th>Role</th><th>Status</th><th>First login</th><th>Actions</th></tr></thead>
            <tbody>
              {users.map((user) => {
                const isLocked = Boolean(user.locked_until && new Date(user.locked_until).getTime() > Date.now());
                const statusText = !user.is_active ? "Disabled" : isLocked ? "Locked (failed logins)" : "Active";
                const canManageUser = currentUser.role === "admin" || (currentUser.role === "technician" && user.role === "employee");
                return <tr key={user.id}>
                  <td>{user.full_name}<div className="cell-caption">{user.email}</div></td>
                  <td className="mono">{user.username}</td>
                  <td><span className={`comment-badge ${user.role}`}>{user.role}</span></td>
                  <td><span style={{ color: !user.is_active ? "#b91c1c" : isLocked ? "#d97706" : "#15803d", fontWeight: 600 }}>{statusText}</span></td>
                  <td>{user.must_change_password ? <span style={{ color: "#d97706" }}>Password change required</span> : <span style={{ color: "#15803d" }}>Active</span>}</td>
                  <td>
                    {canManageUser && user.id !== currentUser.id && (
                      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                        <button className="btn btn-small" title="Reset temporary password" onClick={() => void handleResetPassword(user)}>Reset pwd</button>
                        <button className={`btn btn-small ${user.is_active ? "btn-danger" : "btn-success"}`} onClick={async () => { try { await api.setUserActive(user.id, !user.is_active); await load(); } catch (e) { setError(e instanceof Error ? e.message : "Could not update account"); } }}>{user.is_active ? "Lock" : "Unlock"}</button>
                      </div>
                    )}
                  </td>
                </tr>;
              })}
            </tbody>
          </table>
          {!users.length && <div className="empty-state">No accounts to display.</div>}
        </div>
      </Panel>
    </div>
  </div>;
}

