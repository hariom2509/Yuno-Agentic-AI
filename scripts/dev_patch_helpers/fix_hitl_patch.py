import sys
sys.stdout.reconfigure(encoding='utf-8')

bundle_path = 'app/static/static/js/main.f973130c.js'

with open(bundle_path, 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = 'children:[t.final_output&&'
end_marker = ',(0,ia.jsxs)("div",{children:[(0,ia.jsxs)("div",{style:{fontSize:11,fontWeight:600,color:"var(--text-muted)",marginBottom:12,textTransform:"uppercase",letterSpacing:1},children:["Message Timeline ('

start_pos = content.find(start_marker)
end_pos = content.find(end_marker)

print("start_pos:", start_pos)
print("end_pos:", end_pos)

if start_pos != -1 and end_pos != -1:
    old_segment = content[start_pos:end_pos]
    print("OLD SEGMENT:\n", old_segment)

    hitl_box = '"waiting_for_approval"===t.status&&(0,ia.jsxs)("div",{style:{background:"rgba(245, 158, 11, 0.15)",border:"2px solid #f59e0b",borderRadius:8,padding:16,marginBottom:16},children:[(0,ia.jsxs)("div",{style:{color:"#f59e0b",fontWeight:700,fontSize:15,marginBottom:6},children:["⚠️ HUMAN-IN-THE-LOOP APPROVAL REQUIRED"]}),(0,ia.jsxs)("div",{style:{fontSize:13,color:"#fff",marginBottom:12},children:["Execution paused at node ",(0,ia.jsx)("code",{children:t.current_node}),". Review and approve or reject."]}),(0,ia.jsxs)("div",{style:{display:"flex",gap:12},children:[(0,ia.jsx)("button",{className:"btn btn-sm",style:{background:"#22c55e",color:"#fff",fontWeight:600,padding:"6px 14px",borderRadius:4,border:"none",cursor:"pointer"},onClick:e=>{e.stopPropagation();fetch("/executions/"+t.id+"/resume",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({decision:"APPROVED"})}).then(()=>window.location.reload())},children:"✅ Approve & Resume"}),(0,ia.jsx)("button",{className:"btn btn-sm",style:{background:"#ef4444",color:"#fff",fontWeight:600,padding:"6px 14px",borderRadius:4,border:"none",cursor:"pointer"},onClick:e=>{e.stopPropagation();fetch("/executions/"+t.id+"/resume",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({decision:"REJECTED"})}).then(()=>window.location.reload())},children:"❌ Reject Execution"})]})]})'

    final_output_box = 't.final_output&&(0,ia.jsxs)("div",{style:{marginBottom:16},children:[(0,ia.jsx)("div",{style:{fontSize:11,fontWeight:600,color:"var(--text-muted)",marginBottom:8,textTransform:"uppercase",letterSpacing:1},children:"Final Output"}),(0,ia.jsx)("div",{className:"code-block",children:t.final_output})]})'

    new_segment = f'children:[{hitl_box},{final_output_box}'

    new_content = content[:start_pos] + new_segment + content[end_pos:]

    with open(bundle_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print("FIXED BUNDLE SUCCESSFULLY!")
else:
    print("Markers not found!")
