import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { RefreshCw, ChevronDown, ChevronRight } from "lucide-react";
import toast from "react-hot-toast";
import api from "../services/api";

const getWSUrl = () => {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const hostname = window.location.hostname;
  return `${protocol}//${hostname}:8001/ws/executions`;
};

const WS_URL = getWSUrl();

function StatusBadge({ status }) {
  return (
    <span className={`badge badge-${status || "pending"}`}>
      {(status === "running") && <span className="badge-dot" />}
      {status || "pending"}
    </span>
  );
}

function MessageItem({ msg }) {
  const colors = {
    human: "#6366f1",
    agent: "#22c55e",
    tool: "#a855f7",
    system: "#64748b",
  };
  const color = colors[msg.message_type] || "#94a3b8";
  const initial = (msg.sender || "?")[0].toUpperCase();
  const time = msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString() : "";

  return (
    <div className="message-item">
      <div className="message-avatar" style={{ background: color + "22", color, border: `1px solid ${color}44` }}>
        {initial}
      </div>
      <div className="message-body">
        <div className="message-meta">
          <span className="message-from">{msg.sender}</span>
          <span className="message-arrow">→</span>
          <span className="message-to">{msg.receiver}</span>
          <span className="message-time">{time}</span>
        </div>
        <div className="message-content">{msg.content?.slice(0, 600)}{msg.content?.length > 600 ? "..." : ""}</div>
      </div>
    </div>
  );
}

