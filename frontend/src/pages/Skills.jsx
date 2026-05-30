import React, { useEffect, useState } from "react";
import { Plus, Pencil, Trash2, X, Wrench } from "lucide-react";
import toast from "react-hot-toast";
import api from "../services/api";

const DEFAULT_FORM = {
  name: "",
  description: "",
  code: "def execute(payload):\n    # Custom logic here\n    # Make sure to assign to 'result' local variable\n    result = f\"Processed: {payload}\"\n",
};

function SkillModal({ skill, onClose, onSaved }) {
  const [form, setForm] = useState(skill ? { ...DEFAULT_FORM, ...skill } : { ...DEFAULT_FORM });
  const [saving, setSaving] = useState(false);

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.code) {
      toast.error("Name and code are required.");
      return;
    }
    
    // Ensure the user doesn't use names that conflict with default tools
    const reserved = ["web_search", "calculator", "report_generator", "file_reader"];
    if (reserved.includes(form.name.toLowerCase())) {
        toast.error(`The name '${form.name}' is reserved for a built-in tool.`);
        return;
    }

    setSaving(true);
    try {
      if (skill?.id) {
        await api.put(`/skills/${skill.id}`, form);
        toast.success("Skill updated");
      } else {
        await api.post("/skills/", form);
        toast.success("Skill created");
      }
      onSaved();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to save skill");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal modal-wide">
        <div className="modal-header">
          <div className="modal-title">{skill?.id ? "Edit Skill" : "Create Skill"}</div>
          <button className="btn btn-icon btn-ghost" onClick={onClose}><X size={16} /></button>
        </div>

        <form onSubmit={submit}>
          <div className="form-group">
            <label className="form-label">Skill/Tool Name *</label>
            <input className="form-input" value={form.name} onChange={e => set("name", e.target.value)} placeholder="get_crypto_price" />
            <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4 }}>This will be used by agents to invoke this tool. Use underscores, no spaces.</div>
          </div>
          
          <div className="form-group">
            <label className="form-label">Description</label>
            <textarea className="form-textarea" value={form.description} onChange={e => set("description", e.target.value)} placeholder="What does this skill do?" />
          </div>

          <div className="form-group">
            <label className="form-label">Python Execution Code *</label>
            <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 8 }}>
                Write pure python code. The input to the tool is injected as <code>payload</code>. You must assign your final output to a variable named <code>result</code>.
            </div>
            <textarea
              className="form-textarea"
              style={{ minHeight: 250, fontFamily: "monospace", fontSize: 13, background: "var(--bg)", color: "var(--accent)" }}
              value={form.code}
              onChange={e => set("code", e.target.value)}
              spellCheck="false"
            />
          </div>

          <div className="modal-footer" style={{ marginTop: 32 }}>
            <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? <span className="spinner" /> : (skill?.id ? "Update Skill" : "Create Skill")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function Skills() {
  const [skills, setSkills] = useState([]);
  const [modal, setModal] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const r = await api.get("/skills/");
      setSkills(r.data || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const deleteSkill = async (id) => {
    if (!window.confirm("Delete this skill?")) return;
    await api.delete(`/skills/${id}`);
    toast.success("Skill deleted");
    load();
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="page-title">Skills Registry</div>
          <div className="page-subtitle">Build custom python tools and integrations for your agents</div>
        </div>
        <button className="btn btn-primary" onClick={() => setModal("create")}>
          <Plus size={14} /> New Skill
        </button>
      </div>

      {loading ? (
        <div className="flex items-center gap-12" style={{ color: "var(--text-muted)", padding: "40px 0" }}>
          <span className="spinner" /> Loading skills...
        </div>
      ) : skills.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🔧</div>
          <div className="empty-state-title">No custom skills</div>
          <p>Create your first custom skill to expand your agent's capabilities.</p>
          <button className="btn btn-primary mt-16" onClick={() => setModal("create")}>
            <Plus size={14} /> Create Skill
          </button>
        </div>
      ) : (
        <div className="card-grid card-grid-3">
          {skills.map(skill => (
            <div key={skill.id} className="card" style={{ position: "relative" }}>
              <div className="flex items-center gap-12 mb-16">
                <div style={{ width: 42, height: 42, borderRadius: "50%", background: "rgba(168,85,247,0.1)", border: "2px solid #a855f7", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20, flexShrink: 0 }}><Wrench size={18} color="#a855f7" /></div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 700, fontSize: 14, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{skill.name}</div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>Custom Tool</div>
                </div>
              </div>

              <div style={{ fontSize: 12, color: "var(--text-secondary)", marginBottom: 14, display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                {skill.description || "No description provided."}
              </div>

              <div className="divider" />

              <div className="flex gap-8">
                <button className="btn btn-ghost btn-sm" onClick={() => setModal(skill)}>
                  <Pencil size={12} /> Edit
                </button>
                <button className="btn btn-danger btn-sm" onClick={() => deleteSkill(skill.id)}>
                  <Trash2 size={12} /> Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {modal && (
        <SkillModal
          skill={modal === "create" ? null : modal}
          onClose={() => setModal(null)}
          onSaved={() => { setModal(null); load(); }}
        />
      )}
    </div>
  );
}
