import React, { useEffect, useState } from "react";
import {
  ShieldCheck,
  Server,
  Sliders,
  RefreshCw,
  Lock,
  CheckCircle2,
  AlertTriangle,
  Info,
  Check,
  X,
  ExternalLink,
} from "lucide-react";
import toast from "react-hot-toast";
import api from "../services/api";

const EXPOSURE_TIERS = [
  { id: "BUILDER_VISIBLE", label: "Builder Visible", color: "#a855f7", desc: "Selectable by users in workflow builder" },
  { id: "AGENT_ASSIGNABLE", label: "Agent Assignable", color: "#6366f1", desc: "Assigned by Admin to autonomous agents" },
  { id: "PLATFORM_INTERNAL", label: "Platform Internal", color: "#64748b", desc: "Internal platform policies & hooks" },
];

const RISK_LEVELS = [
  { id: "LOW", label: "LOW", color: "#22c55e", bg: "rgba(34, 197, 94, 0.15)" },
  { id: "MEDIUM", label: "MEDIUM", color: "#3b82f6", bg: "rgba(59, 130, 246, 0.15)" },
  { id: "HIGH", label: "HIGH", color: "#f59e0b", bg: "rgba(245, 158, 11, 0.15)" },
  { id: "CRITICAL", label: "CRITICAL", color: "#ef4444", bg: "rgba(239, 68, 68, 0.15)" },
];

