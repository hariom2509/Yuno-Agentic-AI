import sys
sys.stdout.reconfigure(encoding='utf-8')

bundle_path = 'app/static/static/js/main.f973130c.js'

with open(bundle_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update modal font size and width
old_modal_tag = 'className:"modal modal-wide"'
new_modal_tag = 'className:"modal modal-wide",style:{width:760,fontSize:"14px",lineHeight:"1.5"}'

if old_modal_tag in content:
    content = content.replace(old_modal_tag, new_modal_tag)
    print("Updated Agent modal width and font scaling to 100%.")

# 2. Target old tools block
target_tools_block = '(0,ia.jsxs)("div",{className:"form-group",children:[(0,ia.jsx)("label",{className:"form-label",children:"Tools"}),(0,ia.jsx)("div",{className:"flex gap-8",style:{flexWrap:"wrap"},children:f.map(e=>(0,ia.jsx)("button",{type:"button",className:"btn btn-sm ".concat(b.tools.includes(typeof e==="string"?e:e.id)?"btn-primary":"btn-ghost"),onClick:()=>(e=>{let val=typeof e==="string"?e:e.id; E("tools",b.tools.includes(val)?b.tools.filter(t=>t!==val):[...b.tools,val])})(e),children:typeof e==="string"?e:e.label},"btn_"+(typeof e==="string"?e:e.id)))})]})'

# Replacement: 2 Distinct Section Groups (Yuno Tools & PostgreSQL MCP)
replacement_tools_block = """(0,ia.jsxs)(ia.Fragment,{children:[
  (0,ia.jsx)("div",{className:"divider",style:{margin:"24px 0 16px"}}),
  (0,ia.jsx)("div",{style:{fontWeight:700,fontSize:"14px",color:"var(--accent)",marginBottom:16,letterSpacing:"0.5px"},children:"🛠️ AGENT CAPABILITIES & MCP INTEGRATIONS"}),
  
  /* Section 1: Yuno Tools */
  (0,ia.jsxs)("div",{className:"form-group",style:{marginBottom:20},children:[
    (0,ia.jsx)("label",{className:"form-label",style:{fontSize:"13px",fontWeight:600,color:"var(--text-bright)",marginBottom:8},children:"Yuno Tools (Built-in Workflow Capabilities)"}),
    (0,ia.jsx)("div",{className:"flex gap-8",style:{flexWrap:"wrap"},children:[
      {id:"mcp::yuno-tools::web_search",label:"Web Search"},
      {id:"mcp::yuno-tools::calculator",label:"Calculator"},
      {id:"mcp::yuno-tools::report_generator",label:"Report Generator"},
      {id:"mcp::yuno-tools::file_reader",label:"File Reader"},
      {id:"mcp::yuno-tools::analyze_text",label:"Analyze Text"},
      {id:"mcp::yuno-tools::calculate_metrics",label:"Calculate Metrics"},
      {id:"mcp::yuno-tools::format_report",label:"Format Report"}
    ].map(t=>{
      let sel = b.tools.includes(t.id) || b.tools.includes(t.id.split("::").pop());
      return (0,ia.jsxs)("button",{type:"button",style:{fontSize:"13px",padding:"6px 14px",borderRadius:"6px"},className:"btn btn-sm ".concat(sel?"btn-primary":"btn-ghost"),onClick:()=>{
        let val = t.id;
        E("tools", sel ? b.tools.filter(x=>x!==val && x!==val.split("::").pop()) : [...b.tools, val]);
      },children:[sel?"✓ ":" ",t.label]},t.id);
    })})
  ]}),

  /* Section 2: PostgreSQL MCP */
  (0,ia.jsxs)("div",{className:"form-group",style:{marginBottom:24},children:[
    (0,ia.jsxs)("div",{className:"flex items-center justify-between mb-12",children:[
      (0,ia.jsx)("label",{className:"form-label",style:{fontSize:"13px",fontWeight:600,color:"var(--text-bright)",marginBottom:0},children:"External MCP Integration: PostgreSQL MCP"}),
      (0,ia.jsx)("span",{style:{fontSize:"11px",padding:"2px 8px",background:"var(--accent-glow)",border:"1px solid var(--accent)",borderRadius:"12px",color:"var(--accent)",fontWeight:600},children:"Enabled ✓"})
    ]}),
    (0,ia.jsx)("div",{className:"card-grid card-grid-2",style:{gap:8},children:[
      {id:"mcp::postgres-mcp::inspect_schema",label:"Inspect Schema",risk:"LOW",req:false},
      {id:"mcp::postgres-mcp::list_tables",label:"List Tables",risk:"LOW",req:false},
      {id:"mcp::postgres-mcp::describe_table",label:"Describe Table",risk:"LOW",req:false},
      {id:"mcp::postgres-mcp::execute_select",label:"Execute Select",risk:"LOW",req:false},
      {id:"mcp::postgres-mcp::insert_row",label:"Insert Row",risk:"HIGH",req:true},
      {id:"mcp::postgres-mcp::update_rows",label:"Update Rows",risk:"HIGH",req:true},
      {id:"mcp::postgres-mcp::truncate_table",label:"Truncate Table",risk:"CRITICAL",req:true},
      {id:"mcp::postgres-mcp::drop_table",label:"Drop Table",risk:"CRITICAL",req:true}
    ].map(t=>{
      let sel = b.tools.includes(t.id) || b.tools.includes(t.id.split("::").pop());
      let isRiskHigh = t.risk==="HIGH" || t.risk==="CRITICAL";
      return (0,ia.jsxs)("div",{onClick:()=>{
        let val = t.id;
        E("tools", sel ? b.tools.filter(x=>x!==val && x!==val.split("::").pop()) : [...b.tools, val]);
      },style:{padding:"10px 14px",borderRadius:6,background:sel?"var(--bg-card-hover)":"var(--bg-surface)",border:sel?"1.5px solid var(--accent)":"1px solid var(--border)",cursor:"pointer",display:"flex",alignItems:"center",justifyBetween:"space-between",justifyContent:"space-between"},children:[
        (0,ia.jsxs)("div",{style:{display:"flex",alignItems:"center",gap:10},children:[
          (0,ia.jsx)("input",{type:"checkbox",checked:sel,readOnly:true,style:{cursor:"pointer",width:15,height:15}}),
          (0,ia.jsx)("span",{style:{fontSize:"13px",fontWeight:sel?600:400,color:sel?"var(--text-bright)":"var(--text-primary)"},children:t.label})
        ]}),
        (0,ia.jsxs)("span",{style:{fontSize:"10px",padding:"2px 6px",borderRadius:4,fontWeight:700,background:isRiskHigh?"rgba(239, 68, 68, 0.15)":"rgba(34, 197, 94, 0.15)",color:isRiskHigh?"#ef4444":"#22c55e",border:"1px solid ".concat(isRiskHigh?"rgba(239, 68, 68, 0.3)":"rgba(34, 197, 94, 0.3)")},children:[t.risk,t.req?" · Approval Required":""]})
      ]},t.id);
    })})
  ]})
]}"""

# Strip formatting newlines for minified JS
replacement_minified = "".join([line.strip() for line in replacement_tools_block.split("\n") if line.strip() and not line.strip().startswith("/*")])

if target_tools_block in content:
    content = content.replace(target_tools_block, replacement_minified)
    print("SUCCESSFULLY replaced Agents modal tools layout with 2 distinct capability groups!")
else:
    print("WARNING: Target tools block not found in static bundle.")

with open(bundle_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Redesign patch script complete.")
