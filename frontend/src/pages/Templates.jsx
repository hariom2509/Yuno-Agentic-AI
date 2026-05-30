import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Zap } from "lucide-react";
import toast from "react-hot-toast";
import api from "../services/api";

const TEMPLATE_ICONS = {
  research_workflow: "🔬",
  customer_support_workflow: "💬",
};

export default function Templates() {
  const [templates, setTemplates] = useState([]);
  const [deploying, setDeploying] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    api.get("/templates/").then(r => setTemplates(r.data || [])).catch(() => {});
  }, []);

  const deploy = async (id) => {
    setDeploying(id);
    try {
      const r = await api.post(`/templates/${id}/deploy`);
      toast.success(`Workflow created! ID #${r.data.workflow_id}`);
      navigate(`/builder/${r.data.workflow_id}`);
    } catch {
      toast.error("Deployment failed");
    } finally {
      setDeploying(null);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="page-title">Templates</div>
          <div className="page-subtitle">Pre-built workflows to get started instantly</div>
        </div>
      </div>

      <div className="card-grid card-grid-2" style={{ gap: 20 }}>
        {templates.map(tpl => (
          <div key={tpl.id} className="card" style={{ borderColor: "var(--border-bright)" }}>
            <div className="flex items-center gap-16 mb-16">
              <div style={{ fontSize: 40 }}>{TEMPLATE_ICONS[tpl.id] || "🤖"}</div>
              <div>
                <div style={{ fontWeight: 700, fontSize: 16 }}>{tpl.name}</div>
                <span className="tag" style={{ marginTop: 6 }}>{tpl.node_count} nodes</span>
              </div>
            </div>
            <div style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 20, lineHeight: 1.6 }}>
              {tpl.description}
            </div>
            <button
              className="btn btn-primary w-full"
              onClick={() => deploy(tpl.id)}
              disabled={deploying === tpl.id}
            >
              {deploying === tpl.id ? <span className="spinner" /> : <><Zap size={14} /> Deploy Template</>}
            </button>
          </div>
        ))}
      </div>

      <div className="card mt-24" style={{ background: "linear-gradient(135deg, rgba(99,102,241,0.1), rgba(168,85,247,0.05))", borderColor: "rgba(99,102,241,0.3)" }}>
        <div style={{ fontWeight: 600, marginBottom: 8 }}>Adding Custom Templates</div>
        <div style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.7 }}>
          Templates are defined in <code style={{ fontFamily: "JetBrains Mono, monospace", background: "var(--bg-elevated)", padding: "1px 5px", borderRadius: 3 }}>backend/app/routes/template_routes.py</code>.
          Each template is a dict with a <code style={{ fontFamily: "JetBrains Mono, monospace", background: "var(--bg-elevated)", padding: "1px 5px", borderRadius: 3 }}>graph</code> definition (nodes + edges)
          that maps directly to the ReactFlow canvas format.
        </div>
      </div>
    </div>
  );
}
