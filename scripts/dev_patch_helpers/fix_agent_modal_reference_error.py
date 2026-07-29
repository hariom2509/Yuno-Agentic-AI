import sys
sys.stdout.reconfigure(encoding='utf-8')

bundle_path = 'app/static/static/js/main.f973130c.js'

with open(bundle_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Define T (toggleTool) inside function ya(e) (AgentModal)
target_state_init = 'x=y[1],w=d((0,o.useState)(!1),2),S=w[0],k=w[1];'
replacement_state_init = 'x=y[1],w=d((0,o.useState)(!1),2),S=w[0],k=w[1];const T=toolId=>x(n=>{let cur=n.tools||[];let exists=cur.includes(toolId)||cur.includes(toolId.split("::").pop());return Ze(Ze({},n),{},{tools:exists?cur.filter(x=>x!==toolId&&x!==toolId.split("::").pop()):[...cur,toolId]});});'

if target_state_init in content:
    content = content.replace(target_state_init, replacement_state_init)
    print("SUCCESSFULLY added toggleTool (T) definition inside AgentModal (ya)!")
else:
    print("WARNING: target_state_init not found in static bundle.")

with open(bundle_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fix script complete.")
