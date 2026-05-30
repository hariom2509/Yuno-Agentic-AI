import React, { useEffect, useState } from "react";
import { Plus, Pencil, Trash2, X, Bot } from "lucide-react";
import toast from "react-hot-toast";
import api from "../services/api";

const DEFAULT_TOOLS = ["web_search", "calculator", "report_generator", "file_reader"];
const MODELS = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "llama3-70b-8192", "llama3-8b-8192", "gemini-1.5-flash"];
const CHANNELS = ["none", "telegram"];

const DEFAULT_FORM = {
  name: "",
  role: "",
  system_prompt: "",
  model: "gpt-4o-mini",
  tools: [],
  memory_enabled: true,
  max_iterations: 5,
  max_tokens: 2000,
  channel: "none",
  schedule_config: {},
};

function AgentModal({ agent, availableTools, onClose, onSaved }) {
  const [workflows, setWorkflows] = useState([]);
  const [form, setForm] = useState(() => {
    return agent ? {
      ...DEFAULT_FORM,
      ...agent,
      schedule_config: {
        enabled: false,
        interval_minutes: 10,
        workflow_id: "",
        ...(agent.schedule_config || {})
      },
      guardrails: {
        blocked_topics: [],
        content_filter: false,
        max_output_length: 2000,
        ...(agent.guardrails || {})
      }
    } : {
      ...DEFAULT_FORM,
      schedule_config: { enabled: false, interval_minutes: 10, workflow_id: "" },
      guardrails: { blocked_topics: [], content_filter: false, max_output_length: 2000 }
    };
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.get("/workflows/").then(r => {
      setWorkflows(r.data || []);
    }).catch(() => {});
  }, []);

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));
  const setSchedule = (k, v) => setForm(f => ({
    ...f,
    schedule_config: { ...(f.schedule_config || {}), [k]: v }
  }));
  const setGuardrail = (k, v) => setForm(f => ({
    ...f,
    guardrails: { ...(f.guardrails || {}), [k]: v }
  }));

  const toggleTool = (tool) => {
    set("tools", form.tools.includes(tool)
      ? form.tools.filter(t => t !== tool)
      : [...form.tools, tool]);
  };

  const submit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.role || !form.system_prompt) {
      toast.error("Name, role, and system prompt are required.");
      return;
    }
    setSaving(true);
    try {
      if (agent?.id) {
        await api.put(`/agents/${agent.id}`, form);
        toast.success("Agent updated");
      } else {
        await api.post("/agents/", form);
        toast.success("Agent created");
      }
      onSaved();
    } catch (err) {
      toast.error("Failed to save agent");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal modal-wide">
        <div className="modal-header">
          <div className="modal-title">{agent?.id ? "Edit Agent" : "Create Agent"}</div>
          <button className="btn btn-icon btn-ghost" onClick={onClose}><X size={16} /></button>
        </div>

        <form onSubmit={submit}>
          <div className="card-grid card-grid-2">
            <div className="form-group">
              <label className="form-label">Agent Name *</label>
              <input className="form-input" value={form.name} onChange={e => set("name", e.target.value)} placeholder="Research Agent" />
            </div>
            <div className="form-group">
              <label className="form-label">Role *</label>
              <input className="form-input" value={form.role} onChange={e => set("role", e.target.value)} placeholder="researcher" />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">System Prompt *</label>
            <textarea
              className="form-textarea"
              style={{ minHeight: 100 }}
              value={form.system_prompt}
              onChange={e => set("system_prompt", e.target.value)}
              placeholder="You are a research specialist. Your goal is to..."
            />
          </div>

          <div className="card-grid card-grid-2">
            <div className="form-group">
              <label className="form-label">Model</label>
              <select className="form-select" value={form.model} onChange={e => set("model", e.target.value)}>
                {MODELS.map(m => <option key={m} value={m}>{m}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Channel</label>
              <select className="form-select" value={form.channel} onChange={e => set("channel", e.target.value)}>
                {CHANNELS.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          </div>

          <div className="card-grid card-grid-2">
            <div className="form-group">
              <label className="form-label">Max Iterations</label>
              <input className="form-input" type="number" min={1} max={20} value={form.max_iterations} onChange={e => set("max_iterations", +e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Max Tokens</label>
              <input className="form-input" type="number" min={100} max={8000} value={form.max_tokens} onChange={e => set("max_tokens", +e.target.value)} />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Tools</label>
            <div className="flex gap-8" style={{ flexWrap: "wrap" }}>
              {availableTools.map(tool => (
                <button
                  key={tool}
                  type="button"
                  className={`btn btn-sm ${form.tools.includes(tool) ? "btn-primary" : "btn-ghost"}`}
                  onClick={() => toggleTool(tool)}
                >
                  {tool}
                </button>
              ))}
            </div>
          </div>

          <div className="form-group">
            <label className="toggle">
              <input type="checkbox" checked={form.memory_enabled} onChange={e => set("memory_enabled", e.target.checked)} />
              <div className="toggle-track"><div className="toggle-thumb" /></div>
              <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>Memory Enabled</span>
            </label>
          </div>

          {/* ⏰ Execution Schedules */}
          <div className="divider" style={{ margin: "24px 0 16px" }} />
          <div style={{ fontWeight: 600, fontSize: 12, color: "var(--accent)", marginBottom: 12, letterSpacing: "0.5px" }}>⏰ EXECUTION SCHEDULING</div>
          
          <div className="card-grid card-grid-2" style={{ marginBottom: 16 }}>
            <div className="form-group" style={{ display: "flex", alignItems: "center" }}>
              <label className="toggle">
                <input type="checkbox" checked={form.schedule_config?.enabled || false} onChange={e => setSchedule("enabled", e.target.checked)} />
                <div className="toggle-track"><div className="toggle-thumb" /></div>
                <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>Enable Recurring Schedule</span>
              </label>
            </div>
            
            {form.schedule_config?.enabled && (
              <div className="form-group">
                <label className="form-label">Interval (minutes)</label>
                <input className="form-input" type="number" min={1} max={1440} value={form.schedule_config?.interval_minutes || 10} onChange={e => setSchedule("interval_minutes", +e.target.value)} />
              </div>
            )}
          </div>

          {form.schedule_config?.enabled && (
            <div className="form-group" style={{ marginBottom: 20 }}>
              <label className="form-label">Target Workflow to Run</label>
              <select className="form-select" value={form.schedule_config?.workflow_id || ""} onChange={e => setSchedule("workflow_id", e.target.value ? +e.target.value : "")}>
                <option value="">-- Select Target Workflow --</option>
                {workflows.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
              </select>
            </div>
          )}

          {/* 🛡️ Safety Guardrails */}
          <div className="divider" style={{ margin: "24px 0 16px" }} />
          <div style={{ fontWeight: 600, fontSize: 12, color: "var(--accent)", marginBottom: 12, letterSpacing: "0.5px" }}>🛡️ SAFETY GUARDRAILS</div>
          
          <div className="form-group" style={{ marginBottom: 16 }}>
            <label className="form-label">Blocked Topics / Keywords (comma-separated)</label>
            <input className="form-input" value={(form.guardrails?.blocked_topics || []).join(", ")} onChange={e => setGuardrail("blocked_topics", e.target.value.split(",").map(s => s.trim()).filter(Boolean))} placeholder="politics, violence, competitors" />
          </div>
          
          <div className="card-grid card-grid-2">
            <div className="form-group">
              <label className="form-label">Max Output Length (characters)</label>
              <input className="form-input" type="number" min={100} max={10000} value={form.guardrails?.max_output_length || 2000} onChange={e => setGuardrail("max_output_length", +e.target.value)} />
            </div>
            
            <div className="form-group" style={{ display: "flex", alignItems: "center", marginTop: 24 }}>
              <label className="toggle">
                <input type="checkbox" checked={form.guardrails?.content_filter || false} onChange={e => setGuardrail("content_filter", e.target.checked)} />
                <div className="toggle-track"><div className="toggle-thumb" /></div>
                <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>Strict Content Filter</span>
              </label>
            </div>
          </div>

          <div className="modal-footer" style={{ marginTop: 32 }}>
            <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? <span className="spinner" /> : (agent?.id ? "Update Agent" : "Create Agent")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function Agents() {
  const [agents, setAgents] = useState([]);
  const [modal, setModal] = useState(null); // null | "create" | agent object
  const [loading, setLoading] = useState(true);
  const [availableTools, setAvailableTools] = useState(DEFAULT_TOOLS);

  const load = async () => {
    try {
      const r = await api.get("/agents/");
      setAgents(r.data || []);
      const s = await api.get("/skills/");
      const skillNames = (s.data || []).map(sk => sk.name);
      setAvailableTools([...DEFAULT_TOOLS, ...skillNames]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const deleteAgent = async (id) => {
    if (!window.confirm("Delete this agent?")) return;
    await api.delete(`/agents/${id}`);
    toast.success("Agent deleted");
    load();
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="page-title">Agents</div>
          <div className="page-subtitle">Configure and manage AI agents</div>
        </div>
        <button className="btn btn-primary" onClick={() => setModal("create")}>
          <Plus size={14} /> New Agent
        </button>
      </div>

      {loading ? (
        <div className="flex items-center gap-12" style={{ color: "var(--text-muted)", padding: "40px 0" }}>
          <span className="spinner" /> Loading agents...
        </div>
      ) : agents.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🤖</div>
          <div className="empty-state-title">No agents configured</div>
          <p>Create your first agent to start building workflows.</p>
          <button className="btn btn-primary mt-16" onClick={() => setModal("create")}>
            <Plus size={14} /> Create Agent
          </button>
        </div>
      ) : (
        <div className="card-grid card-grid-3">
          {agents.map(agent => (
            <div key={agent.id} className="card" style={{ position: "relative" }}>
              <div className="flex items-center gap-12 mb-16">
                <div style={{ width: 42, height: 42, borderRadius: "50%", background: "var(--accent-glow)", border: "2px solid var(--accent)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20, flexShrink: 0 }}>🤖</div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 700, fontSize: 14, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{agent.name}</div>
                  <div style={{ fontSize: 11, color: "var(--accent)", marginTop: 2 }}>{agent.role}</div>
                </div>
              </div>

              <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 14, display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                {agent.system_prompt}
              </div>

              <div className="flex gap-8" style={{ flexWrap: "wrap", marginBottom: 14 }}>
                <span className="tag">{agent.model}</span>
                {agent.memory_enabled && <span className="tag">memory</span>}
                {agent.channel !== "none" && <span className="tag">{agent.channel}</span>}
              </div>

              {agent.tools?.length > 0 && (
                <div className="flex gap-8" style={{ flexWrap: "wrap", marginBottom: 14 }}>
                  {agent.tools.map(t => (
                    <span key={t} className="badge" style={{ background: "rgba(168,85,247,0.1)", color: "#a855f7", border: "1px solid rgba(168,85,247,0.2)" }}>{t}</span>
                  ))}
                </div>
              )}

              <div className="divider" />

              <div className="flex gap-8">
                <button className="btn btn-ghost btn-sm" onClick={() => setModal(agent)}>
                  <Pencil size={12} /> Edit
                </button>
                <button className="btn btn-danger btn-sm" onClick={() => deleteAgent(agent.id)}>
                  <Trash2 size={12} /> Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {modal && (
        <AgentModal
          agent={modal === "create" ? null : modal}
          availableTools={availableTools}
          onClose={() => setModal(null)}
          onSaved={() => { setModal(null); load(); }}
        />
      )}
    </div>
  );
}