function ExecutionRow({ execution, isExpanded, onToggle }) {
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    if (isExpanded) {
      api.get(`/monitoring/executions/${execution.id}/messages`)
        .then(r => setMessages(r.data || []))
        .catch(() => {});
    }
  }, [isExpanded, execution.id]);

  const duration = execution.started_at && execution.completed_at
    ? ((new Date(execution.completed_at) - new Date(execution.started_at)) / 1000).toFixed(1) + "s"
    : execution.status === "running" ? "running..." : "—";

  return (
    <>
      <tr
        style={{ cursor: "pointer" }}
        onClick={onToggle}
      >
        <td>
          <div className="flex items-center gap-8">
            {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            <span style={{ fontWeight: 600 }}>#{execution.id}</span>
          </div>
        </td>
        <td style={{ maxWidth: 240, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {execution.input_task || "—"}
        </td>
        <td><StatusBadge status={execution.status} /></td>
        <td style={{ color: "var(--text-muted)", fontSize: 12 }}>{execution.current_node}</td>
        <td style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 12 }}>{execution.tokens_used || 0}</td>
        <td style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 12 }}>${(execution.cost_usd || 0).toFixed(4)}</td>
        <td style={{ color: "var(--text-muted)", fontSize: 12 }}>{duration}</td>
      </tr>
      {isExpanded && (
        <tr>
          <td colSpan={7} style={{ background: "var(--bg-elevated)", padding: 20 }}>
            {execution.final_output && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", marginBottom: 8, textTransform: "uppercase", letterSpacing: 1 }}>Final Output</div>
                <div className="code-block">{execution.final_output}</div>
              </div>
            )}
            <div>
              <div style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", marginBottom: 12, textTransform: "uppercase", letterSpacing: 1 }}>
                Message Timeline ({messages.length})
              </div>
              <div className="message-timeline">
                {messages.length === 0
                  ? <div style={{ color: "var(--text-muted)", fontSize: 13 }}>No messages recorded.</div>
                  : messages.map(m => <MessageItem key={m.id} msg={m} />)
                }
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

export default function Monitoring() {
  const [executions, setExecutions] = useState([]);
  const [stats, setStats] = useState({});
  const [expanded, setExpanded] = useState(null);
  const [wsStatus, setWsStatus] = useState("connecting");
  const [liveEvents, setLiveEvents] = useState([]);
  const wsRef = useRef(null);
  const navigate = useNavigate();

  const load = async () => {
    const [e, s] = await Promise.all([
      api.get("/monitoring/executions").catch(() => ({ data: [] })),
      api.get("/monitoring/stats").catch(() => ({ data: {} })),
    ]);
    setExecutions(e.data || []);
    setStats(s.data || {});
  };

  useEffect(() => {
    load();

    // WebSocket connection
    const connect = () => {
      try {
        const ws = new WebSocket(WS_URL);
        wsRef.current = ws;

        ws.onopen = () => setWsStatus("live");
        ws.onclose = () => {
          setWsStatus("disconnected");
          setTimeout(connect, 3000); // reconnect
        };
        ws.onerror = () => setWsStatus("disconnected");

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            setLiveEvents(prev => [data, ...prev].slice(0, 30));
            
            if (data.type === "execution_update") {
              load(); // refresh lists
              if (data.status === "completed") {
                toast.success(`Workflow #${data.execution_id} completed successfully!`, { duration: 5000 });
              } else if (data.status === "failed") {
                toast.error(`Workflow #${data.execution_id} failed.`, { duration: 5000 });
              }
            } else if (data.type === "message") {
              if (data.message_type === "agent") {
                toast.success(`${data.sender} ➔ ${data.receiver}: ${data.content.slice(0, 50)}...`, {
                  icon: "🤖",
                  duration: 3000,
                });
              } else if (data.message_type === "tool") {
                toast.success(`${data.sender} ➔ ${data.receiver} (Tool run)`, {
                  icon: "🔧",
                  duration: 3000,
                });
              } else if (data.message_type === "system") {
                toast.loading(data.content, { duration: 1500 });
              }
            }
          } catch {}
        };
      } catch {
        setWsStatus("disconnected");
      }
    };

    connect();
    return () => wsRef.current?.close();
  }, []);

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="page-title">Monitoring</div>
          <div className="page-subtitle">Live execution tracking and message history</div>
        </div>
        <div className="flex gap-12 items-center">
          <span className={`live-dot ${wsStatus !== "live" ? "disconnected" : ""}`} style={{ color: wsStatus === "live" ? "var(--green)" : "var(--text-muted)" }}>
            {wsStatus === "live" ? "LIVE" : wsStatus.toUpperCase()}
          </span>
          <button className="btn btn-ghost btn-sm" onClick={load}><RefreshCw size={13} /> Refresh</button>
        </div>
      </div>

      {/* Stats row */}
      <div className="card-grid card-grid-4 mb-16">
        {[
          { label: "Total", value: stats.total_executions || 0 },
          { label: "Completed", value: stats.completed || 0, color: "var(--green)" },
          { label: "Failed", value: stats.failed || 0, color: "var(--red)" },
          { label: "Total Cost", value: `$${(stats.total_cost_usd || 0).toFixed(4)}`, color: "var(--yellow)" },
        ].map(s => (
          <div key={s.label} className="card" style={{ padding: "14px 20px" }}>
            <div style={{ fontSize: 22, fontWeight: 700, color: s.color || "var(--text-primary)" }}>{s.value}</div>
            <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>{s.label}</div>
          </div>
        ))}
      </div>

      <div className="card-grid card-grid-2" style={{ gap: 20 }}>
        {/* Execution table */}
        <div className="card" style={{ gridColumn: "1 / -1" }}>
          <div style={{ fontWeight: 600, marginBottom: 16 }}>Executions</div>
          {executions.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📊</div>
              <div className="empty-state-title">No executions yet</div>
              <p>Run a workflow to see activity here.</p>
              <button className="btn btn-primary mt-16" onClick={() => navigate("/workflows")}>Go to Workflows</button>
            </div>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table className="table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Task</th>
                    <th>Status</th>
                    <th>Current Node</th>
                    <th>Tokens</th>
                    <th>Cost</th>
                    <th>Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {executions.map(ex => (
                    <ExecutionRow
                      key={ex.id}
                      execution={ex}
                      isExpanded={expanded === ex.id}
                      onToggle={() => setExpanded(expanded === ex.id ? null : ex.id)}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Live event feed */}
        <div className="card" style={{ gridColumn: "1 / -1" }}>
          <div className="flex items-center justify-between mb-12">
            <div style={{ fontWeight: 600, fontSize: 14 }}>Live Event Feed</div>
            {wsStatus === "live" && <span className="live-dot">LIVE</span>}
          </div>
          {liveEvents.length === 0 ? (
            <div style={{ color: "var(--text-muted)", fontSize: 13, padding: "20px 0" }}>
              Waiting for events... Start a workflow execution to see live updates here.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {liveEvents.map((ev, i) => (
                <div key={i} style={{ display: "flex", gap: 10, fontSize: 12, padding: "6px 10px", background: "var(--bg-elevated)", borderRadius: 6, borderLeft: "3px solid var(--accent)" }}>
                  <span style={{ color: "var(--text-muted)", fontFamily: "JetBrains Mono, monospace" }}>{ev.type}</span>
                  <span style={{ color: "var(--text-secondary)" }}>
                    {ev.sender && `${ev.sender} → ${ev.receiver}: `}
                    {ev.content || ev.status || JSON.stringify(ev).slice(0, 80)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}