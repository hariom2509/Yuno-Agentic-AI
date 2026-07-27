import React, { useCallback, useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import ReactFlow, {
  addEdge,
  Background,
  Controls,
  MiniMap,
  useEdgesState,
  useNodesState,
  Panel,
  Handle,
  Position,
} from "reactflow";
import "reactflow/dist/style.css";
import { Save, Plus, Trash2, X, Settings2 } from "lucide-react";
import toast from "react-hot-toast";
import api from "../services/api";

function formatToolLabel(toolIdentifier) {
  if (!toolIdentifier) return "Web Search";
  if (toolIdentifier.includes("::")) {
    const raw = toolIdentifier.split("::").pop();
    return raw.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
  }
  return toolIdentifier.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
}

// Custom Node Components
function AgentNodeComponent({ data }) {
  const isTool = data.type === "tool";
  return (
    <div className={`agent-node ${isTool ? "tool-node" : ""}`} style={{ position: "relative" }}>
      {/* Target handle (input) on top */}
      <Handle type="target" position={Position.Top} style={{ background: isTool ? "var(--purple)" : "var(--accent)", width: 12, height: 12 }} />
      
      <div style={{ fontSize: 32, marginBottom: 8 }}>{isTool ? "🔧" : "🤖"}</div>
      <div className="agent-node-title">{data.label}</div>
      <div className="agent-node-role">{isTool ? `tool: ${formatToolLabel(data.tool)}` : data.model || "llama-3.3-70b-versatile"}</div>
      
      {/* Source handle (output) on bottom */}
      <Handle type="source" position={Position.Bottom} style={{ background: isTool ? "var(--purple)" : "var(--accent)", width: 12, height: 12 }} />
    </div>
  );
}

const nodeTypes = { agentNode: AgentNodeComponent };

const NODE_PALETTE = [
  { type: "agent", label: "Agent Node", icon: "🤖", desc: "AI agent powered by LLM" },
  { type: "tool", label: "Tool Node", icon: "🔧", desc: "Execute a tool (search, calc, report, MCP)" },
];

function NodeConfigPanel({ node, availableTools, capabilityGroups, onUpdate, onClose }) {
  const [data, setData] = useState(node.data);

  const set = (k, v) => setData(d => ({ ...d, [k]: v }));
  const setGuardrail = (k, v) => setData(d => ({ 
    ...d, 
    guardrails: { ...(d.guardrails || {}), [k]: v } 
  }));

  return (
    <div style={{
      position: "absolute", right: 0, top: 0, bottom: 0, width: 420,
      background: "var(--bg-surface)", borderLeft: "1px solid var(--border-bright)",
      padding: 24, overflowY: "auto", zIndex: 10,
      boxShadow: "-12px 0 32px rgba(0, 0, 0, 0.4)",
    }}>
      <div className="flex items-center justify-between mb-16">
        <div style={{ fontWeight: 600 }}>Configure Node</div>
        <button className="btn btn-icon btn-ghost" onClick={() => { onUpdate(data); onClose(); }}><X size={16} /></button>
      </div>

      <div className="form-group">
        <label className="form-label">Label</label>
        <input className="form-input" value={data.label || ""} onChange={e => set("label", e.target.value)} />
      </div>
      <div className="form-group">
        <label className="form-label">Type</label>
        <select className="form-select" value={data.type || "agent"} onChange={e => set("type", e.target.value)}>
          <option value="agent">Agent</option>
          <option value="tool">Tool</option>
        </select>
      </div>

      {data.type !== "tool" && (
        <>
          <div className="form-group">
            <label className="form-label">System Prompt</label>
            <textarea className="form-textarea" value={data.system_prompt || ""} onChange={e => set("system_prompt", e.target.value)} placeholder="You are a..." />
          </div>
          <div className="flex gap-12 mb-16">
            <div className="w-full">
              <label className="form-label">Model</label>
              <select className="form-select" value={data.model || "gpt-3.5-turbo"} onChange={e => set("model", e.target.value)}>
                <option value="llama-3.1-8b-instant">Llama 3.1 8B</option>
                <option value="llama-3.3-70b-versatile">Llama 3.3 70B</option>
                <option value="gpt-3.5-turbo">gpt-3.5-turbo</option>
              </select>
            </div>
            <div className="w-full">
              <label className="form-label">Temp ({data.temperature || 0.7})</label>
              <input type="range" min="0" max="1" step="0.1" style={{width: "100%", marginTop: 8}} 
                value={data.temperature || 0.7} onChange={e => set("temperature", parseFloat(e.target.value))} />
            </div>
          </div>
          
          <label className="toggle mb-16">
            <input type="checkbox" checked={data.memory_enabled !== false} onChange={e => set("memory_enabled", e.target.checked)} />
            <div className="toggle-track"><div className="toggle-thumb" /></div>
            <span style={{fontSize: 13}}>Enable Memory</span>
          </label>

          <div style={{ marginTop: 24, marginBottom: 12, fontSize: 12, fontWeight: 600, color: "var(--text-secondary)", textTransform: "uppercase" }}>Guardrails</div>
          <div className="form-group">
            <label className="form-label">Blocked Topics (comma separated)</label>
            <input className="form-input" placeholder="e.g. politics, violence" 
              value={(data.guardrails?.blocked_topics || []).join(", ")} 
              onChange={e => setGuardrail("blocked_topics", e.target.value.split(",").map(s => s.trim()).filter(Boolean))} />
          </div>
          <label className="toggle mb-16">
            <input type="checkbox" checked={data.guardrails?.content_filter || false} onChange={e => setGuardrail("content_filter", e.target.checked)} />
            <div className="toggle-track"><div className="toggle-thumb" /></div>
            <span style={{fontSize: 13}}>Strict Content Filter</span>
          </label>
        </>
      )}

      {data.type === "tool" && (
        <div className="form-group">
          <label className="form-label">Tool</label>
          <select className="form-select" value={data.tool || "mcp::yuno-tools::web_search"} onChange={e => set("tool", e.target.value)}>
            {(capabilityGroups && capabilityGroups.length > 0) ? (
              capabilityGroups.map(group => (
                <optgroup key={group.id} label={group.name}>
                  {group.tools.map(tool => (
                    <option key={tool.canonical_name || tool.id} value={tool.canonical_name || tool.id}>
                      {tool.label}
                    </option>
                  ))}
                </optgroup>
              ))
            ) : (
              (availableTools || []).map(tool => {
                const val = typeof tool === "string" ? tool : (tool.id || tool.canonical_name);
                const lbl = typeof tool === "string" ? tool : (tool.label || tool.name || tool.id);
                return <option key={val} value={val}>{lbl}</option>;
              })
            )}
          </select>
        </div>
      )}

      <button className="btn btn-primary w-full mt-16" onClick={() => { onUpdate(data); onClose(); }}>
        Apply Changes
      </button>
    </div>
  );
}

function EdgeConfigPanel({ edge, onUpdate, onClose }) {
  const [condition, setCondition] = useState(edge.data?.condition || "");

  return (
    <div style={{
      position: "absolute", right: 0, top: 0, bottom: 0, width: 300,
      background: "var(--bg-surface)", borderLeft: "1px solid var(--border)",
      padding: 20, overflowY: "auto", zIndex: 10,
    }}>
      <div className="flex items-center justify-between mb-16">
        <div style={{ fontWeight: 600 }}>Configure Edge</div>
        <button className="btn btn-icon btn-ghost" onClick={onClose}><X size={16} /></button>
      </div>

      <div className="form-group">
        <label className="form-label">Routing Condition</label>
        <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 8 }}>
          If the output contains this text, follow this edge. Leave empty for default.
        </div>
        <input className="form-input" placeholder="e.g. approve, reject, fail" 
          value={condition} onChange={e => setCondition(e.target.value)} />
      </div>

      <button className="btn btn-primary w-full mt-16" onClick={() => {
        onUpdate({
          ...edge,
          data: { ...edge.data, condition },
          label: condition ? `if: ${condition}` : undefined,
          style: condition ? { stroke: "var(--yellow)", strokeWidth: 2 } : {}
        });
        onClose();
      }}>
        Apply Condition
      </button>
    </div>
  );
}

