import sys
sys.stdout.reconfigure(encoding='utf-8')

bundle_path = 'app/static/static/js/main.f973130c.js'

with open(bundle_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = 'className:"btn btn-sm ".concat(b.tools.includes(e)?"btn-primary":"btn-ghost"),onClick:()=>(e=>{E("tools",b.tools.includes(e)?b.tools.filter(t=>t!==e):[...b.tools,e])})(e),children:e},e)'

replacement = 'className:"btn btn-sm ".concat(b.tools.includes(typeof e==="string"?e:e.id)?"btn-primary":"btn-ghost"),onClick:()=>(e=>{let val=typeof e==="string"?e:e.id; E("tools",b.tools.includes(val)?b.tools.filter(t=>t!==val):[...b.tools,val])})(e),children:typeof e==="string"?e:e.label},"btn_"+(typeof e==="string"?e:e.id))'

if target in content:
    content = content.replace(target, replacement)
    print("SUCCESSFULLY patched Agents modal button renderer for MCP tools!")
else:
    print("WARNING: Target string not found.")

with open(bundle_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Agents bundle patch complete.")
