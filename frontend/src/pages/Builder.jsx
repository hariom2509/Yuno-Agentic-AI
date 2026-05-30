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

// Custom Node Components
function AgentNodeComponent({ data }) {
  return (
    <div className="agent-node" style={{ minWidth: 160, position: "relative" }}>
      {/* Target handle (input) on top */}
      <Handle type="target" position={Position.Top} style={{ background: "var(--accent)", width: 8, height: 8 }} />
      
      <div style={{ fontSize: 20, marginBottom: 6 }}>🤖</div>
      <div className="agent-node-title">{data.label}</div>
      <div className="agent-node-role">{data.type === "tool" ? `tool: ${data.tool}` : data.model || "llama-3.1-8b-instant"}</div>
      
      {/* Source handle (output) on bottom */}
      <Handle type="source" position={Position.Bottom} style={{ background: "var(--accent)", width: 8, height: 8 }} />
    </div>
  );
}

const nodeTypes = { agentNode: AgentNodeComponent };

const NODE_PALETTE = [
  { type: "agent", label: "Agent Node", icon: "🤖", desc: "AI agent powered by OpenAI" },
  { type: "tool", label: "Tool Node", icon: "🔧", desc: "Execute a tool (search, calc, report)" },
];

function NodeConfigPanel({ node, availableTools, onUpdate, onClose }) {
  const [data, setData] = useState(node.data);

  const set = (k, v) => setData(d => ({ ...d, [k]: v }));
  const setGuardrail = (k, v) => setData(d => ({ 
    ...d, 
    guardrails: { ...(d.guardrails || {}), [k]: v } 
  }));

  return (
    <div style={{
      position: "absolute", right: 0, top: 0, bottom: 0, width: 340,
      background: "var(--bg-surface)", borderLeft: "1px solid var(--border)",
      padding: 20, overflowY: "auto", zIndex: 10,
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
          <select className="form-select" value={data.tool || "web_search"} onChange={e => set("tool", e.target.value)}>
            {availableTools.map(tool => (
              <option key={tool} value={tool}>{tool}</option>
            ))}
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
  const [availableTools, setAvailableTools] = useState(["web_search", "calculator", "report_generator", "file_reader"]);
  const [nodeCounter, setNodeCounter] = useState(1);

  useEffect(() => {
    // Fetch available skills
    api.get("/skills/").then(s => {
      const skillNames = (s.data || []).map(sk => sk.name);
      setAvailableTools(["web_search", "calculator", "report_generator", "file_reader", ...skillNames]);
    }).catch(() => {});

    if (!workflowId) return;
    api.get(`/workflows/${workflowId}`).then(r => {
      setWorkflow(r.data);
      const graph = r.data.graph || {};
      setNodes(graph.nodes || []);
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
    if (!workflowId) {
      toast.error("Please open a workflow first from the Workflows page.");
      return;
    }
    setSaving(true);
    try {
      await api.put(`/workflows/${workflowId}`, {
        name: workflow?.name || "Untitled",
        description: workflow?.description || "",
        graph: { nodes, edges },
      });
      toast.success("Workflow graph saved!");
    } catch {
      toast.error("Save failed");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ position: "relative", height: "calc(100vh - 64px)", display: "flex" }}>
      {/* Left palette */}
      <div style={{ width: 200, background: "var(--bg-surface)", borderRight: "1px solid var(--border)", padding: 16, flexShrink: 0 }}>
        <div style={{ fontWeight: 600, marginBottom: 12, fontSize: 13 }}>Node Palette</div>
        {NODE_PALETTE.map(n => (
          <div
            key={n.type}
            className="card"
            style={{ marginBottom: 10, cursor: "grab", padding: "10px 12px" }}
            onClick={() => addNode(n.type)}
          >
            <div className="flex items-center gap-8">
              <span style={{ fontSize: 18 }}>{n.icon}</span>
              <div>
                <div style={{ fontSize: 12, fontWeight: 600 }}>{n.label}</div>
                <div style={{ fontSize: 10, color: "var(--text-muted)" }}>{n.desc}</div>
              </div>
            </div>
          </div>
        ))}

        <div className="divider" />

        {workflowId ? (
          <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
            Editing: <strong style={{ color: "var(--text-secondary)" }}>{workflow?.name}</strong>
          </div>
        ) : (
          <div style={{ fontSize: 11, color: "var(--yellow)" }}>
            ⚠️ No workflow selected. Open a workflow from the Workflows page.
          </div>
        )}

        <button
          className="btn btn-ghost btn-sm w-full mt-16"
          style={{ fontSize: 11 }}
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
