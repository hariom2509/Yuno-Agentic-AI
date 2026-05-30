import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Bot, GitBranch, Activity, DollarSign, Zap, ArrowRight } from "lucide-react";
import api from "../services/api";

function StatCard({ icon, label, value, color }) {
  return (
    <div className="stat-card">
      <div className="stat-icon" style={{ background: color + "22", color }}>
        {icon}
      </div>
      <div>
        <div className="stat-value">{value}</div>
        <div className="stat-label">{label}</div>
      </div>
    </div>
  );
}

function StatusBadge({ status }) {
  return <span className={`badge badge-${status}`}><span className="badge-dot" />{status}</span>;
}

export default function Dashboard() {
  const [stats, setStats] = useState({ total_executions: 0, completed: 0, failed: 0, total_tokens: 0, total_cost_usd: 0 });
  const [agents, setAgents] = useState([]);
  const [executions, setExecutions] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([
      api.get("/monitoring/stats").catch(() => ({ data: {} })),
      api.get("/agents/").catch(() => ({ data: [] })),
      api.get("/executions/").catch(() => ({ data: [] })),
    ]).then(([s, a, e]) => {
      setStats(s.data || {});
      setAgents(a.data || []);
      setExecutions((e.data || []).slice(0, 5));
    });
  }, []);

  return (
    <div>
      <div className="page-header" style={{
      background: "linear-gradient(135deg, var(--accent) 0%, var(--purple) 100%)",
      margin: "-32px -36px 32px -36px",
      padding: "40px 36px",
      color: "white",
      borderRadius: "0 0 16px 16px",
      boxShadow: "0 10px 30px rgba(99, 102, 241, 0.15)",
      position: "relative",
      overflow: "hidden"
    }}>
      <div style={{ position: "relative", zIndex: 1 }}>
        <h1 className="page-title" style={{ fontSize: 32, marginBottom: 8, color: "white" }}>Yuno Platform Overview</h1>
        <p className="page-subtitle" style={{ color: "rgba(255,255,255,0.8)", fontSize: 15 }}>
          Orchestrating autonomous agents and dynamic workflows
        </p>
      </div>
      {/* Decorative elements */}
      <div style={{
        position: "absolute", top: -50, right: -50, width: 200, height: 200,
        background: "rgba(255,255,255,0.1)", borderRadius: "50%", filter: "blur(20px)"
      }} />
    </div>

      {/* Stats */}
      <div className="card-grid card-grid-4 mb-16">
        <StatCard icon={<Bot size={18} />} label="Total Agents" value={agents.length} color="#6366f1" />
        <StatCard icon={<GitBranch size={18} />} label="Executions" value={stats.total_executions || 0} color="#22c55e" />
        <StatCard icon={<Activity size={18} />} label="Total Tokens" value={(stats.total_tokens || 0).toLocaleString()} color="#3b82f6" />
        <StatCard icon={<DollarSign size={18} />} label="Total Cost" value={`$${(stats.total_cost_usd || 0).toFixed(4)}`} color="#f59e0b" />
      </div>

      <div className="card-grid card-grid-2 mt-24" style={{ gap: 20 }}>
        {/* Active Agents */}
        <div className="card">
          <div className="flex items-center justify-between mb-16">
            <div style={{ fontWeight: 600, fontSize: 14 }}>Active Agents</div>
            <button className="btn btn-ghost btn-sm" onClick={() => navigate("/agents")}>
              View all <ArrowRight size={12} />
            </button>
          </div>
          {agents.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">🤖</div>
              <div className="empty-state-title">No agents yet</div>
              <p>Create your first agent to get started.</p>
            </div>
          ) : (
            agents.slice(0, 5).map(agent => (
              <div key={agent.id} className="flex items-center justify-between" style={{ padding: "10px 0", borderBottom: "1px solid var(--border)" }}>
                <div className="flex items-center gap-12">
                  <div style={{ width: 36, height: 36, borderRadius: "50%", background: "var(--accent-glow)", border: "1px solid var(--accent)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16 }}>🤖</div>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 13 }}>{agent.name}</div>
                    <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{agent.role} · {agent.model}</div>
                  </div>
                </div>
                <div className="flex gap-8">
                  {agent.channel !== "none" && <span className="tag">{agent.channel}</span>}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Recent Executions */}
        <div className="card">
          <div className="flex items-center justify-between mb-16">
            <div style={{ fontWeight: 600, fontSize: 14 }}>Recent Executions</div>
            <button className="btn btn-ghost btn-sm" onClick={() => navigate("/monitoring")}>
              View all <ArrowRight size={12} />
            </button>
          </div>
          {executions.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">⚡</div>
              <div className="empty-state-title">No executions yet</div>
              <p>Run a workflow to see results here.</p>
            </div>
          ) : (
            executions.map(ex => (
              <div key={ex.id} className="flex items-center justify-between" style={{ padding: "10px 0", borderBottom: "1px solid var(--border)" }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 13 }}>Execution #{ex.id}</div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
                    {ex.input_task ? ex.input_task.slice(0, 45) + "..." : "No task"}
                  </div>
                </div>
                <div className="flex flex-col items-center gap-8" style={{ alignItems: "flex-end" }}>
                  <StatusBadge status={ex.status} />
                  <span style={{ fontSize: 10, color: "var(--text-muted)" }}>{ex.tokens_used || 0} tokens</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Quick actions */}
      <div className="mt-24">
        <div style={{ fontWeight: 600, marginBottom: 14, fontSize: 14 }}>Quick Actions</div>
        <div className="flex gap-12">
          <button className="btn btn-ghost" onClick={() => navigate("/templates")}>
            <Zap size={14} /> Deploy Template
          </button>
          <button className="btn btn-ghost" onClick={() => navigate("/builder")}>
            <GitBranch size={14} /> Open Builder
          </button>
          <button className="btn btn-ghost" onClick={() => navigate("/monitoring")}>
            <Activity size={14} /> Live Monitoring
          </button>
        </div>
      </div>
    </div>
  );
}