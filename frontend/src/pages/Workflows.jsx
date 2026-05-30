import React, { useEffect, useState } from "react";
import { Plus, Play, GitBranch, X, Trash2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import api from "../services/api";

function CreateWorkflowModal({ onClose, onCreated }) {
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [saving, setSaving] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (!name.trim()) { toast.error("Name is required"); return; }
    setSaving(true);
    try {
      const r = await api.post("/workflows/", { name, description: desc, graph: { nodes: [], edges: [] } });
      toast.success("Workflow created");
      onCreated(r.data);
    } catch {
      toast.error("Failed to create workflow");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <div className="modal-title">New Workflow</div>
          <button className="btn btn-icon btn-ghost" onClick={onClose}><X size={16} /></button>
        </div>
        <form onSubmit={submit}>
          <div className="form-group">
            <label className="form-label">Name *</label>
            <input className="form-input" value={name} onChange={e => setName(e.target.value)} placeholder="Research & Analysis" />
          </div>
          <div className="form-group">
            <label className="form-label">Description</label>
            <textarea className="form-textarea" value={desc} onChange={e => setDesc(e.target.value)} placeholder="What does this workflow do?" />
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? <span className="spinner" /> : "Create Workflow"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function RunModal({ workflow, onClose }) {
  const [task, setTask] = useState("Analyze OpenAI vs Anthropic enterprise positioning");
  const [running, setRunning] = useState(false);
  const navigate = useNavigate();

  const run = async () => {
    setRunning(true);
    try {
      await api.post(`/workflows/${workflow.id}/execute`, { input_task: task });
      toast.success("Workflow started! Check Monitoring for live updates.");
      onClose();
      navigate("/monitoring");
    } catch {
      toast.error("Failed to start workflow");
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <div className="modal-title">Execute — {workflow.name}</div>
          <button className="btn btn-icon btn-ghost" onClick={onClose}><X size={16} /></button>
        </div>
        <div className="form-group">
          <label className="form-label">Input Task</label>
          <textarea className="form-textarea" style={{ minHeight: 80 }} value={task} onChange={e => setTask(e.target.value)} />
        </div>
        <div className="modal-footer">
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn btn-success" onClick={run} disabled={running}>
            {running ? <span className="spinner" /> : <><Play size={13} /> Run Workflow</>}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function Workflows() {
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [createModal, setCreateModal] = useState(false);
  const [runModal, setRunModal] = useState(null);
  const navigate = useNavigate();

  const load = async () => {
    try {
      const r = await api.get("/workflows/");
      setWorkflows(r.data || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const del = async (id) => {
    if (!window.confirm("Delete this workflow?")) return;
    await api.delete(`/workflows/${id}`);
    toast.success("Deleted");
    load();
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="page-title">Workflows</div>
          <div className="page-subtitle">Create and execute multi-agent pipelines</div>
        </div>
        <button className="btn btn-primary" onClick={() => setCreateModal(true)}>
          <Plus size={14} /> New Workflow
        </button>
      </div>

      {loading ? (
        <div className="flex items-center gap-12" style={{ color: "var(--text-muted)", padding: "40px 0" }}>
          <span className="spinner" /> Loading...
        </div>
      ) : workflows.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">⚡</div>
          <div className="empty-state-title">No workflows yet</div>
          <p>Deploy a template or create a new workflow.</p>
          <div className="flex gap-12 mt-16" style={{ justifyContent: "center" }}>
            <button className="btn btn-primary" onClick={() => navigate("/templates")}>Use Template</button>
            <button className="btn btn-ghost" onClick={() => setCreateModal(true)}>Create Blank</button>
          </div>
        </div>
      ) : (
        <div className="card-grid card-grid-3">
          {workflows.map(wf => {
            const nodeCount = wf.graph?.nodes?.length || 0;
            return (
              <div key={wf.id} className="card">
                <div className="flex items-center gap-12 mb-12">
                  <div style={{ width: 38, height: 38, borderRadius: 8, background: "rgba(99,102,241,0.12)", border: "1px solid rgba(99,102,241,0.3)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <GitBranch size={18} color="#6366f1" />
                  </div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 14 }}>{wf.name}</div>
                    {wf.template && <div style={{ fontSize: 11, color: "var(--text-muted)" }}>from: {wf.template}</div>}
                  </div>
                </div>

                {wf.description && (
                  <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 14 }}>{wf.description}</div>
                )}

                <div className="flex gap-8 mb-16">
                  <span className="tag">{nodeCount} nodes</span>
                  <span className="tag">ID #{wf.id}</span>
                </div>

                <div className="divider" />

                <div className="flex gap-8">
                  <button className="btn btn-success btn-sm" onClick={() => setRunModal(wf)}>
                    <Play size={12} /> Execute
                  </button>
                  <button className="btn btn-ghost btn-sm" onClick={() => navigate(`/builder/${wf.id}`)}>
                    <GitBranch size={12} /> Edit Graph
                  </button>
                  <button className="btn btn-danger btn-sm" onClick={() => del(wf.id)}>
                    <Trash2 size={12} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {createModal && (
        <CreateWorkflowModal
          onClose={() => setCreateModal(false)}
          onCreated={() => { setCreateModal(false); load(); }}
        />
      )}

      {runModal && <RunModal workflow={runModal} onClose={() => setRunModal(null)} />}
    </div>
  );
}