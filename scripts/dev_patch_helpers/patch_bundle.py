with open('app/static/static/js/main.f973130c.js', 'r', encoding='utf-8') as f:
    content = f.read()

target = 'children:t.final_output})]}'

hitl_code = 'children:t.final_output})]}),"waiting_for_approval"===t.status&&(0,ia.jsxs)("div",{style:{background:"rgba(245, 158, 11, 0.12)",border:"1px solid rgba(245, 158, 11, 0.5)",borderRadius:8,padding:16,marginBottom:16},children:[(0,ia.jsxs)("div",{style:{color:"#f59e0b",fontWeight:700,fontSize:15,marginBottom:6},children:["⚠️ HUMAN-IN-THE-LOOP APPROVAL REQUIRED"]}),(0,ia.jsxs)("div",{style:{fontSize:13,color:"var(--text-primary)",marginBottom:12},children:["Execution paused at node ",(0,ia.jsx)("code",{children:t.current_node}),". Review and approve or reject."]}),(0,ia.jsxs)("div",{style:{display:"flex",gap:12},children:[(0,ia.jsx)("button",{className:"btn btn-sm",style:{background:"#22c55e",color:"#fff",fontWeight:600,padding:"6px 14px",borderRadius:4,border:"none",cursor:"pointer"},onClick:e=>{e.stopPropagation();fetch("/executions/"+t.id+"/resume",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({decision:"APPROVED"})}).then(()=>window.location.reload())},children:"✅ Approve & Resume"}),(0,ia.jsx)("button",{className:"btn btn-sm",style:{background:"#ef4444",color:"#fff",fontWeight:600,padding:"6px 14px",borderRadius:4,border:"none",cursor:"pointer"},onClick:e=>{e.stopPropagation();fetch("/executions/"+t.id+"/resume",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({decision:"REJECTED"})}).then(()=>window.location.reload())},children:"❌ Reject Execution"})]})]})'

if target in content:
    new_content = content.replace(target, hitl_code, 1)
    with open('app/static/static/js/main.f973130c.js', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('SUCCESSFULLY PATCHED BUNDLE WITH HITL APPROVAL UI!')
else:
    print('Target not found in bundle.')
