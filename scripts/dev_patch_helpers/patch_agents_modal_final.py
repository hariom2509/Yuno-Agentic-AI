import sys
sys.stdout.reconfigure(encoding='utf-8')

bundle_path = 'app/static/static/js/main.f973130c.js'

with open(bundle_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Target Agents modal tool section in compiled bundle
# Old target pattern around "Authorized Tools"
old_tools_header = 'className:"form-label",children:"Authorized Tools & External MCP Integrations"'

if old_tools_header in content:
    print("Found old tools header in static bundle.")

# Write full patch script for bundle replacement
with open(bundle_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Check finished.")