export default function Admin() {
  const [activeTab, setActiveTab] = useState("tools");
  const [loading, setLoading] = useState(true);
  const [servers, setServers] = useState([]);
  const [tools, setTools] = useState([]);
  const [agents, setAgents] = useState([]);

  // Agent Permissions Tab state
  const [selectedAgentId, setSelectedAgentId] = useState("");
  const [agentAssignedToolIds, setAgentAssignedToolIds] = useState([]);
  const [savingPermissions, setSavingPermissions] = useState(false);

  // Tool Edit Modal
  const [editingTool, setEditingTool] = useState(null);
  const [toolUpdateLoading, setToolUpdateLoading] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [serversRes, toolsRes, agentsRes] = await Promise.all([
        api.get("/api/mcp-servers"),
        api.get("/api/mcp-servers/tools/manage"),
        api.get("/agents/"),
      ]);
      setServers(serversRes.data || []);
      setTools(toolsRes.data || []);
      const agList = agentsRes.data || [];
      setAgents(agList);
      if (agList.length > 0 && !selectedAgentId) {
        setSelectedAgentId(agList[0].id.toString());
      }
    } catch (err) {
      console.error("Failed to load admin data", err);
      toast.error("Failed to load administrative governance data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // When selectedAgentId changes, fetch their authorized tools
  useEffect(() => {
    if (!selectedAgentId) return;
    api
      .get(`/agents/${selectedAgentId}/mcp-tools`)
      .then((res) => {
        const assignedIds = (res.data || []).map((t) => t.id);
        setAgentAssignedToolIds(assignedIds);
      })
      .catch((err) => {
        console.error("Failed to load agent permissions", err);
      });
  }, [selectedAgentId]);

  const handleSavePermissions = async () => {
    if (!selectedAgentId) return;
    setSavingPermissions(true);
    try {
      await api.post(`/agents/${selectedAgentId}/mcp-tools`, {
        mcp_tool_ids: agentAssignedToolIds,
      });
      toast.success("Agent MCP Tool permissions updated successfully!");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to update permissions.");
    } finally {
      setSavingPermissions(false);
    }
  };

  const toggleToolAssignment = (toolId) => {
    setAgentAssignedToolIds((prev) =>
      prev.includes(toolId) ? prev.filter((id) => id !== toolId) : [...prev, toolId]
    );
  };

  const handleUpdateTool = async (toolId, updates) => {
    setToolUpdateLoading(true);
    try {
      await api.put(`/api/mcp-servers/tools/${toolId}`, updates);
      toast.success("Tool configuration saved!");
      setTools((prev) =>
        prev.map((t) => (t.id === toolId ? { ...t, ...updates } : t))
      );
      if (editingTool && editingTool.id === toolId) {
        setEditingTool(null);
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to update tool configuration.");
    } finally {
      setToolUpdateLoading(false);
    }
  };

  const handleSeedServers = async () => {
    const toastId = toast.loading("Seeding and discovering MCP capability servers...");
    try {
      await api.post("/api/mcp-servers/seed-all");
      toast.success("All MCP Capability Servers seeded and classified!", { id: toastId });
      loadData();
    } catch (err) {
      toast.error("Failed to seed servers.", { id: toastId });
    }
  };

  const handleRefreshServer = async (serverId) => {
    const toastId = toast.loading("Discovering tools via JSON-RPC 2.0 stdio...");
    try {
      await api.post(`/api/mcp-servers/${serverId}/refresh-tools`);
      toast.success("Server tools refreshed successfully!", { id: toastId });
      loadData();
    } catch (err) {
      toast.error("Discovery failed for server.", { id: toastId });
    }
  };

  // Stat metrics
  const totalTools = tools.length;
  const builderTools = tools.filter((t) => t.exposure === "BUILDER_VISIBLE").length;
  const agentTools = tools.filter((t) => t.exposure === "AGENT_ASSIGNABLE").length;
  const hitlTools = tools.filter((t) => t.requires_approval).length;

  const currentAgent = agents.find((a) => a.id.toString() === selectedAgentId);
  const assignableTools = tools.filter((t) => t.exposure === "AGENT_ASSIGNABLE");

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto", paddingBottom: 60 }}>
      {/* Page Header */}
      <div className="page-header" style={{ marginBottom: 24 }}>
        <div>
          <div className="flex items-center gap-12">
            <div
              style={{
                width: 36,
                height: 36,
                borderRadius: "var(--radius-sm)",
                background: "var(--accent-glow)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "var(--accent)",
              }}
            >
              <ShieldCheck size={22} />
            </div>
            <div>
              <div className="page-title">Admin & Security Governance</div>
              <div className="page-subtitle">
                3-Tier Capability Exposure, MCP Tools Configuration, and Agent ACL Junction Permissions
              </div>
            </div>
          </div>
        </div>

        <div className="flex gap-12">
          <button className="btn btn-ghost btn-sm" onClick={loadData}>
            <RefreshCw size={14} /> Refresh
          </button>
          <button className="btn btn-primary btn-sm" onClick={handleSeedServers}>
            <Server size={14} /> Re-seed Capability Servers
          </button>
        </div>
      </div>

      {/* Security Stat Cards */}
      <div className="card-grid card-grid-4" style={{ marginBottom: 28 }}>
        <div className="stat-card" style={{ padding: "18px 22px" }}>
          <div className="stat-icon" style={{ background: "rgba(99, 102, 241, 0.15)", color: "var(--accent)" }}>
            <Sliders size={24} />
          </div>
          <div>
            <div className="stat-value" style={{ fontSize: 28 }}>{totalTools}</div>
            <div className="stat-label" style={{ fontSize: 11 }}>Registered Tools</div>
          </div>
        </div>

        <div className="stat-card" style={{ padding: "18px 22px" }}>
          <div className="stat-icon" style={{ background: "rgba(168, 85, 247, 0.15)", color: "#a855f7" }}>
            <Sliders size={24} />
          </div>
          <div>
            <div className="stat-value" style={{ fontSize: 28 }}>{builderTools}</div>
            <div className="stat-label" style={{ fontSize: 11 }}>Builder Visible</div>
          </div>
        </div>

        <div className="stat-card" style={{ padding: "18px 22px" }}>
          <div className="stat-icon" style={{ background: "rgba(34, 197, 94, 0.15)", color: "#22c55e" }}>
            <Lock size={24} />
          </div>
          <div>
            <div className="stat-value" style={{ fontSize: 28 }}>{agentTools}</div>
            <div className="stat-label" style={{ fontSize: 11 }}>Agent Assignable (ACL)</div>
          </div>
        </div>

        <div className="stat-card" style={{ padding: "18px 22px" }}>
          <div className="stat-icon" style={{ background: "rgba(239, 68, 68, 0.15)", color: "#ef4444" }}>
            <AlertTriangle size={24} />
          </div>
          <div>
            <div className="stat-value" style={{ fontSize: 28 }}>{hitlTools}</div>
            <div className="stat-label" style={{ fontSize: 11 }}>HITL Gated (Approval)</div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div
        style={{
          display: "flex",
          gap: 8,
          borderBottom: "1.5px solid var(--border)",
          paddingBottom: 2,
          marginBottom: 24,
        }}
      >
        <button
          onClick={() => setActiveTab("tools")}
          style={{
            padding: "8px 18px",
            fontSize: 14,
            fontWeight: 600,
            borderRadius: "6px 6px 0 0",
            background: activeTab === "tools" ? "var(--bg-elevated)" : "transparent",
            color: activeTab === "tools" ? "var(--accent)" : "var(--text-secondary)",
            borderBottom: activeTab === "tools" ? "2px solid var(--accent)" : "2px solid transparent",
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <Sliders size={15} /> 1. MCP Tools & 3-Tier Security
        </button>

        <button
          onClick={() => setActiveTab("permissions")}
          style={{
            padding: "8px 18px",
            fontSize: 14,
            fontWeight: 600,
            borderRadius: "6px 6px 0 0",
            background: activeTab === "permissions" ? "var(--bg-elevated)" : "transparent",
            color: activeTab === "permissions" ? "var(--accent)" : "var(--text-secondary)",
            borderBottom: activeTab === "permissions" ? "2px solid var(--accent)" : "2px solid transparent",
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <Lock size={15} /> 2. Agent Tool Permissions (ACL)
        </button>

        <button
          onClick={() => setActiveTab("servers")}
          style={{
            padding: "8px 18px",
            fontSize: 14,
            fontWeight: 600,
            borderRadius: "6px 6px 0 0",
            background: activeTab === "servers" ? "var(--bg-elevated)" : "transparent",
            color: activeTab === "servers" ? "var(--accent)" : "var(--text-secondary)",
            borderBottom: activeTab === "servers" ? "2px solid var(--accent)" : "2px solid transparent",
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <Server size={15} /> 3. MCP Servers & Transports
        </button>
      </div>

      {/* Loading state */}
      {loading ? (
        <div className="flex items-center gap-12" style={{ color: "var(--text-muted)", padding: "50px 0" }}>
          <span className="spinner" /> Loading administration state...
        </div>
      ) : (
        <>
          {/* TAB 1: MCP TOOLS CONFIGURATION */}
          {activeTab === "tools" && (
            <div className="card" style={{ padding: 24 }}>
              <div className="flex items-center justify-between mb-16">
                <div>
                  <h3 style={{ fontSize: 16, fontWeight: 700, color: "var(--text-primary)" }}>
                    MCP Tools Security Classification
                  </h3>
                  <div style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 4 }}>
                    Define capability exposure tier, risk classification, and Human-In-The-Loop approval gates.
                  </div>
                </div>
              </div>

              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                  <thead>
                    <tr style={{ borderBottom: "1.5px solid var(--border)", textAlign: "left" }}>
                      <th style={{ padding: "10px 14px", color: "var(--text-secondary)", fontWeight: 600 }}>Tool</th>
                      <th style={{ padding: "10px 14px", color: "var(--text-secondary)", fontWeight: 600 }}>Server</th>
                      <th style={{ padding: "10px 14px", color: "var(--text-secondary)", fontWeight: 600 }}>Exposure Tier</th>
                      <th style={{ padding: "10px 14px", color: "var(--text-secondary)", fontWeight: 600 }}>Risk Level</th>
                      <th style={{ padding: "10px 14px", color: "var(--text-secondary)", fontWeight: 600 }}>HITL Approval</th>
                      <th style={{ padding: "10px 14px", color: "var(--text-secondary)", fontWeight: 600 }}>Status</th>
                      <th style={{ padding: "10px 14px", color: "var(--text-secondary)", fontWeight: 600 }}>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tools.map((tool) => {
                      const tier = EXPOSURE_TIERS.find((t) => t.id === tool.exposure) || EXPOSURE_TIERS[0];
                      const risk = RISK_LEVELS.find((r) => r.id === tool.risk_level) || RISK_LEVELS[0];

                      return (
                        <tr
                          key={tool.id}
                          style={{
                            borderBottom: "1px solid var(--border)",
                            transition: "background 0.15s ease",
                          }}
                        >
                          <td style={{ padding: "12px 14px" }}>
                            <div style={{ fontWeight: 600, color: "var(--text-primary)" }}>{tool.name}</div>
                            <div
                              style={{
                                fontSize: 11,
                                color: "var(--text-muted)",
                                maxWidth: 280,
                                overflow: "hidden",
                                textOverflow: "ellipsis",
                                whiteSpace: "nowrap",
                              }}
                            >
                              {tool.description || "No description"}
                            </div>
                          </td>
                          <td style={{ padding: "12px 14px" }}>
                            <span
                              style={{
                                fontSize: 11,
                                padding: "2px 8px",
                                borderRadius: 4,
                                background: "var(--bg-elevated)",
                                border: "1px solid var(--border)",
                                fontFamily: "JetBrains Mono, monospace",
                              }}
                            >
                              {tool.server_name}
                            </span>
                          </td>
                          <td style={{ padding: "12px 14px" }}>
                            <span
                              style={{
                                fontSize: 11,
                                fontWeight: 600,
                                padding: "3px 8px",
                                borderRadius: 4,
                                background: `${tier.color}22`,
                                color: tier.color,
                                border: `1px solid ${tier.color}44`,
                              }}
                            >
                              {tier.label}
                            </span>
                          </td>
                          <td style={{ padding: "12px 14px" }}>
                            <span
                              style={{
                                fontSize: 11,
                                fontWeight: 700,
                                padding: "3px 8px",
                                borderRadius: 4,
                                background: risk.bg,
                                color: risk.color,
                                border: `1px solid ${risk.color}44`,
                              }}
                            >
                              {risk.label}
                            </span>
                          </td>
                          <td style={{ padding: "12px 14px" }}>
                            {tool.requires_approval ? (
                              <span
                                style={{
                                  fontSize: 11,
                                  fontWeight: 600,
                                  color: "#ef4444",
                                  display: "flex",
                                  alignItems: "center",
                                  gap: 4,
                                }}
                              >
                                <AlertTriangle size={13} /> Required
                              </span>
                            ) : (
                              <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Auto-Execute</span>
                            )}
                          </td>
                          <td style={{ padding: "12px 14px" }}>
                            <span
                              style={{
                                fontSize: 11,
                                color: tool.enabled ? "#22c55e" : "var(--text-muted)",
                                fontWeight: 600,
                              }}
                            >
                              {tool.enabled ? "● Enabled" : "○ Disabled"}
                            </span>
                          </td>
                          <td style={{ padding: "12px 14px" }}>
                            <button
                              className="btn btn-ghost btn-sm"
                              onClick={() => setEditingTool(tool)}
                              style={{ padding: "4px 10px", fontSize: 12 }}
                            >
                              Configure
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 2: AGENT TOOL PERMISSIONS (ACL) */}
          {activeTab === "permissions" && (
            <div className="card" style={{ padding: 24 }}>
              <div className="flex items-center justify-between mb-16">
                <div>
                  <h3 style={{ fontSize: 16, fontWeight: 700, color: "var(--text-primary)" }}>
                    Agent Capability Authorization (agent_mcp_tools ACL)
                  </h3>
                  <div style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 4 }}>
                    Explicitly authorize which external AGENT_ASSIGNABLE tools an agent may invoke at runtime.
                  </div>
                </div>

                <button
                  className="btn btn-primary"
                  onClick={handleSavePermissions}
                  disabled={savingPermissions || !selectedAgentId}
                >
                  <Check size={14} /> {savingPermissions ? "Saving..." : "Save Permissions"}
                </button>
              </div>

              {/* Agent Selector */}
              <div
                style={{
                  background: "var(--bg-elevated)",
                  borderRadius: "var(--radius-sm)",
                  padding: 16,
                  marginBottom: 24,
                  display: "flex",
                  alignItems: "center",
                  gap: 16,
                }}
              >
                <div style={{ flex: 1 }}>
                  <label className="form-label" style={{ marginBottom: 6 }}>
                    Select Target Agent
                  </label>
                  <select
                    className="form-select"
                    value={selectedAgentId}
                    onChange={(e) => setSelectedAgentId(e.target.value)}
                  >
                    {agents.map((ag) => (
                      <option key={ag.id} value={ag.id}>
                        {ag.name} ({ag.role}) — Model: {ag.model}
                      </option>
                    ))}
                  </select>
                </div>

                {currentAgent && (
                  <div
                    style={{
                      borderLeft: "1px solid var(--border)",
                      paddingLeft: 16,
                      fontSize: 12,
                      color: "var(--text-secondary)",
                      maxWidth: 400,
                    }}
                  >
                    <div style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                      Security Boundary for Agent #{currentAgent.id}
                    </div>
                    <div>{currentAgent.system_prompt?.slice(0, 100)}...</div>
                    <div style={{ marginTop: 4, color: "var(--accent)" }}>
                      Authorized Tools: {agentAssignedToolIds.length} / {assignableTools.length}
                    </div>
                  </div>
                )}
              </div>

              {/* Security info alert */}
              <div
                style={{
                  background: "rgba(99, 102, 241, 0.08)",
                  border: "1px solid rgba(99, 102, 241, 0.3)",
                  borderRadius: "var(--radius-sm)",
                  padding: 14,
                  marginBottom: 20,
                  fontSize: 12,
                  display: "flex",
                  gap: 10,
                  alignItems: "flex-start",
                }}
              >
                <Info size={16} color="var(--accent)" style={{ flexShrink: 0, marginTop: 2 }} />
                <div>
                  <strong>Least-Privilege Authorization Model:</strong> Newly created agents start with zero external tool permissions.
                  Checked tools below are registered in the <code>agent_mcp_tools</code> junction table. During workflow execution,
                  even if JIT scopes an external tool, <code>MCPAuthorizationService.verify_agent_tool_access()</code> will strictly reject
                  calls not granted here.
                </div>
              </div>

              {/* Tools Checklist */}
              <div className="card-grid card-grid-2" style={{ gap: 12 }}>
                {assignableTools.map((tool) => {
                  const isChecked = agentAssignedToolIds.includes(tool.id);
                  const isCritical = tool.risk_level === "CRITICAL" || tool.risk_level === "HIGH";

                  return (
                    <div
                      key={tool.id}
                      onClick={() => toggleToolAssignment(tool.id)}
                      style={{
                        padding: "14px 16px",
                        borderRadius: "var(--radius-sm)",
                        background: isChecked ? "var(--bg-elevated)" : "var(--bg-surface)",
                        border: isChecked ? "1.5px solid var(--accent)" : "1px solid var(--border)",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "flex-start",
                        gap: 12,
                        transition: "all 0.15s ease",
                        minWidth: 0,
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        readOnly
                        style={{ marginTop: 3, cursor: "pointer" }}
                      />
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div className="flex items-center justify-between">
                          <span style={{ fontWeight: 600, fontSize: 13, color: isChecked ? "var(--text-bright)" : "var(--text-primary)" }}>
                            {tool.name}
                          </span>
                          <span
                            style={{
                              fontSize: 10,
                              fontWeight: 700,
                              padding: "2px 6px",
                              borderRadius: 4,
                              background: isCritical ? "rgba(239, 68, 68, 0.15)" : "rgba(34, 197, 94, 0.15)",
                              color: isCritical ? "#ef4444" : "#22c55e",
                              border: `1px solid ${isCritical ? "rgba(239, 68, 68, 0.3)" : "rgba(34, 197, 94, 0.3)"}`,
                            }}
                          >
                            {tool.risk_level} {tool.requires_approval ? "· Approval Required" : ""}
                          </span>
                        </div>
                        <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4 }}>
                          {tool.description}
                        </div>
                        <div style={{ fontSize: 10, color: "var(--accent-dim)", marginTop: 4, fontFamily: "JetBrains Mono, monospace" }}>
                          server: {tool.server_name}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              <div style={{ marginTop: 20, display: "flex", justifyContent: "flex-end" }}>
                <button
                  className="btn btn-primary"
                  onClick={handleSavePermissions}
                  disabled={savingPermissions || !selectedAgentId}
                >
                  <Check size={14} /> {savingPermissions ? "Saving..." : "Save Permissions"}
                </button>
              </div>
            </div>
          )}

          {/* TAB 3: MCP SERVERS & TRANSPORTS */}
          {activeTab === "servers" && (
            <div className="card" style={{ padding: 24, overflow: "hidden" }}>
              <div className="flex items-center justify-between mb-16">
                <div>
                  <h3 style={{ fontSize: 16, fontWeight: 700, color: "var(--text-primary)" }}>
                    Registered MCP Servers & Capability Providers
                  </h3>
                  <div style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 4 }}>
                    Manage JSON-RPC 2.0 stdio and HTTP streamable capability servers.
                  </div>
                </div>
              </div>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
                  gap: 16,
                  width: "100%",
                }}
              >
                {servers.map((server) => (
                  <div
                    key={server.id}
                    style={{
                      background: "var(--bg-elevated)",
                      border: "1px solid var(--border)",
                      borderRadius: "var(--radius-sm)",
                      padding: 18,
                      display: "flex",
                      flexDirection: "column",
                      justifyContent: "space-between",
                      minWidth: 0,
                      overflow: "hidden",
                    }}
                  >
                    <div>
                      <div className="flex items-center justify-between mb-10">
                        <span
                          style={{
                            fontWeight: 700,
                            fontSize: 15,
                            color: "var(--text-primary)",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                          }}
                        >
                          {server.name}
                        </span>
                        <span
                          style={{
                            fontSize: 11,
                            padding: "2px 8px",
                            borderRadius: 4,
                            background: server.enabled ? "rgba(34, 197, 94, 0.15)" : "rgba(100, 116, 139, 0.15)",
                            color: server.enabled ? "#22c55e" : "#94a3b8",
                            fontWeight: 600,
                            flexShrink: 0,
                          }}
                        >
                          {server.enabled ? "● Enabled" : "○ Disabled"}
                        </span>
                      </div>

                      <p
                        style={{
                          fontSize: 12,
                          color: "var(--text-secondary)",
                          marginBottom: 12,
                          lineHeight: 1.4,
                          minHeight: 34,
                        }}
                      >
                        {server.description}
                      </p>

                      <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 8 }}>
                        <strong>Transport:</strong> <code style={{ color: "var(--accent)" }}>{server.transport}</code>
                      </div>

                      {server.command && (
                        <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 10 }}>
                          <strong style={{ display: "block", marginBottom: 4 }}>Command / Script:</strong>
                          <div
                            style={{
                              background: "rgba(0, 0, 0, 0.35)",
                              padding: "6px 10px",
                              borderRadius: 4,
                              fontFamily: "JetBrains Mono, monospace",
                              fontSize: 10,
                              wordBreak: "break-all",
                              whiteSpace: "pre-wrap",
                              lineHeight: 1.4,
                              maxHeight: 70,
                              overflowY: "auto",
                              color: "var(--text-primary)",
                              border: "1px solid rgba(255, 255, 255, 0.05)",
                            }}
                          >
                            {server.command} {server.args?.join(" ")}
                          </div>
                        </div>
                      )}

                      <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 16 }}>
                        <strong>Cached Tools:</strong> {server.tools?.length || 0} tools
                      </div>
                    </div>

                    <div className="flex gap-8">
                      <button
                        className="btn btn-ghost btn-sm w-full"
                        onClick={() => handleRefreshServer(server.id)}
                      >
                        <RefreshCw size={12} /> Rediscover Tools
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* Tool Policy Configuration Modal */}
      {editingTool && (
        <div
          className="modal-overlay"
          onClick={(e) => e.target === e.currentTarget && setEditingTool(null)}
        >
          <div className="modal" style={{ width: 500, fontSize: 14 }}>
            <div className="modal-header">
              <div className="modal-title">Configure Tool Policy: {editingTool.name}</div>
              <button className="btn btn-icon btn-ghost" onClick={() => setEditingTool(null)}>
                <X size={16} />
              </button>
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleUpdateTool(editingTool.id, {
                  exposure: editingTool.exposure,
                  risk_level: editingTool.risk_level,
                  requires_approval: editingTool.requires_approval,
                  enabled: editingTool.enabled,
                });
              }}
            >
              <div className="form-group mb-16">
                <label className="form-label">Exposure Tier</label>
                <select
                  className="form-select"
                  value={editingTool.exposure}
                  onChange={(e) => setEditingTool({ ...editingTool, exposure: e.target.value })}
                >
                  {EXPOSURE_TIERS.map((tier) => (
                    <option key={tier.id} value={tier.id}>
                      {tier.label} ({tier.desc})
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group mb-16">
                <label className="form-label">Risk Classification</label>
                <select
                  className="form-select"
                  value={editingTool.risk_level}
                  onChange={(e) => setEditingTool({ ...editingTool, risk_level: e.target.value })}
                >
                  {RISK_LEVELS.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group mb-16">
                <label className="toggle">
                  <input
                    type="checkbox"
                    checked={editingTool.requires_approval}
                    onChange={(e) =>
                      setEditingTool({ ...editingTool, requires_approval: e.target.checked })
                    }
                  />
                  <div className="toggle-track">
                    <div className="toggle-thumb" />
                  </div>
                  <span style={{ fontSize: 13 }}>Require Human-In-The-Loop (HITL) Approval</span>
                </label>
              </div>

              <div className="form-group mb-20">
                <label className="toggle">
                  <input
                    type="checkbox"
                    checked={editingTool.enabled}
                    onChange={(e) => setEditingTool({ ...editingTool, enabled: e.target.checked })}
                  />
                  <div className="toggle-track">
                    <div className="toggle-thumb" />
                  </div>
                  <span style={{ fontSize: 13 }}>Tool Enabled</span>
                </label>
              </div>

              <div className="flex gap-8 justify-end">
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={() => setEditingTool(null)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={toolUpdateLoading}>
                  {toolUpdateLoading ? "Saving..." : "Save Policy"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