export default function Builder() {
  const { workflowId } = useParams();
  const navigate = useNavigate();

  const [workflow, setWorkflow] = useState(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const [selectedNode, setSelectedNode] = useState(null);
  const [selectedEdge, setSelectedEdge] = useState(null);
  const [saving, setSaving] = useState(false);
  const [availableTools, setAvailableTools] = useState(["mcp::yuno-tools::web_search", "mcp::yuno-tools::calculator", "mcp::yuno-tools::report_generator", "mcp::yuno-tools::file_reader"]);
  const [capabilityGroups, setCapabilityGroups] = useState([]);
  const [nodeCounter, setNodeCounter] = useState(1);

  useEffect(() => {
    // Fetch builder-visible tools from Capability API
    api.get("/capabilities/builder-tools").then(res => {
      const groups = res.data?.groups || [];
      setCapabilityGroups(groups);
      const toolList = [];
      groups.forEach(group => {
        (group.tools || []).forEach(t => {
          toolList.push(t.canonical_name || t.id);
        });
      });
      if (toolList.length > 0) {
        setAvailableTools(toolList);
      }
    }).catch(() => {
      setAvailableTools([
        "mcp::yuno-tools::web_search",
        "mcp::yuno-tools::calculator",
        "mcp::yuno-tools::report_generator",
        "mcp::yuno-tools::file_reader",
        "mcp::yuno-tools::analyze_text",
        "mcp::yuno-tools::calculate_metrics",
        "mcp::yuno-tools::format_report"
      ]);
    });

    if (!workflowId) return;
    api.get(`/workflows/${workflowId}`).then(r => {
      setWorkflow(r.data);
      const graph = r.data.graph || {};
      const safeNodes = (graph.nodes || []).map((n, idx) => ({
        ...n,
        type: n.type || "agentNode",
        position: n.position || { x: 120 + idx * 280, y: 180 },
        data: {
          label: n.data?.label || n.id || `Node ${idx + 1}`,
          type: n.type === "toolNode" || n.data?.type === "tool" || n.data?.tool ? "tool" : "agent",
          tool: n.data?.tool || "",
          model: n.data?.model || "llama-3.1-8b-instant",
          system_prompt: n.data?.prompt || n.data?.system_prompt || "",
          temperature: n.data?.temperature || 0.7,
          memory_enabled: n.data?.memory_enabled !== false,
          guardrails: n.data?.guardrails || {},
        }
      }));
      setNodes(safeNodes);
      setEdges(graph.edges || []);
    }).catch(() => toast.error("Failed to load workflow"));
  }, [workflowId]);

  const onConnect = useCallback((params) => setEdges(eds => addEdge({ ...params, animated: true, data: { condition: "" } }, eds)), [setEdges]);

  const addNode = (type) => {
    const id = `node_${Date.now()}`;
    const isAgent = type === "agent";
    const newNode = {
      id,
      type: "agentNode",
      position: { x: 100 + nodeCounter * 60, y: 150 + (nodeCounter % 3) * 80 },
      data: {
        label: isAgent ? `Agent ${nodeCounter}` : `Tool ${nodeCounter}`,
        type: isAgent ? "agent" : "tool",
        system_prompt: isAgent ? "You are a helpful AI agent." : "",
        model: "gpt-3.5-turbo",
        temperature: 0.7,
        memory_enabled: true,
        guardrails: {},
        tool: isAgent ? "" : "web_search",
      },
    };
    setNodes(ns => [...ns, newNode]);
    setNodeCounter(c => c + 1);
  };

  const updateNodeData = (nodeId, newData) => {
    setNodes(ns => ns.map(n => n.id === nodeId ? { ...n, data: newData } : n));
  };

  const updateEdgeData = (newEdge) => {
    setEdges(es => es.map(e => e.id === newEdge.id ? newEdge : e));
  };

  const deleteNode = (nodeId) => {
    setNodes(ns => ns.filter(n => n.id !== nodeId));
    setEdges(es => es.filter(e => e.source !== nodeId && e.target !== nodeId));
    setSelectedNode(null);
  };
  
  const deleteEdge = (edgeId) => {
    setEdges(es => es.filter(e => e.id !== edgeId));
    setSelectedEdge(null);
  };

  const save = async () => {
    setSaving(true);
    try {
      if (!workflowId) {
        const name = window.prompt("Enter a name for your new workflow:", "My Visual Workflow") || "My Visual Workflow";
        const res = await api.post("/workflows/", {
          name: name,
          description: "Created in Visual Builder",
          graph: { nodes, edges },
        });
        setWorkflow(res.data);
        navigate(`/builder/${res.data.id}`, { replace: true });
        toast.success(`Workflow '${res.data.name}' created and saved!`);
      } else {
        await api.put(`/workflows/${workflowId}`, {
          name: workflow?.name || "Untitled",
          description: workflow?.description || "",
          graph: { nodes, edges },
        });
        toast.success("Workflow graph saved!");
      }
    } catch {
      toast.error("Save failed");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ position: "relative", height: "calc(100vh - 64px)", display: "flex" }}>
      {/* Left palette */}
      <div style={{ width: 240, background: "var(--bg-surface)", borderRight: "1px solid var(--border-bright)", padding: 20, flexShrink: 0 }}>
        <div style={{ fontWeight: 700, marginBottom: 14, fontSize: 14, color: "var(--text-primary)" }}>Node Palette</div>
        {NODE_PALETTE.map(n => (
          <div
            key={n.type}
            className="card"
            style={{ marginBottom: 12, cursor: "grab", padding: "12px 14px", border: "1px solid var(--border-bright)" }}
            onClick={() => addNode(n.type)}
          >
            <div className="flex items-center gap-12">
              <span style={{ fontSize: 24 }}>{n.icon}</span>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)" }}>{n.label}</div>
                <div style={{ fontSize: 11, color: "var(--text-secondary)", marginTop: 2 }}>{n.desc}</div>
              </div>
            </div>
          </div>
        ))}

        <div className="divider" />

        {workflowId ? (
          <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>
            Editing: <strong style={{ color: "var(--text-primary)" }}>{workflow?.name}</strong>
          </div>
        ) : (
          <div style={{ fontSize: 12, color: "var(--accent)" }}>
            ✨ Draft canvas. Click <strong>Save Graph</strong> anytime to name and persist.
          </div>
        )}

        <button
          className="btn btn-ghost btn-sm w-full mt-16"
          style={{ fontSize: 12 }}
          onClick={() => navigate("/workflows")}
        >
          ← Back to Workflows
        </button>
      </div>

      {/* Canvas */}
      <div style={{ flex: 1, position: "relative" }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          onNodeClick={(_, node) => { setSelectedNode(node); setSelectedEdge(null); }}
          onEdgeClick={(_, edge) => { setSelectedEdge(edge); setSelectedNode(null); }}
          fitView
          fitViewOptions={{ padding: 0.35 }}
          minZoom={0.4}
          maxZoom={2.5}
        >
          <Background color="var(--border)" gap={24} />
          <Controls />
          <MiniMap nodeColor={() => "#6366f1"} />

          <Panel position="top-right">
            <div className="flex gap-8">
              {selectedNode && (
                <button className="btn btn-danger btn-sm" onClick={() => deleteNode(selectedNode.id)}>
                  <Trash2 size={12} /> Delete Node
                </button>
              )}
              {selectedEdge && (
                <button className="btn btn-danger btn-sm" onClick={() => deleteEdge(selectedEdge.id)}>
                  <Trash2 size={12} /> Delete Edge
                </button>
              )}
              <button className="btn btn-primary btn-sm" onClick={save} disabled={saving}>
                {saving ? <span className="spinner" /> : <><Save size={12} /> Save Graph</>}
              </button>
            </div>
          </Panel>
        </ReactFlow>

        {nodes.length === 0 && (
          <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", pointerEvents: "none" }}>
            <div className="empty-state">
              <div className="empty-state-icon">🔗</div>
              <div className="empty-state-title">Empty Canvas</div>
              <p>Click nodes on the left palette to add them to the graph.</p>
            </div>
          </div>
        )}
      </div>

      {/* Config panels */}
      {selectedNode && (
        <NodeConfigPanel
          node={selectedNode}
          availableTools={availableTools}
          capabilityGroups={capabilityGroups}
          onUpdate={(data) => updateNodeData(selectedNode.id, data)}
          onClose={() => setSelectedNode(null)}
        />
      )}
      {selectedEdge && (
        <EdgeConfigPanel
          edge={selectedEdge}
          onUpdate={updateEdgeData}
          onClose={() => setSelectedEdge(null)}
        />
      )}
    </div>
  );
}
