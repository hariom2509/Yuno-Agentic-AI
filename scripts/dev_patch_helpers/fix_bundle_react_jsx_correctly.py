import sys
sys.stdout.reconfigure(encoding='utf-8')

bundle_path = 'app/static/static/js/main.f973130c.js'

with open(bundle_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find start of our section replacement around 'Max Tokens'
idx_max = content.find('Max Tokens')
start_idx = content.find('(0,ia.jsxs)("div",{className:"form-group",children:[(0,ia.jsx)("div",{className:"divider"', idx_max)
end_idx = content.find('(0,ia.jsx)("div",{className:"form-group",children:(0,ia.jsxs)("label",{className:"toggle"', idx_max)

print("start_idx:", start_idx)
print("end_idx:", end_idx)

if start_idx != -1 and end_idx != -1:
    # 100% React 18 production runtime compliant snippet
    clean_snippet = """(0,ia.jsx)("div",{className:"form-group",children:[(0,ia.jsx)("div",{className:"divider",style:{margin:"24px 0 16px"}}),(0,ia.jsx)("div",{style:{fontWeight:700,fontSize:"14px",color:"var(--accent)",marginBottom:16,letterSpacing:"0.5px"},children:"AGENT CAPABILITIES & MCP INTEGRATIONS"}),(0,ia.jsx)("div",{className:"form-group",style:{marginBottom:20},children:[(0,ia.jsx)("label",{className:"form-label",style:{fontSize:"13px",fontWeight:600,color:"var(--text-bright)",marginBottom:8},children:"Yuno Tools (Built-in Workflow Capabilities)"}),(0,ia.jsx)("div",{className:"flex gap-8",style:{flexWrap:"wrap"},children:[{id:"mcp::yuno-tools::web_search",label:"Web Search"},{id:"mcp::yuno-tools::calculator",label:"Calculator"},{id:"mcp::yuno-tools::report_generator",label:"Report Generator"},{id:"mcp::yuno-tools::file_reader",label:"File Reader"},{id:"mcp::yuno-tools::analyze_text",label:"Analyze Text"},{id:"mcp::yuno-tools::calculate_metrics",label:"Calculate Metrics"},{id:"mcp::yuno-tools::format_report",label:"Format Report"}].map(function(t){var sel=(b.tools||[]).includes(t.id)||(b.tools||[]).includes(t.id.split("::").pop());return (0,ia.jsx)("button",{type:"button",style:{fontSize:"13px",padding:"6px 14px",borderRadius:"6px"},className:"btn btn-sm ".concat(sel?"btn-primary":"btn-ghost"),onClick:function(){T(t.id)},children:t.label},t.id);})})]}),(0,ia.jsx)("div",{className:"form-group",style:{marginBottom:24},children:[(0,ia.jsx)("div",{className:"flex items-center justify-between mb-12",children:[(0,ia.jsx)("label",{className:"form-label",style:{fontSize:"13px",fontWeight:600,color:"var(--text-bright)",marginBottom:0},children:"External MCP Integration: PostgreSQL MCP"}),(0,ia.jsx)("span",{style:{fontSize:"11px",padding:"2px 8px",background:"var(--accent-glow)",border:"1px solid var(--accent)",borderRadius:"12px",color:"var(--accent)",fontWeight:600},children:"Enabled"})]}),(0,ia.jsx)("div",{className:"card-grid card-grid-2",style:{gap:8},children:[{id:"mcp::postgres-mcp::inspect_schema",label:"Inspect Schema",risk:"LOW",req:false},{id:"mcp::postgres-mcp::list_tables",label:"List Tables",risk:"LOW",req:false},{id:"mcp::postgres-mcp::describe_table",label:"Describe Table",risk:"LOW",req:false},{id:"mcp::postgres-mcp::execute_select",label:"Execute Select",risk:"LOW",req:false},{id:"mcp::postgres-mcp::insert_row",label:"Insert Row",risk:"HIGH",req:true},{id:"mcp::postgres-mcp::update_rows",label:"Update Rows",risk:"HIGH",req:true},{id:"mcp::postgres-mcp::truncate_table",label:"Truncate Table",risk:"CRITICAL",req:true},{id:"mcp::postgres-mcp::drop_table",label:"Drop Table",risk:"CRITICAL",req:true}].map(function(t){var sel=(b.tools||[]).includes(t.id)||(b.tools||[]).includes(t.id.split("::").pop());var isRiskHigh=t.risk==="HIGH"||t.risk==="CRITICAL";return (0,ia.jsx)("div",{onClick:function(){T(t.id)},style:{padding:"10px 14px",borderRadius:6,background:sel?"var(--bg-card-hover)":"var(--bg-surface)",border:sel?"1.5px solid var(--accent)":"1px solid var(--border)",cursor:"pointer",display:"flex",alignItems:"center",justifyContent:"space-between"},children:[(0,ia.jsx)("div",{style:{display:"flex",alignItems:"center",gap:10},children:[(0,ia.jsx)("input",{type:"checkbox",checked:sel,readOnly:true,style:{cursor:"pointer",width:15,height:15}}),(0,ia.jsx)("span",{style:{fontSize:"13px",fontWeight:sel?600:400,color:sel?"var(--text-bright)":"var(--text-primary)"},children:t.label})]}),(0,ia.jsx)("span",{style:{fontSize:"10px",padding:"2px 6px",borderRadius:4,fontWeight:700,background:isRiskHigh?"rgba(239, 68, 68, 0.15)":"rgba(34, 197, 94, 0.15)",color:isRiskHigh?"#ef4444":"#22c55e",border:"1px solid ".concat(isRiskHigh?"rgba(239, 68, 68, 0.3)":"rgba(34, 197, 94, 0.3)")},children:[t.risk,t.req?" - Approval Required":""]})]},t.id);})})]})]})"""

    clean_minified = "".join([l.strip() for l in clean_snippet.split("\n") if l.strip()])
    content = content[:start_idx] + clean_minified + content[end_idx:]
    print("Replaced with 100% React 18 runtime compliant (0,ia.jsx) calls!")

with open(bundle_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch script complete.")
